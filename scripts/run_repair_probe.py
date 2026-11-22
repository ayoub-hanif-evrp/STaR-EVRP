#!/usr/bin/env python3
"""Run limited repair probe on development instances."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from star_evrp.cli import add_config_argument, add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.data_loader import iter_instances
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.experiment_runner import load_experiment_config
from star_evrp.repair_probe import RepairProbeReport, run_repair_probe, save_repair_probe
from star_evrp.results_io import load_json, result_key
from star_evrp.types import Route, RouteStop, Solution


def _load_solution(path: Path, Q: float, h: float) -> Solution:
    data = load_json(path)
    routes = []
    for r in data.get("routes", []):
        stops = [RouteStop(**s) for s in r.get("stops", [])]
        routes.append(
            Route(route_id=r["route_id"], customer_indices=r.get("customer_indices"), stops=stops)
        )
    return Solution(
        instance_key=data["instance_key"],
        variant=data["variant"],
        method=data.get("method", "CON"),
        battery_capacity=Q,
        energy_consumption_rate=h,
        routes=routes,
        metadata=data.get("metadata", {}),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    add_config_argument(parser)
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    config = load_experiment_config(args.config)
    ds = config.get("dataset", {})
    rp = config.get("repair_probe", {})
    Q = float(config.get("battery_capacity", 700))
    h = float(config.get("energy_consumption_rate", 1.0))
    sim = SimulatorConfig(Q, h)
    raw_dir = root / "results" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    target = float(config.get("target_route_reliability", 0.95))
    global_max = int(rp.get("max_routes", 40))
    examined_total = 0

    for inst in iter_instances(
        root,
        families=ds.get("families"),
        variants=ds.get("variants"),
        development_parents_per_family=int(ds.get("development_parents_per_family", 2)),
        partition="development",
    ):
        if examined_total >= global_max:
            break
        bkey = result_key(inst.instance_key, inst.variant)
        bpath = root / "results" / "baselines" / f"{bkey}.json"
        if not bpath.is_file():
            continue
        out = raw_dir / f"{bkey}__repair_probe.json"
        if out.is_file():
            continue
        # Prefer unreliable charging routes from audit when available.
        unreliable_ids = None
        audit_path = raw_dir / f"{bkey}__audit.json"
        if audit_path.is_file():
            audit = load_json(audit_path)
            unreliable_ids = [
                int(r["route_id"])
                for r in audit.get("routes", [])
                if int(r.get("num_charging_visits", 0)) > 0
                and float(r.get("reliability", 1.0)) < target
            ]
            if not unreliable_ids:
                empty = RepairProbeReport(
                    instance_key=inst.instance_key,
                    variant=inst.variant,
                    routes_examined=0,
                    summary={
                        "unreliable_routes_examined": 0,
                        "routes_with_det_alternative": 0,
                        "candidates_improving_reliability": 0,
                        "candidates_meeting_target": 0,
                        "best_reliability_gain": 0.0,
                        "note": "no_unreliable_charging_routes_in_audit",
                    },
                )
                save_repair_probe(out, empty)
                continue

        sol = _load_solution(bpath, Q, h)
        remaining = max(1, global_max - examined_total)
        report = run_repair_probe(
            inst,
            sol,
            sim,
            unreliable_route_ids=unreliable_ids,
            max_routes=min(int(rp.get("max_routes_per_instance", 8)), remaining),
            nearby_stations=int(rp.get("nearby_stations", 5)),
            diagnostic_scenarios=int(rp.get("diagnostic_scenarios", 500)),
            master_seed=int(rp.get("selection_seed", 0)),
            target_reliability=target,
        )
        save_repair_probe(out, report)
        examined_total += int(report.routes_examined)
        print(json.dumps({bkey: report.summary}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())