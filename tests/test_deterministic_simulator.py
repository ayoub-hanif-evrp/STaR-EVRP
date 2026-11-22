"""Deterministic simulation: charging duration, waits, monotonicity."""

from __future__ import annotations

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route, simulate_route_fixed
from star_evrp.types import Route, RouteStop

from tests.conftest import make_synthetic_instance


def test_charging_time_equals_q_over_rs():
    inst = make_synthetic_instance(charging_rate=4.0)
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=1.0)
    sid = inst.station_node_ids[0]
    route = Route(
        route_id=0,
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=1),
            RouteStop(node_id=sid, energy_charged=20.0),
            RouteStop(node_id=0),
        ],
    )
    trace = simulate_route_fixed(inst, route, cfg)
    assert trace.feasible
    station_stops = [s for s in trace.stops if s.node_id == sid]
    assert len(station_stops) == 1
    st = station_stops[0]
    assert abs(st.energy_charged - 20.0) < 1e-9
    assert abs((st.departure_time - st.service_start_time) - 20.0 / 4.0) < 1e-6


def test_zero_extra_wait_matches_no_wait_path():
    inst = make_synthetic_instance(depot_closing=200.0)
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.5)
    sid = inst.station_node_ids[0]
    base_stops = [
        RouteStop(node_id=0),
        RouteStop(node_id=1, energy_charged=None, wait_extra=0.0),
        RouteStop(node_id=sid, energy_charged=None, wait_extra=0.0),
        RouteStop(node_id=0),
    ]
    trace0 = simulate_route_fixed(inst, Route(stops=base_stops), cfg)
    trace1 = simulate_route_fixed(
        inst,
        Route(
            stops=[
                RouteStop(node_id=0),
                RouteStop(node_id=1),
                RouteStop(node_id=sid, energy_charged=None),
                RouteStop(node_id=0),
            ]
        ),
        cfg,
    )
    assert trace0.feasible == trace1.feasible
    assert abs(trace0.end_clock - trace1.end_clock) < 1e-9


def test_increasing_wait_worsens_or_preserves_infeasibility():
    inst = make_synthetic_instance(customer_tw=(0.0, 30.0), depot_closing=100.0)
    Q = 100.0
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.1)
    sid = inst.station_node_ids[0]
    route_small = Route(
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid, wait_extra=5.0),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ]
    )
    route_large = Route(
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid, wait_extra=50.0),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ]
    )
    tr_s = simulate_route_fixed(inst, route_small, cfg)
    tr_l = simulate_route_fixed(inst, route_large, cfg)
    if not tr_s.feasible:
        assert not tr_l.feasible
    elif not tr_l.feasible:
        assert tr_l.end_clock >= tr_s.end_clock - 1e-9