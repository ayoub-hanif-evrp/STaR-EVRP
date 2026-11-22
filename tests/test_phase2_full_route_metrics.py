"""Full-route completion after early customer lateness."""

from __future__ import annotations

import numpy as np

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.stochastic_simulator import evaluate_route_with_waits
from star_evrp.types import Route, RouteStop

from tests.conftest import make_synthetic_instance


def test_late_customer_still_runs_to_depot_completion():
    inst = make_synthetic_instance(
        num_customers=1,
        depot_closing=400.0,
        customer_tw=(0.0, 40.0),
        charging_rate=5.0,
        wait_mu=-0.5,
        wait_sigma=0.1,
    )
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.2)
    sid = inst.station_node_ids[0]
    route = Route(
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid, energy_charged=None),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ]
    )
    assert simulate_route_fixed(inst, route, cfg).feasible
    huge_wait = np.array([35.0])
    out = evaluate_route_with_waits(inst, route, huge_wait, Q=Q, h=cfg.energy_consumption_rate)
    assert out.any_late_customer
    assert out.first_failure_time is not None
    assert out.completion > out.first_failure_time
    assert out.n_customers == 1
    assert out.mean_tardiness > 0