"""Phase-2 experiment orchestration (development only; holdout sealed)."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from star_evrp.baseline_optimizers import BASELINE_REGISTRY, BaselineReport
from star_evrp.budget import BudgetConfig, BudgetTracker
from star_evrp.data_loader import iter_instances, load_instance
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.results_io import load_json, result_key, save_json
from star_evrp.route_evaluator import RouteEvaluator
from star_evrp.search_common import SearchCandidate, meets_target_estimate
from star_evrp.star_optimizer import STaRConfig, STaRReport, optimize_route_star
from star_evrp.stochastic_simulator import simulate_route_stochastic
from star_evrp.types import Instance, NodeType, Route, RouteStop, Solution

PHASE2_METHODS = ("B0", "B1", "B2", "B3", "STaR_v1")

ABLATION_METHODS: dict[str, dict[str, Any]] = {
    "STaR_no_reject": {"use_certified_reject": False},
    "STaR_no_criticality": {"use_criticality": False},
    "STaR_no_progressive": {"use_progressive": False},
    "STaR_no_partial": {"allow_partial_charge": False},
    "STaR_single_edit": {"allow_multi_edit": False},
}

RESULT_FIELDS = [
    "instance_key",
    "variant",
    "family",
    "route_id",
    "method",
    "det_feasible",
    "reliability_opt",
    "e_completion_opt",
    "meets_target_opt",
    "reliability_val",
    "wilson_lo_val",
    "meets_target_val_ci",
    "e_completion_val",
    "n_scenarios_opt",
    "n_scenarios_val",
    "runtime_s",
    "candidates_examined",
    "screen_rejects",
    "budget_snapshot",
    "fingerprint",
    "notes",
]


def load_phase2_config(path: Path | str) -> dict[str, Any]:
    """Load YAML; merge ``inherits``; apply optional env budget overrides."""
    cfg_path = Path(path).resolve()
    with cfg_path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    parent = cfg.get("inherits")
    if parent:
        parent_path = Path(parent)
        if not parent_path.is_file():
            parent_path = cfg_path.parent / parent
        if not parent_path.is_file():
            parent_path = cfg_path.parent.parent / parent
        if parent_path.is_file():
            base = load_phase2_config(parent_path)
            merged = {**base, **{k: v for k, v in cfg.items() if k != "inherits"}}
            for key in ("budget", "star", "simulation", "outputs", "dataset"):
                if key in base and key in cfg and isinstance(base[key], dict) and isinstance(cfg[key], dict):
                    merged[key] = {**base[key], **cfg[key]}
            cfg = merged
    _apply_budget_env_overrides(cfg)
    return cfg


def _apply_budget_env_overrides(cfg: dict[str, Any]) -> None:
    budget = cfg.setdefault("budget", {})
    env_map = {
        "PHASE2_WALL_SECONDS": ("wall_seconds", float),
        "PHASE2_MAX_CANDIDATE_EVALS": ("max_candidate_evals", int),
        "PHASE2_VALIDATION_SCENARIOS": ("validation_scenarios", int),
        "PHASE2_PROGRESSIVE_STAGES": ("progressive_stages", lambda s: [int(x) for x in s.split(",")]),
    }
    for env_key, (field, conv) in env_map.items():
        raw = os.environ.get(env_key)
        if raw is not None:
            budget[field] = conv(raw)


def load_baseline_solution(path: Path | str, *, default_q: float = 700.0, default_h: float = 1.0) -> Solution:
    """Reconstruct ``Solution`` from Phase-1 baseline JSON (read-only)."""
    data = load_json(path)
    routes: list[Route] = []
    for r in data.get("routes", []):
        stops = [RouteStop(**s) for s in r.get("stops", [])]
        routes.append(
            Route(
                route_id=int(r["route_id"]),
                customer_indices=r.get("customer_indices"),
                stops=stops,
            )
        )
    return Solution(
        instance_key=data["instance_key"],
        variant=data["variant"],
        method=data.get("method", "CON"),
        battery_capacity=float(data.get("battery_capacity", default_q)),
        energy_consumption_rate=float(data.get("energy_consumption_rate", default_h)),
        routes=routes,
        total_distance=data.get("total_distance"),
        feasible=data.get("feasible"),
        metadata=data.get("metadata", {}),
    )


def _count_charging_visits(instance: Instance, route: Route) -> int:
    return sum(
        1 for s in route.stops or [] if instance.node(s.node_id).node_type == NodeType.STATION
    )


def select_eligible_routes(
    instance: Instance,
    solution: Solution,
    audit_row: dict[str, Any] | None = None,
    *,
    target: float = 0.95,
    require_below_target: bool = False,
) -> list[Route]:
    """Return charging-exposed routes (optionally below target per Phase-1 audit)."""
    audit_by_id: dict[int, dict[str, Any]] = {}
    if audit_row is not None:
        rid = int(audit_row.get("route_id", -1))
        audit_by_id[rid] = audit_row

    eligible: list[Route] = []
    for route in solution.routes:
        if not route.stops:
            continue
        row = audit_by_id.get(route.route_id)
        if row is not None:
            exposed = int(row.get("num_charging_visits", 0) or 0) > 0
            if not exposed:
                continue
            if require_below_target and float(row.get("reliability", 1.0)) >= target:
                continue
            eligible.append(route)
            continue
        if _count_charging_visits(instance, route) <= 0:
            continue
        if require_below_target:
            sim_cfg = SimulatorConfig(
                instance.ev_specs.battery_capacity,
                solution.energy_consumption_rate,
            )
            st = simulate_route_stochastic(
                instance,
                route,
                sim_cfg,
                num_scenarios=64,
                master_seed=0,
            )
            if st.reliability >= target:
                continue
        eligible.append(route)
    return eligible


def _reliability_bin(rel: float) -> str:
    if rel < 0.80:
        return "B1_<0.80"
    if rel < 0.90:
        return "B2_0.80-0.90"
    if rel < 0.95:
        return "B3_0.90-0.95"
    return "B4_>=0.95"


def build_balanced_panel(
    aggregate_csv: Path | str,
    *,
    n_per_family_variant: int = 6,
    seed: int = 20261122,
    target: float = 0.95,
    manifest_path: Path | str | None = None,
) -> list[tuple[str, str, int]]:
    """Stratified panel of (instance_key, variant, route_id) by reliability bin."""
    agg_path = Path(aggregate_csv)
    rows: list[dict[str, str]] = []
    if agg_path.is_file():
        with agg_path.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))

    pool = [
        r
        for r in rows
        if r.get("partition") == "development"
        and int(float(r.get("num_charging_visits", 0) or 0)) > 0
        and str(r.get("det_feasible", "True")).lower() in ("true", "1", "yes")
    ]
    rng = np.random.default_rng(seed)
    panel: list[tuple[str, str, int]] = []
    by_fv: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in pool:
        key = (r["instance_key"], r["variant"])
        by_fv.setdefault(key, []).append(r)

    for (_ik, _var), group in sorted(by_fv.items()):
        ik, var = group[0]["instance_key"], group[0]["variant"]
        _ = (ik, var)
        by_bin: dict[str, list[dict[str, str]]] = {}
        for r in group:
            rel = float(r.get("reliability", 0.0))
            by_bin.setdefault(_reliability_bin(rel), []).append(r)
        picked: list[dict[str, str]] = []
        bins = sorted(by_bin.keys())
        per_bin = max(1, n_per_family_variant // max(1, len(bins)))
        for b in bins:
            candidates = by_bin[b]
            rng.shuffle(candidates)
            picked.extend(candidates[:per_bin])
        if len(picked) < n_per_family_variant:
            rest = [r for r in group if r not in picked]
            rng.shuffle(rest)
            picked.extend(rest[: n_per_family_variant - len(picked)])
        else:
            picked = picked[:n_per_family_variant]
        for r in picked:
            panel.append((ik, var, int(r["route_id"])))

    if manifest_path:
        mp = Path(manifest_path)
        mp.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seed": seed,
            "n_per_family_variant": n_per_family_variant,
            "target_reliability": target,
            "source_csv": str(agg_path),
            "panel": [
                {"instance_key": a, "variant": b, "route_id": c} for a, b, c in panel
            ],
        }
        save_json(mp, payload)
    return panel


def _budget_from_config(cfg: dict[str, Any]) -> BudgetConfig:
    b = cfg.get("budget", {})
    stages = b.get("progressive_stages", [64, 256])
    return BudgetConfig(
        wall_seconds=float(b.get("wall_seconds", 25.0)),
        max_candidate_evals=int(b.get("max_candidate_evals", 50)),
        max_scenario_evals=int(b.get("max_scenario_evals", 500_000)),
        progressive_stages=tuple(int(x) for x in stages),
        validation_scenarios=int(b.get("validation_scenarios", 2000)),
    )


def _sim_config(cfg: dict[str, Any]) -> SimulatorConfig:
    Q = float(cfg.get("battery_capacity", 700.0))
    h = float(cfg.get("energy_consumption_rate", 1.0))
    return SimulatorConfig(Q, h)


def independent_validate(
    instance: Instance,
    selected_plan: Route,
    sim_config: SimulatorConfig,
    *,
    N_val: int,
    seed: int,
    split: str = "val",
    target: float = 0.95,
) -> dict[str, Any]:
    """Independent validation tape (``split='val'``)."""
    budget = BudgetTracker(BudgetConfig(max_scenario_evals=N_val + 1))
    evaluator = RouteEvaluator(instance, sim_config, seed, split, budget=budget)  # type: ignore[arg-type]
    ev = evaluator.evaluate_stochastic(selected_plan, N_val, use_cache=False)
    meets_ci = ev.wilson_ci_low >= target
    return {
        "reliability_val": ev.reliability,
        "wilson_lo_val": ev.wilson_ci_low,
        "meets_target_val_ci": meets_ci,
        "e_completion_val": ev.e_completion,
        "n_scenarios_val": ev.scenarios,
        "det_feasible": ev.det_feasible,
    }


def run_method_on_route(
    method_name: str,
    instance: Instance,
    route: Route,
    sim_config: SimulatorConfig,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Run one method on one fixed-customer route; includes val split."""
    target = float(cfg.get("target_route_reliability", 0.95))
    sim = cfg.get("simulation", {})
    master_seed = int(sim.get("master_seed", sim.get("scenario_seed", 20261122)))
    N_val = int(sim.get("N_val", cfg.get("budget", {}).get("validation_scenarios", 2000)))
    budget_cfg = _budget_from_config(cfg)
    star_section = cfg.get("star", {})
    nearby = int(star_section.get("nearby_stations", 5))
    t0 = time.perf_counter()

    screen_rejects = 0
    candidates_examined = 0
    budget_snapshot: dict[str, Any] = {}
    incumbent: SearchCandidate | None = None
    notes = ""

    if method_name in BASELINE_REGISTRY:
        fn = BASELINE_REGISTRY[method_name]
        kwargs: dict[str, Any] = {
            "target": target,
            "master_seed": master_seed,
            "budget_cfg": budget_cfg,
        }
        if method_name != "B0":
            kwargs["nearby"] = nearby
        rep: BaselineReport = fn(instance, route, sim_config, **kwargs)
        incumbent = rep.incumbent
        candidates_examined = rep.candidates_examined
        budget_snapshot = rep.budget
        notes = "" if incumbent and incumbent.meets_target else "below_target_incumbent"
    elif method_name == "STaR_v1" or method_name in ABLATION_METHODS:
        flags = {**star_section, **ABLATION_METHODS.get(method_name, {})}
        star_cfg = STaRConfig(
            target_reliability=target,
            master_seed=master_seed,
            use_certified_reject=bool(flags.get("use_certified_reject", True)),
            use_criticality=bool(flags.get("use_criticality", True)),
            use_progressive=bool(flags.get("use_progressive", True)),
            allow_partial_charge=bool(flags.get("allow_partial_charge", True)),
            allow_multi_edit=bool(flags.get("allow_multi_edit", True)),
            nearby_stations=nearby,
            budget=budget_cfg,
        )
        rep_star: STaRReport = optimize_route_star(instance, route, sim_config, star_cfg)
        incumbent = rep_star.incumbent
        candidates_examined = rep_star.candidates_examined
        screen_rejects = rep_star.screen_rejects
        budget_snapshot = rep_star.budget
        notes = rep_star.notes
    else:
        raise ValueError(f"Unknown method: {method_name}")

    runtime_s = time.perf_counter() - t0
    if incumbent is None:
        det_ok = simulate_route_fixed(instance, route, sim_config).feasible
        val = independent_validate(
            instance, route, sim_config, N_val=N_val, seed=master_seed + 1, target=target
        )
        return _result_row(
            instance,
            route.route_id,
            method_name,
            det_feasible=det_ok,
            reliability_opt=0.0,
            e_completion_opt=0.0,
            meets_target_opt=False,
            val=val,
            n_scenarios_opt=0,
            runtime_s=runtime_s,
            candidates_examined=candidates_examined,
            screen_rejects=screen_rejects,
            budget_snapshot=budget_snapshot,
            fingerprint="",
            notes="no_incumbent",
        )

    val = independent_validate(
        instance,
        incumbent.route,
        sim_config,
        N_val=N_val,
        seed=master_seed + 1,
        target=target,
    )
    return _result_row(
        instance,
        route.route_id,
        method_name,
        det_feasible=incumbent.det_feasible,
        reliability_opt=incumbent.reliability,
        e_completion_opt=incumbent.e_completion,
        meets_target_opt=bool(incumbent.meets_target or meets_target_estimate(incumbent.reliability, target)),
        val=val,
        n_scenarios_opt=incumbent.scenarios,
        runtime_s=runtime_s,
        candidates_examined=candidates_examined,
        screen_rejects=screen_rejects,
        budget_snapshot=budget_snapshot,
        fingerprint=incumbent.fingerprint,
        notes=notes,
    )


def _result_row(
    instance: Instance,
    route_id: int,
    method: str,
    *,
    det_feasible: bool,
    reliability_opt: float,
    e_completion_opt: float,
    meets_target_opt: bool,
    val: dict[str, Any],
    n_scenarios_opt: int,
    runtime_s: float,
    candidates_examined: int,
    screen_rejects: int,
    budget_snapshot: dict[str, Any],
    fingerprint: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "instance_key": instance.instance_key,
        "variant": instance.variant,
        "family": instance.family,
        "route_id": route_id,
        "method": method,
        "det_feasible": det_feasible,
        "reliability_opt": reliability_opt,
        "e_completion_opt": e_completion_opt,
        "meets_target_opt": meets_target_opt,
        "reliability_val": val["reliability_val"],
        "wilson_lo_val": val["wilson_lo_val"],
        "meets_target_val_ci": val["meets_target_val_ci"],
        "e_completion_val": val["e_completion_val"],
        "n_scenarios_opt": n_scenarios_opt,
        "n_scenarios_val": val["n_scenarios_val"],
        "runtime_s": runtime_s,
        "candidates_examined": candidates_examined,
        "screen_rejects": screen_rejects,
        "budget_snapshot": budget_snapshot,
        "fingerprint": fingerprint,
        "notes": notes,
    }


def _phase2_result_filename(instance_key: str, variant: str, route_id: int, method: str) -> str:
    safe_method = method.replace("/", "_")
    return f"{result_key(instance_key, variant)}__r{route_id}__{safe_method}"


def _save_result(raw_dir: Path, row: dict[str, Any]) -> Path:
    stem = _phase2_result_filename(
        row["instance_key"], row["variant"], int(row["route_id"]), row["method"]
    )
    path = raw_dir / f"{stem}.json"
    save_json(path, row)
    return path


def _result_exists(raw_dir: Path, instance_key: str, variant: str, route_id: int, method: str) -> bool:
  stem = _phase2_result_filename(instance_key, variant, route_id, method)
  return (raw_dir / f"{stem}.json").is_file()


def _audit_rows_for(project_root: Path) -> dict[tuple[str, str, int], dict[str, Any]]:
    index: dict[tuple[str, str, int], dict[str, Any]] = {}
    agg = project_root / "results" / "raw" / "aggregate_routes.csv"
    if not agg.is_file():
        return index
    with agg.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("partition") != "development":
                continue
            key = (row["instance_key"], row["variant"], int(row["route_id"]))
            index[key] = row
    return index


def _resolve_work_items(
    project_root: Path,
    cfg: dict[str, Any],
    *,
    panel_only: bool,
    max_routes: int | None = None,
) -> list[tuple[str, str, int]]:
    root = Path(project_root)
    manifest = root / "results" / "phase2" / "manifests" / "dev_panel.json"
    agg = root / "results" / "raw" / "aggregate_routes.csv"
    if panel_only and manifest.is_file():
        data = load_json(manifest)
        items = [
            (e["instance_key"], e["variant"], int(e["route_id"])) for e in data.get("panel", [])
        ]
    else:
        if not manifest.is_file():
            ds = cfg.get("dataset", {})
            seed = int(cfg.get("simulation", {}).get("master_seed", 20261122))
            build_balanced_panel(
                agg,
                n_per_family_variant=int(ds.get("panel_per_family_variant", 6)),
                seed=seed,
                manifest_path=manifest,
            )
        data = load_json(manifest)
        items = [
            (e["instance_key"], e["variant"], int(e["route_id"])) for e in data.get("panel", [])
        ]
        if not panel_only:
            items = []
            index = _audit_rows_for(root)
            for key, row in sorted(index.items()):
                if int(row.get("num_charging_visits", 0) or 0) > 0:
                    items.append(key)
    if max_routes is not None:
        items = items[: max_routes]
    return items


def _run_batch(
    project_root: Path,
    cfg: dict[str, Any],
  *,
    methods: list[str],
    raw_subdir: str,
    panel_only: bool,
    max_routes: int | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    raw_dir = root / raw_subdir
    raw_dir.mkdir(parents=True, exist_ok=True)
    baselines_dir = root / "results" / "baselines"
    sim_config = _sim_config(cfg)
    items = _resolve_work_items(root, cfg, panel_only=panel_only, max_routes=max_routes)
    audit_index = _audit_rows_for(root)
    completed = 0
    skipped = 0
    errors: list[str] = []

    for instance_key, variant, route_id in items:
        bpath = baselines_dir / f"{result_key(instance_key, variant)}.json"
        if not bpath.is_file():
            errors.append(f"missing baseline {bpath.name}")
            continue
        try:
            inst = load_instance(root, instance_key, variant)
        except Exception as exc:
            errors.append(f"load_instance {instance_key}/{variant}: {exc}")
            continue
        sol = load_baseline_solution(bpath, default_q=sim_config.battery_capacity, default_h=sim_config.energy_consumption_rate)
        audit_row = audit_index.get((instance_key, variant, route_id))
        routes = select_eligible_routes(inst, sol, audit_row)
        route = next((r for r in routes if r.route_id == route_id), None)
        if route is None:
            route = next((r for r in sol.routes if r.route_id == route_id), None)
        if route is None:
            errors.append(f"route {route_id} missing for {instance_key}/{variant}")
            continue

        for method in methods:
            if _result_exists(raw_dir, instance_key, variant, route_id, method):
                skipped += 1
                continue
            try:
                row = run_method_on_route(method, inst, route, sim_config, cfg)
                _save_result(raw_dir, row)
                completed += 1
            except Exception as exc:
                errors.append(f"{instance_key}/{variant}/r{route_id}/{method}: {exc}")

    summary = {
        "methods": methods,
        "work_items": len(items),
        "completed": completed,
        "skipped_resume": skipped,
        "errors": errors,
        "raw_dir": str(raw_dir),
    }
    save_json(raw_dir.parent.parent / "reports" / f"batch_{Path(raw_subdir).name}.json", summary)
    return summary


def run_smoke(project_root: Path | str, config_path: Path | str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    cfg = load_phase2_config(config_path)
    manifest = root / "results" / "phase2" / "manifests" / "dev_panel.json"
    if not manifest.is_file():
        build_balanced_panel(
            root / "results" / "raw" / "aggregate_routes.csv",
            seed=int(cfg.get("simulation", {}).get("master_seed", 20261122)),
            manifest_path=manifest,
        )
    smoke_cfg = cfg.get("smoke", {})
    max_routes = int(smoke_cfg.get("max_routes", 2))
    out_rel = cfg.get("outputs", {}).get("smoke", "results/phase2/raw/smoke")
    methods = list(cfg.get("methods", PHASE2_METHODS))
    summary = _run_batch(
        root,
        cfg,
        methods=methods,
        raw_subdir=out_rel,
        panel_only=True,
        max_routes=max_routes,
    )
    summary["mode"] = "smoke"
    return summary


def run_development(
    project_root: Path | str,
    config_path: Path | str,
    *,
    panel_only: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    cfg = load_phase2_config(config_path)
    agg = root / "results" / "raw" / "aggregate_routes.csv"
    manifest = root / "results" / "phase2" / "manifests" / "dev_panel.json"
    if not manifest.is_file():
        ds = cfg.get("dataset", {})
        build_balanced_panel(
            agg,
            n_per_family_variant=int(ds.get("panel_per_family_variant", 6)),
            seed=int(cfg.get("simulation", {}).get("master_seed", 20261122)),
            manifest_path=manifest,
        )
    out_rel = cfg.get("outputs", {}).get("raw", "results/phase2/raw/dev")
    baselines = list(cfg.get("baselines", ["B0", "B1", "B2", "B3"]))
    methods = baselines + ["STaR_v1"]
    summary = _run_batch(
        root,
        cfg,
        methods=methods,
        raw_subdir=out_rel,
        panel_only=panel_only,
    )
    summary["mode"] = "development"
    summary["panel_only"] = panel_only
    return summary


def run_ablations(project_root: Path | str, config_path: Path | str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    cfg = load_phase2_config(config_path)
    methods = [a.get("name") for a in cfg.get("ablations", []) if a.get("name")]
    if not methods:
        methods = ["STaR_v1", *ABLATION_METHODS.keys()]
    out_rel = cfg.get("outputs", {}).get("raw", "results/phase2/raw/ablation")
    summary = _run_batch(
        root,
        cfg,
        methods=methods,
        raw_subdir=out_rel,
        panel_only=True,
    )
    summary["mode"] = "ablation"
    return summary


def run_d1_crosswalk(
    project_root: Path | str,
    config_path: Path | str,
    *,
    out_path: Path | str | None = None,
) -> Path:
    """Re-evaluate Phase-1 CON plans (development panel); write crosswalk CSV."""
    root = Path(project_root).resolve()
    cfg = load_phase2_config(config_path)
    sim_config = _sim_config(cfg)
    sim = cfg.get("simulation", {})
    master_seed = int(sim.get("master_seed", 20261122))
    n_scen = int(sim.get("scenarios_per_route", cfg.get("budget", {}).get("validation_scenarios", 2000)))
    target = float(cfg.get("target_route_reliability", 0.95))
    items = _resolve_work_items(root, cfg, panel_only=True)
    audit_index = _audit_rows_for(root)
    out = Path(out_path or root / "results" / "phase2" / "raw" / "d1_crosswalk.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for instance_key, variant, route_id in items:
        bpath = root / "results" / "baselines" / f"{result_key(instance_key, variant)}.json"
        if not bpath.is_file():
            continue
        inst = load_instance(root, instance_key, variant)
        sol = load_baseline_solution(bpath)
        route = next((r for r in sol.routes if r.route_id == route_id), None)
        if route is None:
            continue
        old = audit_index.get((instance_key, variant, route_id), {})
        new = simulate_route_stochastic(
            inst,
            route,
            sim_config,
            num_scenarios=n_scen,
            master_seed=master_seed,
        )
        rows.append(
            {
                "instance_key": instance_key,
                "variant": variant,
                "route_id": route_id,
                "old_reliability": old.get("reliability"),
                "new_reliability": new.reliability,
                "old_e_completion": old.get("e_completion"),
                "new_e_completion": new.e_completion,
                "target": target,
                "n_scenarios": n_scen,
            }
        )

    fieldnames = list(rows[0].keys()) if rows else [
        "instance_key", "variant", "route_id", "old_reliability", "new_reliability",
        "old_e_completion", "new_e_completion", "target", "n_scenarios",
    ]
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    return out


def config_fingerprint(cfg: dict[str, Any]) -> str:
    payload = json.dumps(cfg, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]