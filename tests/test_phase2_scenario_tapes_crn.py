"""CRN shares Z not W across station parameter changes."""

from __future__ import annotations

import numpy as np

from star_evrp.charge_moves import replace_station
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.scenario_tapes import generate_z_tape, waits_from_z
from star_evrp.types import Route, RouteStop, StationAttributes

from tests.conftest import make_synthetic_instance


def test_same_z_different_waits_after_station_swap():
    inst = make_synthetic_instance(station_ids=[1001, 1002], wait_mu=-1.0, wait_sigma=0.25)
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.2)
    s1, s2 = inst.station_node_ids[0], inst.station_node_ids[1]
    base_att = inst.station_attributes[s2]
    inst.station_attributes[s2] = StationAttributes(
        station_id=s2,
        charging_rate=base_att.charging_rate,
        price_mu=base_att.price_mu,
        price_sigma=base_att.price_sigma,
        wait_mu=-0.2,
        wait_sigma=0.6,
        density_score=base_att.density_score,
    )
    route = Route(
        route_id=7,
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=s1, energy_charged=None),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ],
    )
    alt = replace_station(inst, route, 1, s2, cfg)
    assert alt.feasible and alt.route

    z = generate_z_tape(42, inst.parent_key, inst.variant, route.route_id, "opt", 100, 4)
    w1 = waits_from_z(inst, route, z)
    w2 = waits_from_z(inst, alt.route, z)
    assert not np.allclose(w1[:, 0], w2[:, 0])
    z0 = z[:, 0]
    att1 = inst.station_attributes[s1]
    att2 = inst.station_attributes[s2]
    exp1 = np.exp(att1.wait_mu + att1.wait_sigma * z0)
    exp2 = np.exp(att2.wait_mu + att2.wait_sigma * z0)
    assert np.allclose(w1[:, 0], exp1)
    assert np.allclose(w2[:, 0], exp2)


def test_z_tape_order_invariant():
    inst = make_synthetic_instance()
    route = Route(route_id=1, stops=[RouteStop(node_id=0), RouteStop(node_id=1), RouteStop(node_id=0)])
    z_a = generate_z_tape(1, inst.parent_key, inst.variant, 1, "opt", 5, 2)
    z_b = generate_z_tape(1, inst.parent_key, inst.variant, 1, "opt", 5, 2)
    assert np.array_equal(z_a, z_b)