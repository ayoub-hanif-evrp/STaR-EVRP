"""Deterministic CON/HC baselines via deposited solver + explicit route expansion."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from star_evrp.data_loader import discover_dataset_root
from star_evrp.deterministic_simulator import (
    SimulatorConfig,
    simulate_route_baseline_expansion,
)
from star_evrp.route_validator import validate_solution
from star_evrp.statistics import stable_seed
from star_evrp.types import Instance, NodeType, NUM_TOL, Route, RouteStop, Solution

_DEPOSITED_MODULE = None


def _dataset_code_dir(project_root: Path | str) -> Path:
    root = Path(project_root).resolve()
    ds = discover_dataset_root(root / "dataset")
    return ds / "code"


def _import_deposited(project_root: Path | str):
    global _DEPOSITED_MODULE
    if _DEPOSITED_MODULE is not None:
        return _DEPOSITED_MODULE
    code_dir = str(_dataset_code_dir(project_root))
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    import evrptw_solvers  # type: ignore

    _DEPOSITED_MODULE = evrptw_solvers
    return evrptw_solvers


def _hill_climb_routes(dep, instance: dict, Q: float, h: float, max_iterations: int, seed: int):
    """Mirror deposited HC but return final route list (upstream API returns stats only)."""
    rng = np.random.default_rng(seed)
    routes, _ev0 = dep.constructive_solve_with_routes(instance, Q, h)
    ev_cur = dep.evaluate_routes(routes, instance, Q, h)
    if not ev_cur["feasible"]:
        return routes
    current_routes = dep._deep_copy_routes(routes)
    current_cost = ev_cur["total_distance"]
    best_routes = dep._deep_copy_routes(routes)
    best_cost = current_cost
    for _ in range(max_iterations):
        trial, _rec = dep._random_neighbor_move(current_routes, rng)
        if trial is None:
            continue
        ev2 = dep.evaluate_routes(trial, instance, Q, h)
        if not ev2["feasible"]:
            continue
        if ev2["total_distance"] < current_cost:
            current_routes = trial
            current_cost = ev2["total_distance"]
            if current_cost < best_cost:
                best_cost = current_cost
                best_routes = dep._deep_copy_routes(trial)
    return best_routes


def instance_to_deposited(instance: Instance) -> dict[str, Any]:
    """Convert :class:`Instance` to deposited ``prepare_instance`` dict layout."""
    station_indices = np.asarray(
        [instance.node_id_to_index[s] for s in instance.station_node_ids],
        dtype=np.int64,
    )
    n_c = instance.num_customers
    charging_rate = np.asarray(
        [instance.charging_rate(s) for s in instance.station_node_ids],
        dtype=np.float64,
    )
    return {
        "fleet_size": instance.fleet_size,
        "load_capacity": float(instance.load_capacity),
        "num_customers": n_c,
        "depot_closing_time": float(instance.depot_closing_time),
        "distance_matrix": instance.distance_matrix,
        "customer_indices": np.arange(1, 1 + n_c),
        "station_indices": station_indices,
        "customer_ready_time": np.asarray(
            [instance.node(cid).ready_time for cid in instance.customer_node_ids],
            dtype=np.float64,
        ),
        "customer_due_date": np.asarray(
            [instance.node(cid).due_date for cid in instance.customer_node_ids],
            dtype=np.float64,
        ),
        "customer_demand": np.asarray(
            [instance.node(cid).demand for cid in instance.customer_node_ids],
            dtype=np.float64,
        ),
        "customer_service_time": np.asarray(
            [instance.node(cid).service_time for cid in instance.customer_node_ids],
            dtype=np.float64,
        ),
        "charging_rate": charging_rate,
        "station_to_depot_dist": instance.distance_matrix[station_indices, 0],
    }


def expand_customer_route_to_explicit(
    instance: Instance,
    customer_locals: list[int],
    Q: float,
    h: float,
    route_id: int,
) -> Route:
    """Expand CON customer sequence to explicit depot–stops–depot plan."""
    config = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=h)
    trace = simulate_route_baseline_expansion(
        instance,
        customer_locals,
        config,
        route_id=route_id,
    )
    stops: list[RouteStop] = []
    for ts in trace.stops:
        node = instance.node(ts.node_id)
        if node.node_type == NodeType.STATION and ts.energy_charged > NUM_TOL:
            ec: float | None = float(ts.energy_charged)
        else:
            ec = None
        stops.append(RouteStop(node_id=ts.node_id, energy_charged=ec, wait_extra=0.0))
    return Route(
        route_id=route_id,
        customer_indices=list(customer_locals),
        stops=stops,
    )


def solution_metadata_hashes(instance: Instance) -> dict[str, str]:
    return {
        "instance_file_sha256": instance.instance_file_sha256,
        "stations_file_sha256": instance.stations_file_sha256,
    }


def generate_baseline(
    instance: Instance,
    Q: float,
    h: float,
    method: str = "CON",
    *,
    seed: int | None = None,
    project_root: Path | str | None = None,
    hc_iterations: int = 36,
) -> Solution:
    """Run deposited CON or HC and return explicit-stop ``Solution``."""
    t0 = time.perf_counter()
    root = Path(project_root) if project_root else Path.cwd()
    dep = _import_deposited(root)
    dep_inst = instance_to_deposited(instance)

    method_norm = method.upper().replace("_DEPOSITED", "")
    deposited_method = f"{method_norm}_deposited" if method.upper().endswith("_DEPOSITED") else method_norm

    if method_norm == "CON":
        routes_local, _eval = dep.constructive_solve_with_routes(dep_inst, Q, h)
        label = "CON_deposited" if "deposited" in method.lower() else "CON"
    elif method_norm == "HC":
        use_seed = stable_seed(seed if seed is not None else 0, instance.instance_key, instance.variant)
        routes_local = _hill_climb_routes(dep, dep_inst, Q, h, hc_iterations, use_seed)
        label = "HC_deposited"
    else:
        raise ValueError(f"Unknown baseline method: {method!r}")

    routes: list[Route] = []
    total_distance = 0.0
    for rid, locals_ in enumerate(routes_local):
        route = expand_customer_route_to_explicit(instance, list(locals_), Q, h, rid)
        routes.append(route)
        cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=h)
        tr = simulate_route_baseline_expansion(instance, list(locals_), cfg, route_id=rid)
        if tr.feasible:
            total_distance += tr.total_distance

    runtime_s = time.perf_counter() - t0
    sol = Solution(
        instance_key=instance.instance_key,
        variant=instance.variant,
        method=label,
        battery_capacity=Q,
        energy_consumption_rate=h,
        routes=routes,
        total_distance=round(total_distance, 4),
        feasible=None,
        metadata={
            "runtime_seconds": runtime_s,
            "seed": seed,
            "method_requested": method,
            "deposited_method": deposited_method,
            **solution_metadata_hashes(instance),
            "num_routes": len(routes),
        },
    )
    report = validate_solution(instance, sol, config=SimulatorConfig(Q, h))
    sol.feasible = report.feasible
    sol.metadata["validation_feasible"] = report.feasible
    sol.metadata["validation_issues"] = len(report.issues)
    return sol


def save_baseline_solution(path: Path | str, solution: Solution) -> None:
    from star_evrp.results_io import save_json

    save_json(path, solution)