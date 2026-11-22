"""Monte Carlo route reliability tests."""

from __future__ import annotations

from scipy import stats

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.risk_bounds import isolated_wait_threshold
from star_evrp.stochastic_simulator import crn_wait_matrix, simulate_route_stochastic
from star_evrp.types import Route, RouteStop

from tests.conftest import make_synthetic_instance


def test_zero_charge_route_reliability_equals_det():
    inst = make_synthetic_instance()
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.2)
    route = Route(
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ]
    )
    det = simulate_route_fixed(inst, route, cfg)
    m = simulate_route_stochastic(inst, route, cfg, num_scenarios=100, master_seed=42)
    assert m.zero_charge_route
    expected = 1.0 if det.feasible else 0.0
    assert m.reliability == expected


def test_reproducibility_same_seed():
    inst = make_synthetic_instance(wait_mu=-2.0, wait_sigma=0.2)
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.3)
    sid = inst.station_node_ids[0]
    route = Route(
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ]
    )
    m1 = simulate_route_stochastic(inst, route, cfg, num_scenarios=400, master_seed=7)
    m2 = simulate_route_stochastic(inst, route, cfg, num_scenarios=400, master_seed=7)
    assert m1.reliability == m2.reliability
    assert m1.successes == m2.successes


def test_one_station_analytical_agreement_within_tol():
    inst = make_synthetic_instance(
        depot_closing=300.0,
        wait_mu=-1.5,
        wait_sigma=0.25,
        charging_rate=5.0,
    )
    Q = 80.0
    h = 0.2
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=h)
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
    pos = 1
    tau = isolated_wait_threshold(inst, route, cfg, pos, tol=0.25)
    att = inst.station_attributes[sid]
    analytical = float(stats.lognorm.cdf(tau, s=att.wait_sigma, scale=float(__import__("numpy").exp(att.wait_mu))))

    n = 8000
    crn = crn_wait_matrix(inst, route, n, master_seed=123)
    m = simulate_route_stochastic(
        inst, route, cfg, num_scenarios=n, master_seed=123, wait_matrix=crn
    )
    assert abs(m.reliability - analytical) < 0.03