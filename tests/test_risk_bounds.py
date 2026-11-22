"""Isolated-wait upper bound and safe-reject behavior."""

from __future__ import annotations

from scipy import stats

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.risk_bounds import reliability_upper_bound, safe_reject
from star_evrp.stochastic_simulator import simulate_route_stochastic
from star_evrp.types import Route, RouteStop

from tests.conftest import make_synthetic_instance


def _toy_route_with_charge(wait_mu=-3.0, wait_sigma=0.1):
    inst = make_synthetic_instance(
        depot_closing=400.0,
        wait_mu=wait_mu,
        wait_sigma=wait_sigma,
        charging_rate=10.0,
    )
    Q = 60.0
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.15)
    sid = inst.station_node_ids[0]
    route = Route(
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid, energy_charged=5.0),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ]
    )
    return inst, cfg, route, sid


def test_upper_bound_matches_min_cdf_on_toy():
    inst, cfg, route, sid = _toy_route_with_charge()
    assert simulate_route_fixed(inst, route, cfg).feasible
    res = reliability_upper_bound(inst, route, cfg, target=0.95)
    att = inst.station_attributes[sid]
    tau = res.tau[0]
    cdf = float(stats.lognorm.cdf(tau, s=att.wait_sigma, scale=float(__import__("numpy").exp(att.wait_mu))))
    assert abs(res.upper_bound_u - cdf) < 1e-6
    m = simulate_route_stochastic(inst, route, cfg, num_scenarios=5000, master_seed=11)
    assert m.reliability <= res.upper_bound_u + 0.05


def test_no_unsafe_reject_when_bound_above_target():
    inst, cfg, route, _ = _toy_route_with_charge(wait_mu=-5.0, wait_sigma=0.05)
    res = reliability_upper_bound(inst, route, cfg, target=0.95)
    assert res.upper_bound_u >= 0.95
    assert not safe_reject(res.upper_bound_u, target=0.95)