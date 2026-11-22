"""Customer time windows and depot closing."""

from __future__ import annotations

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.geometry import build_coordinate_array, precompute_distance_matrix
from star_evrp.types import Node, NodeType, Route, RouteStop

from tests.conftest import make_synthetic_instance


def test_customer_time_window_violation():
    inst = make_synthetic_instance(customer_tw=(0.0, 20.0), depot_closing=500.0)
    inst.nodes[1] = Node(
        node_id=1,
        node_type=NodeType.CUSTOMER,
        x=200.0,
        y=0.0,
        demand=1.0,
        ready_time=0.0,
        due_date=20.0,
        service_time=5.0,
    )
    inst.coordinates = build_coordinate_array(inst.nodes)
    inst.distance_matrix = precompute_distance_matrix(inst.coordinates)
    cfg = SimulatorConfig(battery_capacity=500.0, energy_consumption_rate=1.0)
    route = Route(stops=[RouteStop(node_id=0), RouteStop(node_id=1), RouteStop(node_id=0)])
    trace = simulate_route_fixed(inst, route, cfg)
    assert not trace.feasible
    assert trace.failure_reason == "customer_time_window"


def test_depot_closing_violation():
    inst = make_synthetic_instance(customer_tw=(0.0, 500.0), depot_closing=8.0)
    cfg = SimulatorConfig(battery_capacity=200.0, energy_consumption_rate=0.01)
    route = Route(stops=[RouteStop(node_id=0), RouteStop(node_id=1), RouteStop(node_id=0)])
    trace = simulate_route_fixed(inst, route, cfg)
    assert not trace.feasible
    assert trace.failure_reason == "depot_closing"