"""Independently rerun count-budget searches and the historical D1 crosswalk."""

import argparse
import csv
import math
from pathlib import Path

from star_evrp.budget import BudgetConfig
from star_evrp.charge_plan import ChargePlan
from star_evrp.competitive_search import METHODS, optimize
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.experiment_phase25 import _load_case, _profile_path, _read_batch, prepare_run
from star_evrp.results_io import save_json
from star_evrp.stochastic_simulator import simulate_route_stochastic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/phase25"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    cfg, development = prepare_run(root, root / "configs/phase25.yaml", output)
    physics = SimulatorConfig(cfg["battery_capacity"], cfg["energy_consumption_rate"])
    with (root / "results/phase2/raw/d1_crosswalk.csv").open(encoding="utf-8", newline="") as handle:
        crosswalk = {(row["instance_key"], row["variant"], int(row["route_id"])): row
                     for row in csv.DictReader(handle)}
    crosswalk_checked = 0
    checked = 0
    for (parent, variant), inventory in development.items():
        instance, routes = _load_case(root, parent, variant, inventory, physics)
        expected = {(route.route_id, method) for route in routes for method in METHODS}
        indexed = {route.route_id: route for route in routes}
        for profile, limits in cfg["profiles"].items():
            if limits["wall_seconds"] < 1:
                continue
            rows = _read_batch(_profile_path(output, profile, parent, variant), expected)
            for row in rows:
                route = indexed[row["route_id"]]
                new = optimize(instance, physics, route, row["method"], BudgetConfig(**limits),
                               seed=cfg["seed"], samples=cfg["opt_scenarios"], target=cfg["target"],
                               nearby=cfg["nearby_stations"])
                if ChargePlan.from_route(instance, new.route).fingerprint() != row["fingerprint"]:
                    raise ValueError("Selected plan did not replay")
                if list(new.score) != row["search_score"] or any(
                    new.budget[field] != row["budget"][field]
                    for field in ("scenarios_evaluated", "candidates_evaluated", "generated")
                ):
                    raise ValueError("Score or budget counters did not replay")
                checked += 1
        for route in routes:
            item = crosswalk.get((parent, variant, route.route_id))
            if item:
                new = simulate_route_stochastic(
                    instance, route, physics, master_seed=cfg["seed"], num_scenarios=int(item["n_scenarios"]),
                )
                if new.reliability != float(item["new_reliability"]) or not math.isclose(
                    new.e_completion, float(item["new_e_completion"]), rel_tol=0, abs_tol=1e-8,
                ):
                    raise ValueError(f"D1 crosswalk mismatch for {parent}/{variant}/{route.route_id}")
                crosswalk_checked += 1
        print(f"{parent}/{variant}: replayed", flush=True)
    if crosswalk_checked != len(crosswalk):
        raise ValueError("Incomplete D1 replay")
    summary = {"search_records": checked, "d1_crosswalk_routes": crosswalk_checked,
               "wall_profile": "not replayed as exact search; all its final plans are validated separately"}
    save_json(output / "search_replay.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
