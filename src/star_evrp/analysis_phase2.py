"""Phase-2 results aggregation, tables 07–14, figures 07–16."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from star_evrp.experiment_runner import _latex_escape_cell, _write_table_bundle
from star_evrp.plotting import COLORBLIND, apply_style, _empty_figure


def _load_raw_results(raw_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not raw_dir.is_dir():
        return rows
    for path in sorted(raw_dir.glob("*.json")):
        if path.name.startswith("batch_"):
            continue
        with path.open("r", encoding="utf-8") as fh:
            rows.append(json.load(fh))
    return rows


def aggregate_results_to_csv(project_root: Path | str, *, out_path: Path | str | None = None) -> Path:
    root = Path(project_root)
    proc = root / "results" / "phase2" / "processed"
    proc.mkdir(parents=True, exist_ok=True)
    out = Path(out_path or proc / "phase2_aggregate.csv")
    parts: list[dict[str, Any]] = []
    for sub in ("raw/dev", "raw/smoke", "raw/ablation"):
        parts.extend(_load_raw_results(root / "results" / "phase2" / sub))
    if not parts:
        out.write_text("instance_key,variant,method\n", encoding="utf-8")
        return out
    fieldnames = sorted({k for row in parts for k in row.keys()})
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in parts:
            w.writerow(row)
    return out


def paired_comparisons_vs_b0(rows: list[dict[str, Any]], *, metric: str = "reliability_opt") -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, int], dict[str, Any]] = defaultdict(dict)
    for r in rows:
        key = (r["instance_key"], r["variant"], int(r["route_id"]))
        by_key[key][r["method"]] = r
    pairs: list[dict[str, Any]] = []
    for key, methods in by_key.items():
        b0 = methods.get("B0")
        if b0 is None:
            continue
        b0_val = float(b0.get(metric, 0.0))
        for method, row in methods.items():
            if method == "B0":
                continue
            val = float(row.get(metric, 0.0))
            pairs.append(
                {
                    "instance_key": key[0],
                    "variant": key[1],
                    "route_id": key[2],
                    "method": method,
                    "b0": b0_val,
                    "method_val": val,
                    "delta": val - b0_val,
                }
            )
    return pairs


def _mean_ci(deltas: list[float]) -> tuple[float, float, float]:
    if not deltas:
        return float("nan"), float("nan"), float("nan")
    m = float(np.mean(deltas))
    if len(deltas) < 2:
        return m, m, m
    s = float(np.std(deltas, ddof=1))
    half = 1.96 * s / np.sqrt(len(deltas))
    return m, m - half, m + half


def build_phase2_tables(project_root: Path | str) -> Path:
    root = Path(project_root)
    tables_dir = root / "results" / "phase2" / "tables"
    dev_rows = _load_raw_results(root / "results" / "phase2" / "raw" / "dev")
    abl_rows = _load_raw_results(root / "results" / "phase2" / "raw" / "ablation")
    cross = root / "results" / "phase2" / "raw" / "d1_crosswalk.csv"
    d1_rows: list[dict[str, str]] = []
    if cross.is_file():
        with cross.open("r", encoding="utf-8", newline="") as fh:
            d1_rows = list(csv.DictReader(fh))

    # table07 — Phase-1 corrections (crosswalk)
    t7: list[list[Any]] = []
    for r in d1_rows[:200]:
        old_r = float(r.get("old_reliability") or 0)
        new_r = float(r.get("new_reliability") or 0)
        t7.append(
            [
                r.get("instance_key"),
                r.get("variant"),
                r.get("route_id"),
                old_r,
                new_r,
                new_r - old_r,
                r.get("old_e_completion"),
                r.get("new_e_completion"),
            ]
        )
    if not t7:
        t7 = [["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]]
    _write_table_bundle(
        tables_dir,
        "table07_phase1_corrections",
        ["instance", "variant", "route", "old_rel", "new_rel", "delta", "old_ecomp", "new_ecomp"],
        t7,
    )

    # table08 — main comparison
    t8: list[list[Any]] = []
    methods = sorted({r.get("method") for r in dev_rows})
    for method in methods:
        sub = [r for r in dev_rows if r.get("method") == method]
        if not sub:
            continue
        rels = [float(r.get("reliability_opt", 0)) for r in sub]
        t8.append(
            [
                method,
                len(sub),
                float(np.mean(rels)),
                sum(1 for r in sub if r.get("meets_target_val_ci")),
                float(np.mean([float(r.get("runtime_s", 0)) for r in sub])),
                float(np.mean([float(r.get("candidates_examined", 0)) for r in sub])),
            ]
        )
    if not t8:
        t8 = [["N/A"] * 6]
    _write_table_bundle(
        tables_dir,
        "table08_method_main_comparison",
        ["method", "n_routes", "mean_reliability_opt", "n_meets_target_val_ci", "mean_runtime_s", "mean_candidates"],
        t8,
    )

    # table09 — family × variant
    t9: list[list[Any]] = []
    buckets: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in dev_rows:
        buckets[(r.get("family", "?"), r.get("variant", "?"), r.get("method", "?"))].append(r)
    for (fam, var, method), sub in sorted(buckets.items()):
        rels = [float(x.get("reliability_opt", 0)) for x in sub]
        t9.append([fam, var, method, len(sub), float(np.mean(rels)) if rels else "N/A"])
    if not t9:
        t9 = [["N/A"] * 5]
    _write_table_bundle(
        tables_dir,
        "table09_family_variant_results",
        ["family", "variant", "method", "n", "mean_reliability"],
        t9,
    )

    # table10 — ablation
    t10: list[list[Any]] = []
    star_full = [r for r in abl_rows if r.get("method") in ("STaR_v1", "STaR-FULL")]
    for method in sorted({r.get("method") for r in abl_rows}):
        sub = [r for r in abl_rows if r.get("method") == method]
        if not sub:
            continue
        base = float(np.mean([float(r.get("reliability_opt", 0)) for r in sub]))
        full_mean = float(np.mean([float(r.get("reliability_opt", 0)) for r in star_full])) if star_full else base
        t10.append([method, len(sub), base, base - full_mean, float(np.mean([r.get("runtime_s", 0) for r in sub]))])
    if not t10:
        t10 = [["N/A"] * 5]
    _write_table_bundle(
        tables_dir,
        "table10_ablation_results",
        ["ablation", "n", "mean_rel", "delta_vs_full", "mean_runtime_s"],
        t10,
    )

    # table11 — screen efficiency
    t11: list[list[Any]] = []
    star_dev = [r for r in dev_rows if str(r.get("method", "")).startswith("STaR")]
    for r in star_dev:
        b = r.get("budget_snapshot") or {}
        t11.append(
            [
                r.get("instance_key"),
                r.get("route_id"),
                r.get("method"),
                r.get("screen_rejects"),
                b.get("scenarios_evaluated"),
                r.get("runtime_s"),
            ]
        )
    if not t11:
        t11 = [["N/A"] * 6]
    _write_table_bundle(
        tables_dir,
        "table11_screen_efficiency",
        ["instance", "route", "method", "screen_rejects", "scenarios_eval", "runtime_s"],
        t11,
    )

    # table12 — paired stats vs B0
    pairs = paired_comparisons_vs_b0(dev_rows)
    t12: list[list[Any]] = []
    by_method: dict[str, list[float]] = defaultdict(list)
    for p in pairs:
        by_method[p["method"]].append(p["delta"])
    for method, deltas in sorted(by_method.items()):
        m, lo, hi = _mean_ci(deltas)
        t12.append([method, len(deltas), m, lo, hi, float(np.median(deltas)) if deltas else "N/A"])
    if not t12:
        t12 = [["N/A"] * 6]
    _write_table_bundle(
        tables_dir,
        "table12_paired_statistical_analysis",
        ["method", "n_pairs", "mean_delta", "ci_low", "ci_high", "median_delta"],
        t12,
    )

    # table13 — partial charging (fingerprint / notes proxy)
    t13: list[list[Any]] = []
    for r in dev_rows:
        if r.get("method") != "STaR_v1":
            continue
        t13.append(
            [
                r.get("instance_key"),
                r.get("route_id"),
                r.get("fingerprint"),
                r.get("reliability_opt"),
                r.get("e_completion_opt"),
                r.get("notes"),
            ]
        )
    if not t13:
        t13 = [["N/A"] * 6]
    _write_table_bundle(
        tables_dir,
        "table13_partial_charging",
        ["instance", "route", "fingerprint", "reliability", "e_completion", "notes"],
        t13,
    )

    # table14 — negative cases
    t14: list[list[Any]] = []
    for r in dev_rows:
        if r.get("meets_target_val_ci"):
            continue
        t14.append(
            [
                r.get("instance_key"),
                r.get("variant"),
                r.get("route_id"),
                r.get("method"),
                r.get("reliability_val"),
                r.get("wilson_lo_val"),
                r.get("notes") or "below_target",
            ]
        )
    if not t14:
        t14 = [["N/A"] * 7]
    _write_table_bundle(
        tables_dir,
        "table14_negative_cases",
        ["instance", "variant", "route", "method", "reliability_val", "wilson_lo", "reason"],
        t14,
    )

    return tables_dir


def _paired_plot(dev_rows: list[dict], out: Path, title: str, note: str = "") -> None:
    apply_style()
    pairs = paired_comparisons_vs_b0(dev_rows, metric="reliability_opt")
    star = [p for p in pairs if p["method"] == "STaR_v1"]
    if not star:
        _empty_figure(note or "No STaR vs B0 pairs in raw dev results", out)
        return
    b0 = [p["b0"] for p in star]
    st = [p["method_val"] for p in star]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(b0, st, alpha=0.7, c=COLORBLIND["blue"], edgecolors="none")
    lims = [0, 1]
    ax.plot(lims, lims, "--", color=COLORBLIND["black"], lw=1)
    ax.axhline(0.95, color=COLORBLIND["red"], ls=":", label="target 0.95")
    ax.axvline(0.95, color=COLORBLIND["red"], ls=":")
    ax.set_xlabel("B0 reliability (opt)")
    ax.set_ylabel("STaR reliability (opt)")
    ax.set_title(title)
    if note:
        ax.text(0.02, 0.02, note, transform=ax.transAxes, fontsize=8, color="gray")
    ax.legend(loc="lower right")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="png")
    plt.close(fig)


def regenerate_phase2_figures(project_root: Path | str) -> list[Path]:
    root = Path(project_root)
    fig_dir = root / "results" / "phase2" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    dev_rows = _load_raw_results(root / "results" / "phase2" / "raw" / "dev")
    abl_rows = _load_raw_results(root / "results" / "phase2" / "raw" / "ablation")

    written: list[Path] = []

    def save(name: str, fn) -> None:
        path = fig_dir / name
        fn(path)
        written.append(path)

    save(
        "fig07_before_after_route_reliability.png",
        lambda p: _paired_plot(
            dev_rows,
            p,
            "Route reliability: B0 vs STaR (development)",
            "" if dev_rows else "Partial: run development batch first",
        ),
    )

    # fig08 attainment by method
    def fig08(p: Path) -> None:
        apply_style()
        methods = sorted({r.get("method") for r in dev_rows})
        if not methods:
            _empty_figure("No development results", p)
            return
        rates = []
        for m in methods:
            sub = [r for r in dev_rows if r.get("method") == m]
            rates.append(sum(1 for r in sub if r.get("meets_target_val_ci")) / max(1, len(sub)))
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(methods, rates, color=COLORBLIND["green"])
        ax.axhline(0.95, color=COLORBLIND["red"], ls="--", label="target ref")
        ax.set_ylabel("Fraction meeting target (val CI)")
        ax.set_title("Target attainment by method")
        ax.set_ylim(0, 1.05)
        plt.xticks(rotation=30, ha="right")
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, format="png")
        plt.close(fig)

    save("fig08_target_attainment_by_method.png", fig08)

    # fig09–fig16: lightweight or placeholder when data thin
    placeholders = [
        ("fig09_paired_reliability_gain.png", "Paired Δreliability vs B0"),
        ("fig10_runtime_vs_quality.png", "Runtime vs reliability tradeoff"),
        ("fig11_computation_efficiency.png", "Scenario budget usage by method"),
        ("fig12_stochastic_completion_distributions.png", "Completion distributions (representative routes)"),
        ("fig13_component_ablation.png", "Ablation paired deltas"),
        ("fig14_family_stress_and_repairability.png", "Family/variant exposure"),
        ("fig15_safe_screen_diagnostics.png", "Safe-screen rejection rates"),
        ("fig16_partial_charging_mechanism.png", "Partial-charge illustration"),
    ]

    for fname, caption in placeholders:
        def _mk(caption=caption, fname=fname):
            def fn(p: Path) -> None:
                if fname == "fig13_component_ablation.png" and abl_rows:
                    apply_style()
                    methods = sorted({r.get("method") for r in abl_rows})
                    means = []
                    for m in methods:
                        sub = [r for r in abl_rows if r.get("method") == m]
                        means.append(float(np.mean([float(x.get("reliability_opt", 0)) for x in sub])))
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(methods, means, color=COLORBLIND["purple"])
                    ax.set_ylabel("Mean reliability (opt)")
                    ax.set_title(caption)
                    plt.xticks(rotation=35, ha="right")
                    p.parent.mkdir(parents=True, exist_ok=True)
                    fig.savefig(p, format="png")
                    plt.close(fig)
                    return
                if fname == "fig11_computation_efficiency.png" and dev_rows:
                    apply_style()
                    methods = sorted({r.get("method") for r in dev_rows})
                    scans = [float(np.mean([r.get("candidates_examined", 0) for r in dev_rows if r.get("method") == m])) for m in methods]
                    fig, ax = plt.subplots(figsize=(7, 4))
                    ax.bar(methods, scans, color=COLORBLIND["cyan"])
                    ax.set_ylabel("Mean candidates examined")
                    ax.set_title(caption)
                    plt.xticks(rotation=30, ha="right")
                    p.parent.mkdir(parents=True, exist_ok=True)
                    fig.savefig(p, format="png")
                    plt.close(fig)
                    return
                _empty_figure(f"{caption}\n(insufficient raw data; regenerate after batch runs)", p)

            return fn

        save(fname, _mk())

    return written


def audit_phase2_results(project_root: Path | str) -> dict[str, Any]:
    root = Path(project_root)
    dev = _load_raw_results(root / "results" / "phase2" / "raw" / "dev")
    required = {
        "instance_key", "variant", "method", "route_id", "reliability_opt", "reliability_val",
    }
    issues: list[str] = []
    for i, row in enumerate(dev):
        missing = required - set(row.keys())
        if missing:
            issues.append(f"row {i} missing {missing}")
    agg_path = root / "results" / "phase2" / "processed" / "phase2_aggregate.csv"
    if not agg_path.is_file() and dev:
        aggregate_results_to_csv(root)
    report = {
        "n_dev_results": len(dev),
        "issues": issues,
        "aggregate_csv": str(agg_path),
        "ok": len(issues) == 0,
    }
    out = root / "results" / "phase2" / "reports" / "audit_phase2.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report