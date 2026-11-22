"""Versioned development-only Phase 2.5 experiments and replay."""

from __future__ import annotations

import hashlib
import importlib.metadata
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np
import yaml

from star_evrp.budget import BudgetConfig
from star_evrp.charge_plan import ChargePlan
from star_evrp.competitive_search import METHODS, optimize
from star_evrp.data_loader import load_instance, sha256_file
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.experiment_phase2 import load_baseline_solution
from star_evrp.results_io import load_json, save_json
from star_evrp.route_evaluator import RouteEvaluator
from star_evrp.route_validator import validate_repair, validate_solution
from star_evrp.statistics import wilson_ci, wilson_lower
from star_evrp.stochastic_simulator import evaluate_route_with_waits
from star_evrp.types import Route, RouteStop


def inputs(root: Path):
    inventory = load_json(root / "results/manifests/dataset_inventory.json")["instances"]
    split = yaml.safe_load((root / "configs/experiment_splits.yaml").read_text(encoding="utf-8"))
    allowed = {(parent, variant) for parents in split["development_parents"].values()
               for parent in parents for variant in ("A", "B")}
    development = {(item["instance_key"], item["variant"]): item
                   for item in inventory if item["partition"] == "development"}
    if len(allowed) != 24 or development.keys() != allowed:
        raise ValueError("Development allowlist differs from frozen inventory")
    return development


def prepare_run(root, config_path, output):
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    development = inputs(root)
    files = [
        config_path, root / "configs/experiment_splits.yaml",
        root / "results/phase2/manifests/dev_panel.json",
        root / "scripts/run_phase25.py",
        *sorted((root / "src/star_evrp").glob("*.py")),
        *(root / f"results/baselines/{parent}__{variant}.json" for parent, variant in sorted(development)),
    ]
    manifest = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "source_note": "Working-tree source identified by hashes, not by HEAD alone",
        "file_sha256": {str(path.relative_to(root)).replace("\\", "/"): sha256_file(path) for path in files},
        "development_inventory": list(development.values()),
        "config": cfg,
        "methods": list(METHODS),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "pyyaml", "matplotlib")},
    }
    path = output / "manifest.json"
    if path.exists():
        if load_json(path) != manifest:
            raise ValueError("Resume manifest mismatch; choose a fresh output directory")
    else:
        save_json(path, manifest)
    return cfg, development


def _load_case(root, parent, variant, inventory, physics):
    instance = load_instance(root, parent, variant)
    if (instance.instance_file_sha256, instance.stations_file_sha256) != (
        inventory["instance_sha256"], inventory["stations_sha256"],
    ):
        raise ValueError("Benchmark file hash mismatch")
    solution = load_baseline_solution(root / f"results/baselines/{parent}__{variant}.json")
    if (
        solution.method != "CON" or solution.battery_capacity != physics.battery_capacity
        or solution.energy_consumption_rate != physics.energy_consumption_rate
        or solution.metadata["instance_file_sha256"] != instance.instance_file_sha256
        or solution.metadata["stations_file_sha256"] != instance.stations_file_sha256
        or not validate_solution(instance, solution, config=physics).feasible
    ):
        raise ValueError("Invalid starting CON solution")
    return instance, [route for route in solution.routes if any(
        stop.node_id in instance.station_attributes for stop in route.stops
    )]


def _validate(instance, original, selected, physics, cfg, *, scalar=False):
    trace = validate_repair(instance, original, selected, physics)
    evaluator = RouteEvaluator(instance, physics, cfg["seed"], "val")
    count = cfg["validation_scenarios"]
    entry = evaluator.prepare(selected)
    if not evaluator.extend(selected, entry, count):
        raise ValueError("Incomplete validation")
    if scalar:
        tape = evaluator._ensure_z_tape(selected, count, len(entry.timing.mus))
        for index in (0, count // 2, count - 1):
            wait = entry.timing.waits(tape[index:index + 1])[0]
            ref = evaluate_route_with_waits(
                instance, selected, wait, Q=physics.battery_capacity, h=physics.energy_consumption_rate,
                enforce_station_time_windows=physics.enforce_station_time_windows,
            )
            if ref.success != entry.success[index] or not np.isclose(
                ref.completion, entry.completion[index], rtol=0.0, atol=1e-8,
            ):
                raise ValueError("Reference timing mismatch")
    wins = int(entry.success.sum())
    lower = wilson_lower(wins, count)
    return {
        "successes": wins, "n": count, "reliability": wins / count, "wilson95_lower": lower,
        "wilson95_two_sided": list(wilson_ci(wins, count)), "attained": lower >= cfg["target"],
        "mean_completion": float(entry.completion.mean()), "p95_completion": float(np.quantile(entry.completion, 0.95)),
        "zero_wait_completion": trace.end_clock, "distance": trace.total_distance,
        "completion_quantiles": np.quantile(entry.completion, np.linspace(0, 1, 21)).tolist(),
        "charging": [
            {"stop": index, "station": stop.node_id, "energy": stop.energy_charged,
             "arrival": stop.arrival_time, "departure": stop.departure_time,
             "charge_duration": stop.energy_charged / instance.charging_rate(stop.node_id)}
            for index, stop in enumerate(trace.stops) if stop.node_id in instance.station_attributes
        ],
        "timeline": [stop.departure_time for stop in trace.stops],
    }


def _profile_path(output, profile, parent, variant):
    return output / "raw" / profile / f"{parent}__{variant}.json"


def _identity(rows):
    return {(item["route_id"], item["method"]) for item in rows}


def _read_batch(path, expected):
    payload = load_json(path)
    rows = payload["rows"]
    digest = hashlib.sha256(__import__("json").dumps(rows, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if payload["rows_sha256"] != digest or _identity(rows) != expected or len(rows) != len(expected):
        raise ValueError(f"Invalid or incomplete batch: {path}")
    return rows


def run(root: Path, config_path: Path, output: Path, *, verify: bool = False):
    cfg, development = prepare_run(root, config_path, output)
    physics = SimulatorConfig(cfg["battery_capacity"], cfg["energy_consumption_rate"])
    panel = {(row["instance_key"], row["variant"], row["route_id"]) for row in
             load_json(root / "results/phase2/manifests/dev_panel.json")["panel"]}
    validated = 0
    for (parent, variant), inventory in development.items():
        instance, routes = _load_case(root, parent, variant, inventory, physics)
        expected = {(route.route_id, method) for route in routes for method in METHODS}
        original = {route.route_id: route for route in routes}
        for profile, limits in cfg["profiles"].items():
            path = _profile_path(output, profile, parent, variant)
            if path.exists() or verify:
                batch = _read_batch(path, expected)
                if verify:
                    for row in batch:
                        source = original[row["route_id"]]
                        route = Route(row["route_id"], None, [RouteStop(**stop) for stop in row["stops"]])
                        if ChargePlan.from_route(instance, route).fingerprint() != row["fingerprint"]:
                            raise ValueError("Plan fingerprint mismatch")
                        if _validate(instance, source, route, physics, cfg, scalar=True) != row["validation"]:
                            raise ValueError("Validation replay mismatch")
                        validated += 1
                continue
            budget = BudgetConfig(**limits)
            rows = []
            for route in routes:
                for method in METHODS:
                    search = optimize(
                        instance, physics, route, method, budget, seed=cfg["seed"], samples=cfg["opt_scenarios"],
                        target=cfg["target"], nearby=cfg["nearby_stations"],
                    )
                    plan = ChargePlan.from_route(instance, search.route)
                    selected = plan.to_route(instance, route.route_id)
                    validation = _validate(instance, route, selected, physics, cfg)
                    rows.append({
                        "parent": parent, "variant": variant, "family": instance.family, "profile": profile,
                        "route_id": route.route_id, "panel": (parent, variant, route.route_id) in panel,
                        "method": method, "search_score": list(search.score), "budget": search.budget,
                        "selected_moves": search.moves, "screen_rejections": search.screen_rejections,
                        "prefix_rejections": search.prefix_rejections, "time_to_opt_target": search.target_time,
                        "stops": [asdict(stop) for stop in selected.stops], "fingerprint": plan.fingerprint(),
                        "validation": validation,
                    })
            digest = hashlib.sha256(__import__("json").dumps(rows, sort_keys=True, allow_nan=False).encode()).hexdigest()
            save_json(path, {"rows_sha256": digest, "rows": rows})
        print(f"{parent}/{variant}: {len(routes)} routes", flush=True)
    if verify:
        save_json(output / "replay.json", {"validated_records": validated, "scalar_scenarios_per_record": 3})
        print(f"Revalidated {validated} records", flush=True)
