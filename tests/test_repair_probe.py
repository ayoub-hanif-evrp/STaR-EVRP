"""Repair-probe candidate feasibility and customer-order preservation."""

from __future__ import annotations

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.repair_probe import _customer_sequence, _replace_station_visit
from star_evrp.types import Route, RouteStop, Solution

from tests.conftest import make_synthetic_instance


def test_replace_station_preserves_customer_sequence():
    inst = make_synthetic_instance(station_ids=[1001, 1002])
    stops = [
        RouteStop(node_id=0),
        RouteStop(node_id=1001),
        RouteStop(node_id=1),
        RouteStop(node_id=2),
        RouteStop(node_id=0),
    ]
    route = Route(route_id=0, stops=stops, customer_indices=[0, 1])
    cand = _replace_station_visit(route, 1, 1002)
    assert _customer_sequence(inst, route) == _customer_sequence(inst, cand)


def test_replacement_det_feasible_when_energy_ok():
    inst = make_synthetic_instance(station_ids=[1001, 1002], charging_rate=5.0)
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.2)
    route = Route(
        route_id=0,
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=1001, energy_charged=10.0),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ],
        customer_indices=[0],
    )
    cand = _replace_station_visit(route, 1, 1002)
    tr = simulate_route_fixed(inst, cand, cfg)
    assert tr.feasible


def test_probe_accepts_minimal_solution():
    inst = make_synthetic_instance()
    cfg = SimulatorConfig(
        battery_capacity=inst.ev_specs.battery_capacity,
        energy_consumption_rate=0.15,
    )
    sol = Solution(
        instance_key=inst.instance_key,
        variant="A",
        method="SYNTH",
        battery_capacity=cfg.battery_capacity,
        energy_consumption_rate=cfg.energy_consumption_rate,
        routes=[
            Route(
                route_id=0,
                stops=[
                    RouteStop(node_id=0),
                    RouteStop(node_id=inst.station_node_ids[0]),
                    RouteStop(node_id=1),
                    RouteStop(node_id=0),
                ],
            )
        ],
    )
    from star_evrp.repair_probe import run_repair_probe

    report = run_repair_probe(
        inst,
        sol,
        cfg,
        diagnostic_scenarios=80,
        master_seed=0,
        max_routes=5,
    )
    assert report.routes_examined >= 0
    for c in report.candidates:
        if c.action == "replace_station" and c.det_feasible:
            r = next(rt for rt in sol.routes if rt.route_id == c.route_id)
            parts = c.candidate_id.split("_")
            visit_idx = int(parts[-2]) if "rep" in c.action else None
            if visit_idx is not None:
                cand = _replace_station_visit(r, visit_idx, int(parts[-1]))
                assert _customer_sequence(inst, r) == _customer_sequence(inst, cand)