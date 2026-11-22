"""Charge moves preserve customer order and reject bad energy."""

from __future__ import annotations

from star_evrp.charge_moves import (
    customer_sequence_checksum,
    insert_station,
    remove_station,
    replace_station,
    set_charge_amount,
)
from star_evrp.charge_plan import routes_share_customers
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.types import Route, RouteStop

from tests.conftest import make_synthetic_instance


def _base_route(inst):
    sid = inst.station_node_ids[0]
    return Route(
        route_id=1,
        customer_indices=[0, 1],
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=inst.customer_node_ids[0]),
            RouteStop(node_id=sid, energy_charged=None),
            RouteStop(node_id=inst.customer_node_ids[1]),
            RouteStop(node_id=0),
        ],
    )


def test_moves_preserve_customers():
    inst = make_synthetic_instance(num_customers=2, station_ids=[1001, 1002])
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.2)
    base = _base_route(inst)
    cs0 = customer_sequence_checksum(inst, base)

    sid2 = inst.station_node_ids[1]
    rep = replace_station(inst, base, 2, sid2, cfg)
    assert rep.feasible and rep.route and routes_share_customers(inst, base, rep.route)

    rem = remove_station(inst, base, 2, cfg)
    if rem.feasible and rem.route:
        assert routes_share_customers(inst, base, rem.route)

    ins = insert_station(inst, base, 1, inst.station_node_ids[-1], None, cfg)
    if ins.feasible and ins.route:
        assert customer_sequence_checksum(inst, ins.route) == cs0

    bad = set_charge_amount(inst, base, 2, -5.0, cfg)
    assert not bad.feasible

    over = set_charge_amount(inst, base, 2, Q + 100.0, cfg)
    assert not over.feasible