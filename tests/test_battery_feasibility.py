"""Battery, energy edge cases, and load capacity."""

from __future__ import annotations

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.route_validator import validate_solution
from star_evrp.types import Route, RouteStop, Solution

from tests.conftest import make_synthetic_instance


def test_battery_underflow_on_leg():
    inst = make_synthetic_instance()
    cfg = SimulatorConfig(battery_capacity=5.0, energy_consumption_rate=10.0)
    route = Route(stops=[RouteStop(node_id=0), RouteStop(node_id=1), RouteStop(node_id=0)])
    trace = simulate_route_fixed(inst, route, cfg)
    assert not trace.feasible
    assert trace.failure_reason == "battery_infeasible_leg"


def test_overcharge_rejected_not_clamped():
    inst = make_synthetic_instance()
    Q = inst.ev_specs.battery_capacity
    sid = inst.station_node_ids[0]
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.1)
    route = Route(
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid, energy_charged=Q + 50.0),
            RouteStop(node_id=0),
        ]
    )
    trace = simulate_route_fixed(inst, route, cfg)
    assert not trace.feasible
    assert trace.failure_reason == "overcharge"


def test_negative_charge_rejected():
    inst = make_synthetic_instance()
    Q = inst.ev_specs.battery_capacity
    sid = inst.station_node_ids[0]
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.1)
    route = Route(
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid, energy_charged=-5.0),
            RouteStop(node_id=0),
        ]
    )
    trace = simulate_route_fixed(inst, route, cfg)
    assert not trace.feasible
    assert trace.failure_reason == "negative_charge"


def test_zero_energy_consumption_leg():
    inst = make_synthetic_instance()
    cfg = SimulatorConfig(battery_capacity=10.0, energy_consumption_rate=0.0)
    route = Route(stops=[RouteStop(node_id=0), RouteStop(node_id=1), RouteStop(node_id=0)])
    trace = simulate_route_fixed(inst, route, cfg)
    assert trace.feasible


def test_load_capacity_violation():
    inst = make_synthetic_instance(load_capacity=1.0, num_customers=2)
    cfg = SimulatorConfig(
        battery_capacity=inst.ev_specs.battery_capacity,
        energy_consumption_rate=0.1,
    )
    route = Route(
        route_id=0,
        customer_indices=[0, 1],
    )
    sol = Solution(
        instance_key=inst.instance_key,
        variant="A",
        method="TEST",
        battery_capacity=cfg.battery_capacity,
        energy_consumption_rate=cfg.energy_consumption_rate,
        routes=[route],
    )
    report = validate_solution(inst, sol, config=cfg)
    assert not report.feasible
    assert any("load_capacity" in (i.message or "") or "load" in i.message.lower() for i in report.issues)