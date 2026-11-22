"""Build development-only Phase 2.5 paper tables and PNGs from saved records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLORS = dict(zip(("B0", "B1", "B2", "B3", "B4", "STaR", "STaR_no_partial"), (
    "#555555", "#CC79A7", "#E69F00", "#0072B2", "#009E73", "#D55E00", "#6C5A9A",
)))
LABELS = {"STaR_no_partial": "No partial"}
METHODS = tuple(COLORS)


def group(rows, key):
    groups = defaultdict(list)
    for row in rows:
        groups[key(row)].append(row)
    return groups


def table(root, name, columns, records):
    def display(value):
        return "" if value is None else f"{value:.7g}" if isinstance(value, float) else value

    output = root / "tables"
    output.mkdir(parents=True, exist_ok=True)
    rows = [[display(value) for value in row] for row in records]
    with (output / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    escaping = str.maketrans({"\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&",
                              "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}"})
    environment = "longtable" if len(rows) > 35 else "tabular"
    lines = [r"\begin{" + environment + "}{ll" + "r" * (len(columns) - 2) + "}", r"\hline"]
    for index, row in enumerate([columns, *rows]):
        lines.append(" & ".join(str(value).translate(escaping) for value in row) + r" \\")
        if index == 0:
            lines.append(r"\hline")
    lines.extend((r"\hline", r"\end{" + environment + "}"))
    (output / f"{name}.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def figure(root, name, fig):
    path = root / "figures" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=400, facecolor="white")
    plt.close(fig)


def route_key(row):
    return row["parent"], row["variant"], row["route_id"]


def pair(rows, challenger, comparator):
    indexed = {(*route_key(row), row["method"]): row for row in rows}
    return [(row, indexed[(*route_key(row), comparator)]) for row in rows if row["method"] == challenger]


def cluster_interval(values, seed, parents):
    grouped = group(values, lambda item: item[0])
    sums = np.array([sum(value for _, value in grouped[parent]) for parent in parents])
    sizes = np.array([len(grouped[parent]) for parent in parents])
    if not sizes.sum():
        return None, None, None
    draws = np.random.default_rng(seed).integers(len(parents), size=(9999, len(parents)))
    counts = sizes[draws].sum(axis=1)
    totals = sums[draws].sum(axis=1)
    interval = np.quantile(totals[counts > 0] / counts[counts > 0], [0.025, 0.975])
    return float(sums.sum() / sizes.sum()), *map(float, interval)


def val(row, metric):
    return row["validation"][metric]


def mean(rows, metric):
    return float(np.mean([val(row, metric) for row in rows]))


def load(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for profile in manifest["config"]["profiles"]:
        profile_rows = []
        for item in manifest["development_inventory"]:
            stem = f'{item["instance_key"]}__{item["variant"]}.json'
            payload = json.loads((root / "raw" / profile / stem).read_text(encoding="utf-8"))
            profile_rows.extend(payload["rows"])
        if len(profile_rows) != len({(*route_key(row), row["method"]) for row in profile_rows}):
            raise ValueError("Duplicate results")
        if any({row["method"] for row in sub} != set(METHODS)
               for sub in group(profile_rows, route_key).values()):
            raise ValueError("Incomplete pairing")
        rows.extend(profile_rows)
    return manifest["config"], rows


def analyze(root: Path):
    cfg, rows = load(root)
    profiles = list(cfg["profiles"])
    primary = cfg["primary_profile"]
    main = [row for row in rows if row["profile"] == primary]
    parents = sorted({row["parent"] for row in main})
    methods = group(rows, lambda row: (row["profile"], row["method"]))
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "axes.axisbelow": True, "grid.alpha": 0.2})

    def avg_budget(sub, key):
        return float(np.mean([row["budget"][key] for row in sub]))

    def metrics(sub):
        return len(sub), mean(sub, "reliability"), sum(val(row, "attained") for row in sub), mean(sub, "mean_completion")

    table(root, "main", ["profile", "method", "n", "mean_R", "attained", "mean_completion",
                        "mean_seconds", "mean_scenarios", "mean_distinct_plans", "mean_proposals"], [
        (profile, method, *metrics(sub), *(avg_budget(sub, key) for key in (
            "elapsed_seconds", "scenarios_evaluated", "candidates_evaluated", "generated",
        ))) for (profile, method), sub in methods.items()
    ])
    table(root, "historical_panel", ["profile", "method", "n", "mean_R", "attained", "mean_completion"], [
        (profile, method, *metrics([row for row in sub if row["panel"]]))
        for (profile, method), sub in methods.items()
    ])
    table(root, "family_variant", ["family", "variant", "method", "n", "mean_R", "attained", "mean_completion"], [
        (*key, *metrics(sub)) for key, sub in sorted(group(main, lambda row: (
            row["family"], row["variant"], row["method"],
        )).items())
    ])
    table(root, "repairable", ["family", "method", "below_target_B0", "repaired", "mean_delta_R"], [
        (family, method, len(sub), sum(val(first, "attained") for first, _ in sub),
         float(np.mean([val(first, "reliability") - val(second, "reliability") for first, second in sub])))
        for method in METHODS[1:]
        for family, sub in sorted(group(
            [(first, second) for first, second in pair(main, method, "B0")
             if val(second, "reliability") < cfg["target"]], lambda item: item[0]["family"],
        ).items())
    ])
    table(root, "family_stress", ["family", "exposed", "mean_B0_visits", "multiple_B0_visits",
                                 "STaR_not_attained"], [
        (family, len(pairs), float(np.mean([len(val(second, "charging")) for _, second in pairs])),
         sum(len(val(second, "charging")) > 1 for _, second in pairs),
         sum(not val(first, "attained") for first, _ in pairs))
        for family, pairs in sorted(group(pair(main, "STaR", "B0"), lambda item: item[0]["family"]).items())
    ])

    paired_records = []
    for profile in profiles:
        subset = [row for row in rows if row["profile"] == profile]
        for method in ("B4", "B3", "B1", "B2", "B0", "STaR_no_partial"):
            pairs = pair(subset, "STaR", method)
            for metric in ("reliability", "attained", "mean_completion", "completion_common_attained"):
                field = "mean_completion" if metric == "completion_common_attained" else metric
                values = [
                    (first["parent"], float(val(first, field)) - float(val(second, field)))
                    for first, second in pairs if metric != "completion_common_attained"
                    or (val(first, "attained") and val(second, "attained"))
                ]
                estimate = cluster_interval(values, cfg["analysis_seed"], parents)
                paired_records.append((profile, "STaR", method, metric, len(values), *estimate))
    table(root, "paired_parent_bootstrap", ["profile", "challenger", "comparator", "metric", "n",
                                          "difference", "lower_95", "upper_95"], paired_records)

    work = ("generation_seconds", "deterministic_seconds", "screening_seconds", "simulation_seconds")
    table(root, "overhead", ["profile", "method", *work, "max_seconds", "wall_overruns",
                            "bound_rejects", "prefix_rejects"], [
        (profile, method, *(avg_budget(sub, key) for key in work),
         max(row["budget"]["elapsed_seconds"] for row in sub),
         sum(row["budget"]["elapsed_seconds"] > cfg["profiles"][profile]["wall_seconds"] for row in sub),
         sum(row["screen_rejections"] for row in sub), sum(row["prefix_rejections"] for row in sub))
        for (profile, method), sub in methods.items()
    ])
    table(root, "route_metrics", ["profile", "parent", "variant", "route", "method", "historical_panel", "R",
                                 "wilson95_lower", "attained", "mean_completion", "scenario_count",
                                 "runtime_s", "screen_rejections", "prefix_rejections"], [
        (row["profile"], *route_key(row), row["method"], row["panel"], val(row, "reliability"),
         val(row, "wilson95_lower"), val(row, "attained"), val(row, "mean_completion"),
         row["budget"]["scenarios_evaluated"], row["budget"]["elapsed_seconds"],
         row["screen_rejections"], row["prefix_rejections"]) for row in rows
    ])

    for metric, xlabel, name, scale in (
        ("elapsed_seconds", "Mean optimization time (ms)", "fig10_reliability_runtime", 1000),
        ("scenarios_evaluated", "Mean optimization scenario evaluations", "fig11_reliability_scenarios", 1),
    ):
        fig, ax = plt.subplots(figsize=(6.6, 3.9), layout="constrained")
        for method in METHODS:
            coords = sorted((scale * avg_budget(methods[profile, method], metric),
                             100 * mean(methods[profile, method], "reliability")) for profile in profiles)
            ax.plot(*zip(*coords), ".-", color=COLORS[method], label=LABELS.get(method, method))
        ax.set(xlabel=xlabel, ylabel="Mean validation reliability (%)")
        ax.legend(ncols=2, fontsize=8)
        figure(root, name, fig)

    fig, ax = plt.subplots(figsize=(7.0, 3.75), layout="constrained")
    for index, method in enumerate(METHODS):
        offset = (index - 3) * 0.11
        heights = [100 * mean(methods[profile, method], "attained") for profile in profiles]
        ax.bar(np.arange(len(profiles)) + offset, heights, width=0.105, color=COLORS[method],
               label=LABELS.get(method, method))
    ax.set(xticks=range(len(profiles)), xticklabels=["24 plans", "64 plans", "8,192 scenarios", "40 ms"],
           ylabel="Routes with lower bound ≥ 0.95 (%)", ylim=(0, 100))
    ax.legend(ncols=4, fontsize=8, loc="lower center")
    figure(root, "fig08_equal_budget_attainment", fig)

    pairs = pair(main, "STaR", "B4")
    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.5), layout="constrained")
    for ax, metric, label, scale in (
        (axes[0], "reliability", "Reliability difference (pp)", 100),
        (axes[1], "mean_completion", "Completion difference (time units)", 1),
    ):
        differences = [scale * (float(val(first, metric)) - float(val(second, metric))) for first, second in pairs]
        ax.hist(differences, bins=31, color=COLORS["STaR"])
        ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set(xlabel=label, ylabel="Paired routes")
    figure(root, "fig09_paired_star_b4", fig)

    fig, ax = plt.subplots(figsize=(6.6, 3.6), layout="constrained")
    res = [p for p in paired_records if p[2] == "STaR_no_partial" and p[3] in ("reliability", "attained")]
    for offset, (metric, label) in zip((-0.12, 0.12), (("reliability", "Reliability"), ("attained", "Attainment"))):
        estimates = np.array([[point[5], point[6], point[7]] for point in res if point[3] == metric]) * 100
        ax.errorbar(np.arange(len(profiles)) + offset, estimates[:, 0],
                    yerr=[estimates[:, 0] - estimates[:, 1], estimates[:, 2] - estimates[:, 0]],
                    fmt="o", capsize=4, label=label)
    ax.set(xticks=range(len(profiles)), xticklabels=["24 plans", "64 plans", "8,192 scenarios", "40 ms"],
           ylabel="STaR − no partial (percentage points)")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend()
    figure(root, "fig13_partial_ablation", fig)

    families = sorted({row["family"] for row in main})
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.8), layout="constrained")
    for method in ("B0", "B3", "B4", "STaR"):
        data = group([row for row in main if row["method"] == method], lambda row: row["family"])
        for ax, field, label in ((axes[0], "reliability", "Mean reliability (%)"),
                                 (axes[1], "attained", "Routes attaining target (%)")):
            ax.plot(families, [100 * mean(data[family], field) for family in families],
                    "o-", color=COLORS[method], label=method)
            ax.set(ylabel=label, ylim=(0, 103))
    axes[0].legend(ncols=2, fontsize=8)
    figure(root, "fig14_family_stress", fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.7), layout="constrained")
    comparison = ["B1", "B2", "B3", "B4", "STaR"]
    bottom = np.zeros(len(comparison))
    for index, key in enumerate(work):
        values = np.array([1000 * avg_budget(methods[primary, method], key) for method in comparison])
        axes[0].bar(comparison, values, bottom=bottom, color=list(COLORS.values())[index], label=key.split("_")[0])
        bottom += values
    axes[0].legend(fontsize=8)
    axes[0].set(ylabel="Mean measured work (ms)")
    star_groups = [methods[profile, "STaR"] for profile in profiles]
    axes[1].bar(range(len(profiles)), [np.mean([row["screen_rejections"] for row in sub]) for sub in star_groups],
                color=COLORS["STaR"], label="Mathematical bound")
    axes[1].plot(range(len(profiles)), [np.mean([row["prefix_rejections"] for row in sub]) for sub in star_groups],
                 "o-", color=COLORS["B3"], label="Scenario prefix")
    axes[1].set(xticks=range(len(profiles)), xticklabels=["24 plans", "64 plans", "8,192", "40 ms"],
                ylabel="Mean pruned plans per route")
    axes[1].legend(fontsize=8)
    figure(root, "fig15_component_efficiency", fig)

    repairs = pair(main, "STaR", "B0")
    success = max((item for item in repairs if val(item[0], "attained") and not val(item[1], "attained")),
                  key=lambda item: val(item[0], "reliability") - val(item[1], "reliability"), default=None)
    failure = min((item for item in repairs if item[0]["family"] == "R2" and not val(item[0], "attained")),
                  key=lambda item: route_key(item[0]), default=None)
    partial = max(pair(main, "B4", "B0"), key=lambda item: (
        val(item[0], "reliability") - val(item[1], "reliability"),
        val(item[1], "mean_completion") - val(item[0], "mean_completion"),
    ))
    if success is None or failure is None:
        raise ValueError("This development run does not contain both defined example categories")
    table(root, "examples", ["case", "parent", "variant", "route", "method", "R", "full_completion", "attained"], [
        (label, *route_key(row), row["method"], val(row, "reliability"), val(row, "mean_completion"),
         val(row, "attained")) for label, items in (("restored", success), ("unrestored R2", failure), ("partial", partial))
        for row in items
    ])
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5), layout="constrained")
    for ax, items, label in zip(axes, (success, failure), ("Restored", "Unrestored R2")):
        for row in items:
            ax.plot(val(row, "completion_quantiles"), np.linspace(0, 100, 21), color=COLORS[row["method"]],
                    label=f'{row["method"]}: R={val(row, "reliability"):.3f}')
        ax.set(xlabel="Full completion (time units)", ylabel="Validation percentile",
               title=f"{label}: {items[0]['parent']} {items[0]['variant']} / {items[0]['route_id']}")
        ax.legend(fontsize=8)
    figure(root, "fig12_completion_examples", fig)

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5), layout="constrained")
    for row in partial:
        color = COLORS[row["method"]]
        charging = val(row, "charging")
        offset = -0.17 if row["method"] == "B0" else 0.17
        axes[0].bar(np.arange(len(charging)) + offset, [item["energy"] for item in charging],
                    width=0.33, color=color, label=row["method"])
        axes[1].plot(val(row, "timeline"), color=color, label=row["method"])
    charging = val(partial[0], "charging")
    for item in charging:
        axes[1].axvline(item["stop"], color="gray", linewidth=0.8, linestyle="--")
    axes[0].set(xticks=range(len(charging)), xticklabels=[item["station"] for item in charging],
                xlabel="Charging station ID", ylabel="Energy added (benchmark units)")
    axes[1].set(xlabel="Stop index", ylabel="Zero-wait departure (time units)")
    axes[0].legend()
    first = partial[0]
    fig.suptitle(f"Fixed station sequence: {first['parent']} {first['variant']} / {first['route_id']}")
    figure(root, "fig16_partial_charge_mechanism", fig)

    fig, ax = plt.subplots(figsize=(5.4, 4.7), layout="constrained")
    b0 = pair(main, "STaR", "B0")
    ax.scatter([val(second, "reliability") for first, second in b0],
               [val(first, "reliability") for first, second in b0], s=15, alpha=0.42, color=COLORS["STaR"])
    ax.plot([0, 1], [0, 1], "--", color="black", linewidth=0.8)
    ax.axhline(cfg["target"], color=COLORS["B3"], linewidth=0.8)
    ax.axvline(cfg["target"], color=COLORS["B3"], linewidth=0.8)
    ax.set(xlabel="Unrepaired CON validation reliability", ylabel="STaR validation reliability")
    figure(root, "fig07_validation_before_after", fig)

    def digest(path):
        with path.open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest()

    project = Path(__file__).resolve().parents[1]
    source_paths = ("scripts/analyze_phase25.py", "scripts/verify_phase25_search.py")
    provenance = {
        "analysis_and_replay_source_sha256": {name: digest(project / name) for name in source_paths},
        "experiment_manifest_sha256": digest(root / "manifest.json"),
        "raw_file_sha256": {path.relative_to(root).as_posix(): digest(path)
                            for path in sorted((root / "raw").glob("*/*.json"))},
        "primary_profile": primary, "pairing": "parent, variant, route_id", "resampling_unit": "Homberger parent",
        "bootstrap_repetitions": 9999, "bootstrap_seed": cfg["analysis_seed"], "figure_dpi": 400,
    }
    (root / "analysis_manifest.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/phase25"))
    analyze(parser.parse_args().output)


if __name__ == "__main__":
    main()
