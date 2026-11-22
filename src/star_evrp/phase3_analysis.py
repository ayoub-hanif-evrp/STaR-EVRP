"""Preregistered holdout estimands, publication outputs, and integrity audit."""

from __future__ import annotations

import csv
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from star_evrp.data_loader import sha256_file
from star_evrp.phase3 import canonical, digest, read_bundle, verified_freeze
from star_evrp.results_io import load_json, save_json


COLOR = {"B0": "#555555", "B1": "#AA4499", "B2": "#E69F00", "B3": "#0072B2", "B4": "#009E73",
         "STaR": "#D55E00", "STaR_no_partial": "#6B5895"}
FIGURES = (
    "fig17_holdout_reliability_stars_vs_b4_b3", "fig18_holdout_target_attainment",
    "fig19_reliability_completion_frontier", "fig20_search_scenarios_vs_reliability",
    "fig21_runtime_vs_reliability", "fig22_stochastic_repair_by_family_variant",
    "fig23_partial_vs_topology_repair", "fig24_ablation_and_budget_sensitivity",
    "fig25_individual_route_case_study", "fig26_validation_uncertainty",
)
TABLES = ("population", "overall", "paired", "family_variant", "budget", "mechanism",
          "negative", "robustness", "provenance", "parent_effects", "case_routes")
LATEX = str.maketrans({"\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&",
                      "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}"})


def png_info(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    cursor = 8
    dims = density = None
    while cursor + 12 <= len(data):
        size, kind = struct.unpack(">I4s", data[cursor:cursor+8])
        payload = data[cursor+8:cursor+8+size]
        if kind == b"IHDR":
            dims = struct.unpack(">II", payload[:8])
        if kind == b"pHYs":
            density = struct.unpack(">IIB", payload)
        if kind in (b"tEXt", b"iTXt") and b"placeholder" in payload.lower():
            raise ValueError(f"PNG contains placeholder metadata: {path}")
        cursor += size + 12
    if dims is None or min(dims) < 1000 or density is None or density[2] != 1 or any(
        not 399 <= value * 0.0254 <= 401 for value in density[:2]
    ):
        raise ValueError(f"PNG dimensions or DPI invalid: {path}")
    return {"name": path.name, "px": list(dims), "dpi": 400, "sha256": sha256_file(path)}


def table(out, name, columns, rows):
    directory = out / "tables"
    directory.mkdir(parents=True, exist_ok=True)
    strings = [[("" if value is None else f"{value:.8g}" if isinstance(value, float) else str(value))
                for value in row] for row in rows]
    with (directory / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(strings)
    mode = "longtable" if len(rows) > 30 else "tabular"
    tex = [r"\begin{" + mode + "}{" + "l" * len(columns) + "}", r"\hline"]
    for index, row in enumerate([columns, *strings]):
        tex.append(" & ".join(item.translate(LATEX) for item in row) + r" \\")
        if index == 0:
            tex.append(r"\hline")
    tex.extend([r"\hline", r"\end{" + mode + "}"])
    (directory / f"{name}.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    md = ["| " + " | ".join(row) + " |" for row in [columns, ["---"] * len(columns), *strings]]
    (directory / f"{name}.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def grouped(rows, get_key):
    result = defaultdict(list)
    for row in rows:
        result[get_key(row)].append(row)
    return result


def mean(values):
    values = list(values)
    return float(np.mean(values)) if values else None


def boot(values, parents, seed, draws):
    """Family-stratified percentile bootstrap of route and parent means."""
    stats = grouped(values, lambda item: item[0])
    sums = np.array([sum(pair[1] for pair in stats[parent]) for parent, _ in parents], dtype=float)
    counts = np.array([len(stats[parent]) for parent, _ in parents])
    rng = np.random.default_rng(seed)
    strata = grouped(range(len(parents)), lambda index: parents[index][1])
    samples = np.concatenate([rng.choice(indices, size=(draws, len(indices)), replace=True)
                              for indices in strata.values()], axis=1)
    center = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)
    active = counts[samples].sum(axis=1) > 0
    if not active.any():
        return [None] * 6
    route_draws = sums[samples].sum(axis=1)[active] / counts[samples].sum(axis=1)[active]
    balanced = center[samples].sum(axis=1)[active] / (counts[samples] > 0).sum(axis=1)[active]
    return [float(sums.sum() / counts.sum()), *map(float, np.quantile(route_draws, [.025, .975])),
            float(center[counts > 0].mean()), *map(float, np.quantile(balanced, [.025, .975]))]


def study(root, out):
    manifest, _ = verified_freeze(root, out)
    cfg = manifest["config"]
    token = digest(canonical(manifest))
    execution = load_json(out / "reports/execution.json")
    replay = load_json(out / "reports/replay.json")
    if execution["errors"] or replay["errors"] or execution["freeze"] != token or replay["freeze"] != token:
        raise ValueError("Missing complete execution and independent replay")
    expected_cases = {f'{row["instance_key"]}__{row["variant"]}' for row in manifest["holdout"]}
    for report in (execution, replay):
        if len(report["cases"]) != 96 or {case["case"] for case in report["cases"]} != expected_cases:
            raise ValueError("Missing expected benchmark case")
    rows, raw_hashes, known = {}, {}, set()
    for case in execution["cases"]:
        eligible = case["eligible_route_ids"]
        if len(eligible) != case["exposed"] or case["routes"] != case["zero_charge"] + case["exposed"]:
            raise ValueError("Invalid exposure accounting")
        path = out / "raw/con" / f'{case["case"]}.json.gz'
        raw_hashes[path.relative_to(out).as_posix()] = sha256_file(path)
        for profile, rule in cfg["profiles"].items():
            for start in range(0, len(eligible), cfg["batch_routes"]):
                basename = f'{case["case"]}__{start:04d}.json.gz'
                raw_path, plan_path = out / "raw" / profile / basename, out / "plans" / profile / basename
                loaded, plans = read_bundle(raw_path), read_bundle(plan_path)
                for path in (raw_path, plan_path):
                    raw_hashes[path.relative_to(out).as_posix()] = sha256_file(path)
                    known.add(path)
                if loaded["context"] != plans["context"] or loaded["context"]["freeze"] != token:
                    raise ValueError("Frozen prefix mismatch")
                requested = [(rid, method) for rid in eligible[start:start+cfg["batch_routes"]] for method in rule["methods"]]
                if len(plans["rows"]) != len(requested) or len(loaded["rows"]) != len(requested):
                    raise ValueError("Wrong number of metric/plan records")
                for expected, record, plan in zip(requested, loaded["rows"], plans["rows"]):
                    if (record["route_id"], record["method"]) != expected or (
                        plan["route_id"], plan["method"]
                    ) != expected or record["plan_sha256"] != digest(canonical(plan)):
                        raise ValueError("Saved metric and plan cannot be paired")
                    key = profile, case["parent"], case["variant"], *expected
                    if key in rows or record["validation"]["n"] != cfg["validation_samples"]:
                        raise ValueError("Repeated or incomplete result")
                    rows[key] = {**record, "plan": plan, "profile": profile, "parent": case["parent"],
                                 "variant": case["variant"], "family": case["family"]}
    if len(rows) != sum(case["replayed"] for case in replay["cases"]):
        raise ValueError("Independent replay did not cover all saved plans")
    if known != set((out / "plans").glob("*/*.json.gz")) | {
        path for path in (out / "raw").glob("*/*.json.gz") if path.parent.name != "con"
    }:
        raise ValueError("Unexpected additional raw results")
    return manifest, execution["cases"], rows, raw_hashes


def val(row, field):
    return row["validation"][field]


def paired(rows, profile, challenger, control):
    return [(row, rows[(phase, parent, variant, rid, control)])
            for (phase, parent, variant, rid, method), row in rows.items()
            if phase == profile and method == challenger]


def overall(sub, target):
    return [
        len(sub), mean(val(row, "reliability") for row in sub),
        sum(val(row, "reliability") >= target for row in sub),
        sum(val(row, "attained") for row in sub),
        sum(val(row, "wilson95_two_sided")[0] <= target <= val(row, "wilson95_two_sided")[1] for row in sub),
        mean(val(row, "completion") for row in sub),
        mean(row["work"]["scenarios_evaluated"] for row in sub),
        mean(row["work"]["elapsed_seconds"] * 1000 for row in sub),
        mean(row["cpu_seconds"] * 1000 for row in sub),
    ]


def charts(out, cfg, summaries, cells, rows, phases, paired_rows, controls, cases, case_record):
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "axes.axisbelow": True, "grid.alpha": .2})
    directory = out / "figures"
    directory.mkdir(parents=True, exist_ok=True)
    target = cfg["target"]
    primary = cfg["primary"]
    palette = COLOR
    methods = cfg["profiles"][primary]["methods"]

    def save(index, fig):
        fig.savefig(directory / (FIGURES[index] + ".png"), dpi=400, facecolor="white")
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.5), layout="constrained")
    for ax, control in zip(axes, ("B4", "B3")):
        pairs = paired(rows, primary, "STaR", control)
        ax.scatter([val(second, "reliability") for first, second in pairs],
                   [val(first, "reliability") for first, second in pairs],
                   alpha=.24, s=8, color=palette["STaR"], rasterized=True)
        ax.plot([0, 1], [0, 1], "--", color="#505050", lw=.8)
        ax.set(xlabel=f"{control} reliability", ylabel="STaR reliability", xlim=(-.025, 1.025), ylim=(-.025, 1.025),
               title=f"{len(pairs):,} exposed routes")
    save(0, fig)

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.6), layout="constrained")
    for index, (stat, label) in enumerate(((2, "Point estimate ≥ 0.95"), (3, "One-sided lower bound ≥ 0.95"))):
        values = [100 * summaries[(primary, method)][stat] / summaries[(primary, method)][0] for method in methods]
        axes[0].bar(np.arange(len(methods)) + (index - .5) * .36, values, width=.35, label=label,
                    color=("#72A0C6", "#0072B2")[index])
    axes[0].set(xticks=range(len(methods)), xticklabels=[m.replace("STaR_no_partial", "No partial") for m in methods],
                ylabel="Attained (%)", ylim=(0, 101), title=f"All exposed routes (n={summaries[(primary, 'B0')][0]:,})")
    axes[0].tick_params(axis="x", rotation=35)
    axes[0].legend(fontsize=7)
    families = sorted({family for family, _, _ in cells})
    for method in ("B0", "B3", "B4", "STaR"):
        points = [[cells[(family, var, method)] for var in ("A", "B") if (family, var, method) in cells]
                  for family in families]
        axes[1].plot(families, [100 * sum(p[3] for p in block) / sum(p[0] for p in block) for block in points],
                     "o-", label=method, color=palette[method])
    axes[1].set(ylabel="Lower-bound attainment (%)", ylim=(0, 103))
    axes[1].legend(ncol=2, fontsize=7)
    save(1, fig)

    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.6), layout="constrained")
    for ax, control in zip(axes, ("B4", "B3")):
        pairs = paired(rows, primary, "STaR", control)
        ax.scatter([val(first, "completion") - val(second, "completion") for first, second in pairs],
                   [100 * (val(first, "reliability") - val(second, "reliability")) for first, second in pairs],
                   s=8, alpha=.27, color=palette["STaR"])
        ax.axvline(0, color="black", lw=.7)
        ax.axhline(0, color="black", lw=.7)
        ax.set(xlabel="Δ full completion (native units)", ylabel="Δ reliability (pp)", title=f"STaR minus {control}")
    save(2, fig)

    for index, metric, label in ((3, 6, "Mean search scenarios"), (4, 7, "Mean elapsed search time (ms)")):
        fig, ax = plt.subplots(figsize=(6.1, 3.8), layout="constrained")
        for method in ("B3", "B4", "STaR"):
            points = sorted((summaries[(profile, method)][metric], controls[(profile, method)], profile)
                            for profile in phases)
            x, intervals, _ = zip(*points)
            vals = np.array(intervals)[:, :3] * 100
            ax.vlines(x, vals[:, 1], vals[:, 2], color=palette[method], lw=1.0)
            ax.plot(x, vals[:, 0], "o", color=palette[method], label=method)
        ax.set(xlabel=label, ylabel="Mean validation reliability (%)")
        ax.legend()
        save(index, fig)

    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.8), sharey=True, layout="constrained")
    for ax, variant in zip(axes, ("A", "B")):
        for method in ("B0", "B3", "B4", "STaR"):
            values = [cells.get((family, variant, method), [0, None])[1] for family in families]
            ax.plot(families, [float("nan") if value is None else 100 * value for value in values],
                    "o-", color=palette[method], label=method)
        ax.set(title=f"Variant {variant}", ylabel="Mean validation reliability (%)", ylim=(0, 103))
    axes[0].legend(fontsize=7, ncol=2)
    save(5, fig)

    fig, axes = plt.subplots(1, 2, figsize=(7.7, 3.6), layout="constrained")
    pairs = paired(rows, primary, "STaR", "B4")
    options = [("Same topology", [pair for pair in pairs if pair[0]["plan"]["station_positions"] == pair[1]["plan"]["station_positions"]]),
               ("Changed topology", [pair for pair in pairs if pair[0]["plan"]["station_positions"] != pair[1]["plan"]["station_positions"]])]
    for ax, field, scale, ylabel in ((axes[0], "reliability", 100, "Δ reliability (pp)"),
                                      (axes[1], "completion", 1, "Δ full completion (time units)")):
        plotted = [(label, sub) for label, sub in options if sub]
        ax.boxplot([[scale * (val(first, field) - val(second, field)) for first, second in sub]
                    for _, sub in plotted], tick_labels=[f"{label}\nn={len(sub)}" for label, sub in plotted],
                   showfliers=True, flierprops={"markersize": 2, "alpha": .25})
        ax.axhline(0, color="black", linewidth=.7)
        ax.set(ylabel=ylabel)
    save(6, fig)

    fig, axes = plt.subplots(1, 2, figsize=(7.7, 3.6), layout="constrained")
    for method in ("B3", "B4", "STaR"):
        axes[0].plot(phases, [100 * summaries[(profile, method)][3] / summaries[(profile, method)][0]
                             for profile in phases], "o-", color=palette[method], label=method)
    axes[0].set(ylabel="Lower-bound attainment (%)", xlabel="Frozen profile")
    axes[0].legend(fontsize=7, ncol=2)
    pair_metrics = [row for row in paired_rows if row["profile"] == primary and row["competitor"] == "STaR_no_partial"]
    vals = np.array([[row["estimate"], row["lower95"], row["upper95"]] for row in pair_metrics
                     if row["metric"] in ("reliability", "attained")]) * 100
    axes[1].vlines([0, 1], vals[:, 1], vals[:, 2], color=palette["STaR"], lw=1.2)
    axes[1].plot([0, 1], vals[:, 0], "o", color=palette["STaR"])
    axes[1].axhline(0, color="black", lw=.7)
    axes[1].set(xticks=[0, 1], xticklabels=["Reliability", "Attainment"], ylabel="STaR – no partial (pp)")
    save(7, fig)

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.6), layout="constrained")
    parent, variant, rid = case_record
    for method in ("B0", "B4", "STaR"):
        row = rows[(primary, parent, variant, rid, method)]
        events = row["plan"]["events"]
        customers = [event for event in events if event[1] == "customer"]
        axes[0].plot(np.arange(len(customers)) + 1, [event[5] - event[2] for event in customers],
                     color=palette[method], label=method)
        axes[0].plot(len(customers) + 1, events[-1][5] - events[-1][3], "s", color=palette[method], ms=4)
        axes[1].plot(val(row, "completion_quantiles"), np.arange(21)*5, color=palette[method], label=method)
    axes[0].set(xlabel="Fixed customer order; square = depot", ylabel="Zero-wait deadline margin (native units)")
    axes[1].set(xlabel="Full route completion (native units)", ylabel="Validation percentile")
    axes[1].legend()
    fig.suptitle(f"First eligible R2-A route by parent and route ID: {parent}/{variant}/{rid}")
    save(8, fig)

    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.5), layout="constrained")
    for ax, method in zip(axes, ("B3", "STaR")):
        sub = sorted((r for r in rows.values() if r["profile"] == primary and r["method"] == method
                      and abs(val(r, "reliability") - target) <= .03), key=lambda row: val(row, "reliability"))
        if not sub:
            sub = sorted((r for r in rows.values() if r["profile"] == primary and r["method"] == method),
                         key=lambda row: abs(val(row, "reliability") - target))[:10]
            sub.sort(key=lambda row: val(row, "reliability"))
            title = "10 nearest estimates"
        else:
            title = "Within 3 pp of target"
        vals = np.array([val(row, "reliability") for row in sub])
        ci = np.array([val(row, "wilson95_two_sided") for row in sub])
        ax.vlines(range(len(sub)), ci[:, 0], ci[:, 1], lw=.85, color=palette[method])
        ax.scatter(range(len(sub)), vals, s=6, color=palette[method])
        ax.axhline(target, lw=.7, color="black")
        ax.set(xlabel="Routes sorted by estimate", ylabel="Reliability and two-sided 95% Wilson CI", title=f"{method}: {title}")
    save(9, fig)


def analyze(root, out):
    start = perf_counter()
    manifest, cases, rows, raw_hashes = study(root, out)
    cfg = manifest["config"]
    primary, target = cfg["primary"], cfg["target"]
    phases = list(cfg["profiles"])
    parents = sorted({(case["parent"], case["family"]) for case in cases})
    main = [row for row in rows.values() if row["profile"] == primary]
    groups = grouped(rows.values(), lambda row: (row["profile"], row["method"]))
    metrics = ["n", "mean_R", "point_at_target", "lower_bound_attained", "two_sided_CI_contains_target",
               "full_completion_time", "search_scenarios", "search_wall_ms", "search_cpu_ms"]
    summary = {key: overall(sub, target) for key, sub in groups.items()}
    table(out, "overall", ["method", *metrics], [(method, *summary[(primary, method)])
          for method in cfg["profiles"][primary]["methods"]])
    budget_fields = ["generated", "deterministic_checks", "screen_checks", "generation_seconds",
                     "deterministic_seconds", "screening_seconds", "simulation_seconds"]
    table(out, "budget", ["profile", "method", "unique_plan_cap", "scenario_cap", "cooperative_wall_limit_s",
                           *metrics, *[f"mean_{name}" for name in budget_fields],
                           "mean_validation_ms_including_stress_if_applicable", "wall_overruns",
                           "bound_rejections", "prefix_rejections"], [
        (profile, method, *[cfg["profiles"][profile]["limits"][name] for name in
                            ("max_candidate_evals", "max_scenario_evals", "wall_seconds")],
         *summary[(profile, method)], *(mean(row["work"][name] for row in sub) for name in budget_fields),
         mean(row["validation_seconds"] * 1000 for row in sub),
         sum(row["work"]["elapsed_seconds"] > cfg["profiles"][profile]["limits"]["wall_seconds"] for row in sub),
         sum(row["screen_rejections"] for row in sub), sum(row["prefix_rejections"] for row in sub))
        for (profile, method), sub in sorted(groups.items())
    ])
    by_cell = grouped(main, lambda row: (row["family"], row["variant"], row["method"]))
    cells = {key: overall(sub, target) for key, sub in by_cell.items()}
    base_cells = {(family, var): sub for (family, var, method), sub in by_cell.items() if method == "B0"}
    table(out, "family_variant", ["family", "variant", "method", *metrics, "below_target_B0", "repaired"], [
        (*key, *values, sum(val(row, "reliability") < target for row in base_cells[key[:2]]),
         sum(val(row, "attained") and
             val(rows[(primary, row["parent"], row["variant"], row["route_id"], "B0")], "reliability") < target
             for row in by_cell[key]))
        for key, values in sorted(cells.items())
    ])
    pop = []
    for key, block in sorted(grouped(cases, lambda c: (c["family"], c["variant"])).items()):
        base = base_cells.get(key, [])
        pop.append((*key, len(block), sum(case["routes"] for case in block), sum(case["exposed"] for case in block),
                    sum(case["zero_charge"] for case in block), sum(val(row, "reliability") < target for row in base)))
    totals = ("All", "A+B", *(sum(row[index] for row in pop) for index in range(2, 7)))
    table(out, "population", ["family", "variant", "instances", "all_routes", "exposed", "zero_charge", "below_target_B0"],
          [*pop, totals])
    seed, draws = cfg["statistical_seed"], cfg["bootstrap_draws"]
    keys = [
        "profile", "competitor", "metric", "n", "parents", "estimate", "lower95", "upper95",
        "parent_equal_estimate", "parent_equal_lower95", "parent_equal_upper95",
    ]
    differences = []
    per_parent = []
    controls = {}
    for profile in phases:
        for method in ("B3", "B4", "STaR"):
            controls[(profile, method)] = boot([(r["parent"], val(r, "reliability"))
                                                 for r in groups[(profile, method)]], parents, seed, draws)
        for method in cfg["profiles"][profile]["methods"]:
            if method == "STaR":
                continue
            pairs = paired(rows, profile, "STaR", method)
            comparisons = {
                "reliability": [(first["parent"], val(first, "reliability")-val(second, "reliability"))
                                for first, second in pairs],
                "attained": [(first["parent"], int(val(first, "attained"))-int(val(second, "attained")))
                             for first, second in pairs],
                "full_completion": [(first["parent"], val(first, "completion")-val(second, "completion"))
                                     for first, second in pairs],
                "full_completion_common_attained": [
                    (first["parent"], val(first, "completion")-val(second, "completion"))
                    for first, second in pairs if val(first, "attained") and val(second, "attained")
                ],
                "relative_full_completion_percent": [
                    (first["parent"], 100*(val(first, "completion")/val(second, "completion")-1))
                    for first, second in pairs if val(second, "completion") > 0
                ],
                "search_scenarios": [(first["parent"], first["work"]["scenarios_evaluated"]-
                                      second["work"]["scenarios_evaluated"]) for first, second in pairs],
                "wall_ms": [(first["parent"], 1000*(first["work"]["elapsed_seconds"]-
                                                   second["work"]["elapsed_seconds"])) for first, second in pairs],
            }
            for name, observed in comparisons.items():
                differences.append(dict(zip(keys, [profile, method, name, len(observed), len({r[0] for r in observed}),
                                                    *boot(observed, parents, seed, draws)])))
                if profile == primary and method in ("B4", "B3"):
                    per_parent.extend((method, name, parent, len(block), mean(item[1] for item in block))
                                      for parent, block in sorted(grouped(observed, lambda item: item[0]).items()))
    table(out, "paired", keys, [list(record.values()) for record in differences])
    table(out, "parent_effects", ["competitor", "metric", "parent", "paired_routes", "mean_difference"], per_parent)

    mechanisms = []
    mechanism_contributions = {}
    pairs = paired(rows, primary, "STaR", "B4")
    for group, sub in sorted(grouped(pairs, lambda pair: (
        "topology_changed" if pair[0]["plan"]["station_positions"] != pair[1]["plan"]["station_positions"]
        else "same_topology"
    )).items()):
        diff = [val(first, "reliability")-val(second, "reliability") for first, second in sub]
        contribution = sum(diff) / len(pairs)
        mechanism_contributions[group] = contribution
        mechanisms.append((group, len(sub), mean(diff), contribution,
                           mean(val(first, "completion")-val(second, "completion") for first, second in sub),
                           mean(first["plan"]["energy_added"]-second["plan"]["energy_added"] for first, second in sub),
                           mean(len(first["plan"]["station_positions"])-len(second["plan"]["station_positions"])
                                for first, second in sub)))
    table(out, "mechanism", ["comparison_stratum", "n", "mean_delta_R", "contribution_to_overall_delta_R",
                              "mean_delta_completion", "mean_delta_energy", "mean_delta_visits"], mechanisms)
    negative = []
    for row in sorted(main, key=lambda r: (r["parent"], r["variant"], r["route_id"], r["method"])):
        if val(row, "attained"):
            continue
        count = val(row, "n")
        reason = "statistically_uncertain" if val(row, "reliability") >= target else max(
            ("customer_only", "depot_only", "joint"), key=lambda item: dict(
                customer_only=val(row, "late_customer")-val(row, "late_both"),
                depot_only=val(row, "late_depot")-val(row, "late_both"),
                joint=val(row, "late_both"),
            )[item]
        )
        negative.append((row["parent"], row["variant"], row["family"], row["route_id"], row["method"], reason,
                         val(row, "reliability"), val(row, "wilson95_lower_one_sided"),
                         val(row, "late_customer")/count, val(row, "late_depot")/count, val(row, "completion"),
                         row["plan"]["screen_upper_bound"]))
    table(out, "negative", ["parent", "variant", "family", "route", "method", "classification", "R",
                            "one_sided_lower", "late_customer", "late_depot", "completion", "plan_upper_bound"], negative)

    stress_rows = []
    for stress, rule in cfg["stress"].items():
        for method in cfg["stress_methods"]:
            sub = groups[(primary, method)]
            values = [row["stress"][stress] for row in sub]
            stress_rows.append((stress, method, rule["scale"], rule["sigma"], rule["rho"], len(values), mean(v["reliability"] for v in values),
                                sum(v["attained"] for v in values), mean(v["completion"] for v in values)))
    table(out, "robustness", ["stress", "method", "wait_scale", "sigma_scale", "normal_copula_rho", "n",
                              "mean_R", "lower_bound_attained", "full_completion"], stress_rows)

    first = min((row["parent"], row["variant"], row["route_id"]) for row in main
                if row["family"] == "R2" and row["variant"] == "A" and row["method"] == "B0")
    example = []
    for method in ("B0", "B4", "STaR"):
        row = rows[(primary, *first, method)]
        for index, event in enumerate(row["plan"]["events"]):
            example.append((*first, method, index, *event, val(row, "reliability"), val(row, "completion")))
    table(out, "case_routes", ["parent", "variant", "route", "method", "stop", "node", "kind",
                               "zero_wait_service", "zero_wait_departure", "charged_energy", "deadline",
                               "validated_route_R", "expected_full_completion"], example)
    preflight = load_json(out / "manifests/preflight.json")
    replay = load_json(out / "reports/replay.json")
    table(out, "provenance", ["audit_item", "value"], [
        ("Tagged revision", manifest["commit"]), ("Tag", manifest["tag"]),
        ("Tests passed", preflight["tests_passed"]), ("Parents", len(parents)),
        ("Holdout instances", len(cases)), ("Replayed plans", len(rows)),
        ("Replayed scalar checks per plan/model", cfg["validation_scalar_checks"]),
        ("Validation draws per plan/model", cfg["validation_samples"]),
        ("Raw and plan batches checked", len(raw_hashes)), ("Revalidation elapsed s", replay["elapsed_seconds"]),
        *manifest["dependencies"].items(),
    ])
    charts(out, cfg, summary, cells, rows, phases, differences, controls, cases, first)
    results = {
        "commit": manifest["commit"], "tag": manifest["tag"], "n_parents": len(parents), "population": list(totals),
        "primary": {method: dict(zip(metrics, summary[(primary, method)])) for method in cfg["profiles"][primary]["methods"]},
        "paired": differences, "family": [dict(zip(("family", "variant", "method", *metrics), [*key, *values]))
                                          for key, values in cells.items()],
        "effect_contributions": mechanism_contributions, "example": list(first), "selected_plans": len(rows),
        "stress_results": [list(row) for row in stress_rows], "tests": preflight["tests_passed"],
        "analysis_seconds": perf_counter() - start,
    }
    save_json(out / "processed/summary.json", results)
    generated = [out / "processed/summary.json", *[out / "figures" / f"{fig}.png" for fig in FIGURES],
                 *[out / "tables" / f"{name}.{ext}" for name in TABLES for ext in ("csv", "tex", "md")]]
    save_json(out / "processed/provenance.json", {
        "freeze": digest(canonical(manifest)), "raw": raw_hashes,
        "reports": {name: sha256_file(out / f"reports/{name}.json") for name in ("execution", "replay")},
        "generated": {path.relative_to(out).as_posix(): sha256_file(path) for path in generated},
        "figures": [png_info(out / "figures" / f"{fig}.png") for fig in FIGURES],
        "generator": "python -B scripts/phase3.py analyze",
    })


def audit(root, out):
    manifest, cases, rows, raw_hashes = study(root, out)
    evidence = load_json(out / "processed/provenance.json")
    if evidence["raw"] != raw_hashes or evidence["freeze"] != digest(canonical(manifest)):
        raise ValueError("Provenance check failed")
    for name, value in evidence["generated"].items():
        if sha256_file(out / name) != value:
            raise ValueError(f"Stale generated artifact: {name}")
    for name, value in evidence["reports"].items():
        if sha256_file(out / f"reports/{name}.json") != value:
            raise ValueError("Replay/execution report changed")
    if [png_info(out / "figures" / f"{fig}.png") for fig in FIGURES] != evidence["figures"]:
        raise ValueError("PNG audit failure")
    expected = {out / "figures" / f"{fig}.png" for fig in FIGURES}
    if set((out / "figures").iterdir()) != expected:
        raise ValueError("Unexpected figure output")
    result = {"status": "pass", "commit": manifest["commit"], "tag": manifest["tag"], "cases": len(cases),
              "plans": len(rows), "raw_plan_files": len(raw_hashes), "figures": len(FIGURES), "table_families": len(TABLES)}
    save_json(out / "reports/audit.json", result)
    return result


def paper(root, out):
    from star_evrp.phase3_paper import render

    audit(root, out)
    render(root, out)
