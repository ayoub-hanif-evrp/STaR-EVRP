"""Experiment orchestration: inventory, baselines, stochastic audit, tables."""

from __future__ import annotations

import csv
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from star_evrp.baseline import generate_baseline, save_baseline_solution
from star_evrp.data_loader import (
    build_partition_manifest,
    iter_instances,
    inventory_summary,
    load_all_instances,
)
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.results_io import list_completed_keys, load_json, result_key, save_json
from star_evrp.risk_bounds import reliability_upper_bound
from star_evrp.stochastic_simulator import simulate_route_stochastic
from star_evrp.types import Instance, Solution


def load_experiment_config(path: Path | str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def environment_provenance(config: dict[str, Any]) -> dict[str, Any]:
    import numpy
    import scipy

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "config_experiment": config.get("experiment"),
        "scenario_seed": config.get("simulation", {}).get("scenario_seed"),
        "baseline_seed": config.get("baseline", {}).get("seed"),
    }


def classify_failure_mode(
    row: dict[str, Any],
    *,
    target: float = 0.95,
) -> str:
    if not row.get("det_feasible", True):
        return "deterministically_infeasible"
    if row.get("num_charging_visits", 0) == 0:
        return "no_stochastic_exposure"
    rel = float(row.get("reliability", 0.0))
    hi = float(row.get("wilson_ci_high", 1.0))
    lo = float(row.get("wilson_ci_low", 0.0))
    if rel >= target and lo >= target - 0.02:
        return "high_reliability_charging"
    if lo < target <= hi:
        return "uncertainty_near_threshold"
    fc = row.get("failure_counts") or {}
    cust = fc.get("customer_time_window", 0)
    depot = fc.get("depot_closing", 0)
    if cust and depot:
        return "customer_and_depot_failures"
    if cust:
        return "customer_time_window_failures"
    if depot:
        return "depot_return_failures"
    if rel < target:
        return "low_reliability_other"
    return "high_reliability_charging"


def _min_customer_slack(instance: Instance, trace) -> float:
    best = float("inf")
    for st in trace.stops:
        node = instance.node(st.node_id)
        if node.node_type.value != "customer":
            continue
        slack = node.due_date - st.service_start_time
        best = min(best, slack)
    return 0.0 if best == float("inf") else float(best)


def audit_instance(
    instance: Instance,
    solution: Solution,
    config: dict[str, Any],
    *,
    sim_config: SimulatorConfig,
) -> dict[str, Any]:
    sim_cfg = config.get("simulation", {})
    n_scen = int(sim_cfg.get("scenarios_per_route", 2000))
    master_seed = int(sim_cfg.get("scenario_seed", 0))
    target = float(config.get("target_route_reliability", 0.95))

    route_rows: list[dict[str, Any]] = []
    for route in solution.routes:
        if not route.stops:
            continue
        det_tr = simulate_route_fixed(instance, route, sim_config)
        stoch = simulate_route_stochastic(
            instance,
            route,
            sim_config,
            num_scenarios=n_scen,
            master_seed=master_seed,
        )
        bound = reliability_upper_bound(instance, route, sim_config, target=target)
        row = {
            "instance_key": instance.instance_key,
            "variant": instance.variant,
            "family": instance.family,
            "partition": instance.partition,
            "route_id": route.route_id,
            "num_customers": len(route.customer_indices or []),
            "num_charging_visits": stoch.num_charging_visits,
            "det_feasible": det_tr.feasible,
            "det_completion": det_tr.end_clock,
            "min_customer_slack": _min_customer_slack(instance, det_tr),
            "depot_slack": float(instance.depot_closing_time - det_tr.end_clock),
            **stoch.to_dict(),
            "upper_bound_u": bound.upper_bound_u,
            "safe_reject": bound.safe_reject,
            "critical_visit_index": bound.critical_visit_index,
            "isolated_tau": bound.tau,
        }
        row["failure_mode"] = classify_failure_mode(row, target=target)
        route_rows.append(row)

    pops = population_summary(route_rows, target=target)
    return {
        "instance_key": instance.instance_key,
        "variant": instance.variant,
        "family": instance.family,
        "partition": instance.partition,
        "method": solution.method,
        "solution_feasible": solution.feasible,
        "num_routes": len(solution.routes),
        "routes": route_rows,
        "populations": pops,
        "provenance": environment_provenance(config),
    }


def population_summary(rows: list[dict[str, Any]], *, target: float = 0.95) -> dict[str, Any]:
    def stats(subset: list[dict[str, Any]]) -> dict[str, Any]:
        if not subset:
            return {"count": 0}
        rels = [float(r["reliability"]) for r in subset]
        return {
            "count": len(subset),
            "mean_reliability": float(np.mean(rels)),
            "median_reliability": float(np.median(rels)),
            "fraction_below_target": float(np.mean([r < target for r in rels])),
        }

    all_r = rows
    exposed = [r for r in rows if r.get("num_charging_visits", 0) > 0]
    below = [r for r in exposed if float(r.get("reliability", 0)) < target]
    return {
        "A_all_routes": stats(all_r),
        "B_charging_exposed": stats(exposed),
        "C_below_target_exposed": stats(below),
    }


def run_baseline_generation(
    project_root: Path | str,
    config: dict[str, Any],
    *,
    results_dir: Path | None = None,
) -> list[str]:
    root = Path(project_root).resolve()
    results_dir = results_dir or root / "results" / "baselines"
    results_dir.mkdir(parents=True, exist_ok=True)
    completed = list_completed_keys(results_dir)

    ds = config.get("dataset", {})
    dev_n = int(ds.get("development_parents_per_family", 2))
    Q = float(config.get("battery_capacity", 700))
    h = float(config.get("energy_consumption_rate", 1.0))
    method = config.get("baseline", {}).get("method", "CON")
    seed = config.get("baseline", {}).get("seed")

    saved: list[str] = []
    for inst in iter_instances(
        root,
        families=ds.get("families"),
        variants=ds.get("variants"),
        development_parents_per_family=dev_n,
        partition="development",
    ):
        key = result_key(inst.instance_key, inst.variant)
        out_path = results_dir / f"{key}.json"
        if key in completed and out_path.is_file():
            continue
        sol = generate_baseline(inst, Q, h, method=method, seed=seed, project_root=root)
        save_baseline_solution(out_path, sol)
        saved.append(key)
    return saved


def run_stochastic_audit(
    project_root: Path | str,
    config: dict[str, Any],
    *,
    baselines_dir: Path | None = None,
    raw_dir: Path | None = None,
    development_only: bool = True,
) -> list[str]:
    root = Path(project_root).resolve()
    baselines_dir = baselines_dir or root / "results" / "baselines"
    raw_dir = raw_dir or root / "results" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    completed = list_completed_keys(raw_dir, "*__audit.json")

    ds = config.get("dataset", {})
    dev_n = int(ds.get("development_parents_per_family", 2))
    Q = float(config.get("battery_capacity", 700))
    h = float(config.get("energy_consumption_rate", 1.0))
    sim_config = SimulatorConfig(Q, h)

    from star_evrp.results_io import load_json as lj
    from star_evrp.types import Route, RouteStop

    def sol_from_dict(data: dict) -> Solution:
        routes = []
        for r in data.get("routes", []):
            stops = [RouteStop(**s) for s in r.get("stops", [])]
            routes.append(
                Route(
                    route_id=r["route_id"],
                    customer_indices=r.get("customer_indices"),
                    stops=stops,
                )
            )
        return Solution(
            instance_key=data["instance_key"],
            variant=data["variant"],
            method=data.get("method", "CON"),
            battery_capacity=data.get("battery_capacity", Q),
            energy_consumption_rate=data.get("energy_consumption_rate", h),
            routes=routes,
            total_distance=data.get("total_distance"),
            feasible=data.get("feasible"),
            metadata=data.get("metadata", {}),
        )

    saved: list[str] = []
    for inst in iter_instances(
        root,
        families=ds.get("families"),
        variants=ds.get("variants"),
        development_parents_per_family=dev_n,
        partition="development" if development_only else None,
    ):
        bkey = result_key(inst.instance_key, inst.variant)
        audit_key = f"{bkey}__audit"
        if audit_key in completed:
            continue
        bpath = baselines_dir / f"{bkey}.json"
        if not bpath.is_file():
            continue
        sol = sol_from_dict(lj(bpath))
        payload = audit_instance(inst, sol, config, sim_config=sim_config)
        save_json(raw_dir / f"{audit_key}.json", payload)
        saved.append(audit_key)

    aggregate_csv(raw_dir, raw_dir / "aggregate_routes.csv")
    return saved


def aggregate_csv(raw_dir: Path, out_path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*__audit.json")):
        data = load_json(path)
        for r in data.get("routes", []):
            rows.append(r)
    if not rows:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({k for row in rows for k in row.keys()})
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def write_dataset_inventory(project_root: Path | str, config: dict[str, Any]) -> Path:
    root = Path(project_root).resolve()
    manifest_dir = root / "results" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    ds = config.get("dataset", {})
    dev_n = int(ds.get("development_parents_per_family", 2))
    manifest = build_partition_manifest(root, development_parents_per_family=dev_n)
    instances = load_all_instances(
        root,
        families=ds.get("families"),
        variants=ds.get("variants"),
        development_parents_per_family=dev_n,
    )
    manifest["inventory"] = inventory_summary(instances)
    manifest["provenance"] = environment_provenance(config)
    out = manifest_dir / "dataset_inventory.json"
    save_json(out, manifest)
    return out


def run_pilot(project_root: Path | str, config_path: Path | str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    config = load_experiment_config(config_path)
    t0 = time.perf_counter()
    write_dataset_inventory(root, config)
    baselines = run_baseline_generation(root, config)
    audits = run_stochastic_audit(root, config)
    return {
        "baselines_generated": baselines,
        "audits_completed": audits,
        "elapsed_seconds": time.perf_counter() - t0,
    }


# --- Table generation (Tables 1–6) ---


def _write_table_bundle(tables_dir: Path, name: str, headers: list[str], rows: list[list[Any]]) -> None:
    tables_dir.mkdir(parents=True, exist_ok=True)
    stem = tables_dir / name
    with (stem.with_suffix(".csv")).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(headers)
        w.writerows(rows)
    md_lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        md_lines.append("| " + " | ".join(str(c) for c in row) + " |")
    (stem.with_suffix(".md")).write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    tex = ["\\begin{tabular}{" + "l" * len(headers) + "}"]
    tex.append(" \\hline")
    tex.append(" " + " & ".join(headers) + " \\\\")
    tex.append(" \\hline")
    for row in rows:
        tex.append(" " + " & ".join(str(c) for c in row) + " \\\\")
    tex.append(" \\hline")
    tex.append("\\end{tabular}")
    (stem.with_suffix(".tex")).write_text("\n".join(tex) + "\n", encoding="utf-8")


def generate_all_tables(project_root: Path | str) -> Path:
    root = Path(project_root).resolve()
    tables_dir = root / "results" / "tables"
    manifest_path = root / "results" / "manifests" / "dataset_inventory.json"
    agg_path = root / "results" / "raw" / "aggregate_routes.csv"

    # Table 1 — dataset characteristics
    t1_rows: list[list[Any]] = []
    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        inv = manifest.get("inventory", {})
        t1_rows.append(["total_instances", inv.get("num_instances", "N/A")])
        for k, v in sorted((manifest.get("inventory") or {}).get("by_variant_family_partition", {}).items()):
            t1_rows.append([k, v])
    _write_table_bundle(tables_dir, "table01_dataset_characteristics", ["metric", "value"], t1_rows or [["N/A", "N/A"]])

    # Table 2 — baseline performance (from baselines JSON)
    t2_rows: list[list[Any]] = []
    for bp in sorted((root / "results" / "baselines").glob("*.json")):
        data = load_json(bp)
        meta = data.get("metadata", {})
        n_charges = sum(
            1
            for r in data.get("routes", [])
            for s in r.get("stops", [])
            if int(s.get("node_id", 0)) > 1000 and s.get("energy_charged")
        )
        t2_rows.append(
            [
                data.get("instance_key"),
                data.get("variant"),
                data.get("feasible"),
                len(data.get("routes", [])),
                n_charges,
                data.get("total_distance"),
                meta.get("runtime_seconds", "N/A"),
            ]
        )
    _write_table_bundle(
        tables_dir,
        "table02_deterministic_baseline",
        ["instance", "variant", "feasible", "vehicles", "charge_stops", "distance", "runtime_s"],
        t2_rows or [["N/A"] * 7],
    )

    # Table 3 — stochastic reliability summary (all / exposed / below-target)
    t3_rows: list[list[Any]] = []
    target = 0.95
    if agg_path.is_file():
        with agg_path.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if rows:
            rels = [float(r["reliability"]) for r in rows]
            exposed = [r for r in rows if int(float(r.get("num_charging_visits", 0))) > 0]
            below = [r for r in exposed if float(r["reliability"]) < target]
            ex_rels = [float(r["reliability"]) for r in exposed]
            t3_rows.extend(
                [
                    ["n_routes_all", len(rows)],
                    ["mean_reliability_all", f"{np.mean(rels):.4f}"],
                    ["median_reliability_all", f"{np.median(rels):.4f}"],
                    ["fraction_exposed", f"{len(exposed)/len(rows):.4f}"],
                    ["n_exposed", len(exposed)],
                    [
                        "mean_reliability_exposed",
                        f"{np.mean(ex_rels):.4f}" if ex_rels else "N/A",
                    ],
                    ["n_exposed_below_0.95", len(below)],
                    [
                        "fraction_exposed_below_0.95",
                        f"{(len(below)/len(exposed)):.4f}" if exposed else "N/A",
                    ],
                    [
                        "mean_p_late_customer",
                        f"{np.mean([float(r.get('p_late_customer', 0)) for r in rows]):.4f}",
                    ],
                    [
                        "mean_p_late_depot",
                        f"{np.mean([float(r.get('p_late_depot', 0)) for r in rows]):.4f}",
                    ],
                    [
                        "safe_reject_count",
                        int(sum(1 for r in rows if str(r.get("safe_reject")).lower() in {"true", "1"})),
                    ],
                ]
            )
    _write_table_bundle(tables_dir, "table03_stochastic_reliability", ["metric", "value"], t3_rows or [["N/A", "N/A"]])

    # Table 4 — by family / variant (all-route and charging-exposed)
    t4_rows: list[list[Any]] = []
    if agg_path.is_file():
        with agg_path.open("r", encoding="utf-8", newline="") as fh:
            from collections import defaultdict

            buckets_all: dict[tuple[str, str], list[float]] = defaultdict(list)
            buckets_ex: dict[tuple[str, str], list[float]] = defaultdict(list)
            for r in csv.DictReader(fh):
                key = (r["family"], r["variant"])
                rel = float(r["reliability"])
                buckets_all[key].append(rel)
                if int(float(r.get("num_charging_visits", 0))) > 0:
                    buckets_ex[key].append(rel)
            for key in sorted(buckets_all):
                fam, var = key
                all_r = buckets_all[key]
                ex_r = buckets_ex.get(key, [])
                below = sum(1 for x in ex_r if x < target)
                t4_rows.append(
                    [
                        fam,
                        var,
                        len(all_r),
                        f"{np.mean(all_r):.4f}",
                        len(ex_r),
                        f"{np.mean(ex_r):.4f}" if ex_r else "N/A",
                        below,
                        f"{(below/len(ex_r)):.4f}" if ex_r else "N/A",
                    ]
                )
    _write_table_bundle(
        tables_dir,
        "table04_reliability_by_family_variant",
        [
            "family",
            "variant",
            "n_all",
            "mean_rel_all",
            "n_exposed",
            "mean_rel_exposed",
            "n_exposed_below_0.95",
            "frac_exposed_below",
        ],
        t4_rows or [["N/A"] * 8],
    )

    # Table 5 — repair probe
    t5_rows: list[list[Any]] = []
    for rp in sorted((root / "results" / "raw").glob("*__repair_probe.json")):
        data = load_json(rp)
        s = data.get("summary", {})
        t5_rows.append(
            [
                data.get("instance_key"),
                s.get("unreliable_routes_examined"),
                s.get("routes_with_det_alternative"),
                s.get("candidates_improving_reliability"),
                s.get("best_reliability_gain"),
            ]
        )
    _write_table_bundle(
        tables_dir,
        "table05_repair_probe",
        ["instance", "examined", "with_alt", "improved", "best_gain"],
        t5_rows or [["N/A"] * 5],
    )

    # Table 6 — numerical / implementation validation
    pytest_status = "see_pytest_log"
    pytest_log = root / "results" / "reports" / "pytest_summary.txt"
    if pytest_log.is_file():
        raw = pytest_log.read_bytes()
        text = raw.decode("utf-8", errors="ignore")
        if "\x00" in text or raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            text = raw.decode("utf-16", errors="ignore")
        lines = [ln for ln in text.strip().splitlines() if ln.strip()]
        pytest_status = lines[-1][:120] if lines else "empty"
    n_baselines = len(list((root / "results" / "baselines").glob("*.json")))
    n_audits = len(list((root / "results" / "raw").glob("*__audit.json")))
    n_figs = len(list((root / "results" / "figures").glob("fig*.png")))
    t6_rows = [
        ["implementation_phase", "foundation"],
        ["development_baselines", f"{n_baselines}/24"],
        ["development_audits", f"{n_audits}/24"],
        ["aggregate_routes_csv", agg_path.is_file()],
        ["png_figures", n_figs],
        ["pytest_summary", pytest_status],
        ["battery_capacity_primary", 700],
        ["scenarios_per_route", 2000],
        ["baseline_method", "CON_deposited"],
    ]
    _write_table_bundle(tables_dir, "table06_validation", ["check", "status"], t6_rows)

    return tables_dir