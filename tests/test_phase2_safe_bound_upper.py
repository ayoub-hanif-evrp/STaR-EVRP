"""P0-A: legacy lower bracket can falsely reject; upper bracket cannot."""

from __future__ import annotations

from scipy import stats

import numpy as np

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.risk_bounds import (
    isolated_wait_threshold,
    isolated_wait_threshold_legacy_lower,
    reliability_upper_bound,
    safe_reject,
)
from star_evrp.stochastic_simulator import crn_wait_matrix, simulate_route_stochastic
from star_evrp.types import Route, RouteStop

from tests.conftest import make_synthetic_instance


def _route(wait_mu=-1.5, wait_sigma=0.2):
    inst = make_synthetic_instance(
        depot_closing=350.0,
        wait_mu=wait_mu,
        wait_sigma=wait_sigma,
        charging_rate=8.0,
        ev_specs=__import__("star_evrp.types", fromlist=["EVSpecs"]).EVSpecs(55.0, 0.18),
    )
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.18)
    sid = inst.station_node_ids[0]
    route = Route(
        route_id=3,
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid, energy_charged=None),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ],
    )
    return inst, cfg, route, sid


def test_legacy_lower_can_falsely_reject_near_target():
    inst, cfg, route, sid = _route()
    assert simulate_route_fixed(inst, route, cfg).feasible
    pos = 1
    tau_lo = isolated_wait_threshold_legacy_lower(inst, route, cfg, pos, tol=0.5)
    tau_hi = isolated_wait_threshold(inst, route, cfg, pos, tol=0.01)
    assert tau_lo <= tau_hi + 1e-6
    att = inst.station_attributes[sid]
    scale = float(np.exp(att.wait_mu))
    cdf_lo = float(stats.lognorm.cdf(tau_lo, s=att.wait_sigma, scale=scale))
    cdf_hi = float(stats.lognorm.cdf(tau_hi, s=att.wait_sigma, scale=scale))
    # Upper bracket CDF is at least as large as lower-bracket CDF.
    assert cdf_hi >= cdf_lo - 1e-9
    # Legacy safe_reject on min CDF at tau_lo can trigger while true R may exceed target.
    legacy_u = cdf_lo
    new_res = reliability_upper_bound(inst, route, cfg, target=0.95)
    if legacy_u < 0.95:
        assert safe_reject(legacy_u, target=0.95)
    assert new_res.upper_bound_u >= legacy_u - 1e-9
    mc = simulate_route_stochastic(inst, route, cfg, num_scenarios=1500, master_seed=99)
    assert mc.reliability <= new_res.upper_bound_u + 0.08
    # New upper screen must not reject when bound is above target.
    if new_res.upper_bound_u >= 0.95:
        assert not safe_reject(new_res.upper_bound_u, target=0.95)


def test_indep_product_never_exceeds_min_cdf():
    inst, cfg, route, _ = _route(wait_mu=-2.0, wait_sigma=0.15)
    res = reliability_upper_bound(inst, route, cfg, target=0.95)
    assert res.upper_bound_u_indep <= res.upper_bound_u + 1e-12