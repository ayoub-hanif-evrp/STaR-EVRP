"""Safe stochastic infeasibility screen via isolated wait thresholds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.stochastic_simulator import _fast_time_outcome
from star_evrp.types import Instance, NodeType, Route, RouteStop


@dataclass
class ReliabilityBoundResult:
    route_id: int
    det_feasible: bool
    num_charging_visits: int
    tau: list[float]
    upper_bound_u: float
    critical_visit_index: int | None
    station_node_ids: list[int]
    safe_reject: bool
    target: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "det_feasible": self.det_feasible,
            "num_charging_visits": self.num_charging_visits,
            "isolated_wait_thresholds": self.tau,
            "upper_bound_u": self.upper_bound_u,
            "critical_visit_index": self.critical_visit_index,
            "station_node_ids": self.station_node_ids,
            "safe_reject": self.safe_reject,
            "target": self.target,
        }


def _station_positions(route: Route, instance: Instance) -> list[int]:
    return [
        i
        for i, s in enumerate(route.stops or [])
        if instance.node(s.node_id).node_type == NodeType.STATION
    ]


def _route_with_isolated_wait(route: Route, visit_pos: int, wait: float) -> Route:
    stops: list[RouteStop] = []
    for i, s in enumerate(route.stops or []):
        extra = 0.0
        if i == visit_pos:
            extra = wait
        stops.append(
            RouteStop(node_id=s.node_id, energy_charged=s.energy_charged, wait_extra=extra)
        )
    return Route(route_id=route.route_id, stops=stops, customer_indices=route.customer_indices)


def _feasible_with_wait(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    visit_pos: int,
    wait: float,
) -> bool:
    """Timing feasibility with one isolated wait (fast path)."""
    stations = _station_positions(route, instance)
    wait_vec = np.zeros(len(stations), dtype=np.float64)
    try:
        j = stations.index(visit_pos)
    except ValueError:
        r2 = _route_with_isolated_wait(route, visit_pos, wait)
        return simulate_route_fixed(instance, r2, config).feasible
    wait_vec[j] = float(wait)
    ok, _reason, *_rest = _fast_time_outcome(
        instance,
        route,
        wait_vec,
        Q=float(config.battery_capacity),
        h=float(config.energy_consumption_rate),
    )
    return bool(ok)


def isolated_wait_threshold(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    visit_pos: int,
    *,
    hi_cap: float | None = None,
    tol: float = 1.0,
    max_iter: int = 40,
) -> float:
    """Conservative isolated wait threshold (never overestimates feasible wait)."""
    if hi_cap is None:
        hi_cap = float(instance.depot_closing_time) + 1.0
    if not _feasible_with_wait(instance, route, config, visit_pos, 0.0):
        return 0.0
    # Exponential upper search then binary search (conservative: return ``lo``).
    lo = 0.0
    hi = 1.0
    while hi < hi_cap and _feasible_with_wait(instance, route, config, visit_pos, hi):
        lo = hi
        hi = min(hi_cap, hi * 2.0)
    if hi >= hi_cap and _feasible_with_wait(instance, route, config, visit_pos, hi_cap):
        return hi_cap
    for _ in range(max_iter):
        if hi - lo <= tol:
            break
        mid = lo + 0.49 * (hi - lo)
        if _feasible_with_wait(instance, route, config, visit_pos, mid):
            lo = mid
        else:
            hi = mid
    return lo


def isolated_wait_thresholds(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
) -> list[float]:
    positions = _station_positions(route, instance)
    return [
        isolated_wait_threshold(instance, route, config, pos) for pos in positions
    ]


def _lognormal_cdf(x: float, mu: float, sigma: float) -> float:
    if x <= 0.0:
        return 0.0
    return float(stats.lognorm.cdf(x, s=sigma, scale=np.exp(mu)))


def reliability_upper_bound(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    target: float = 0.95,
) -> ReliabilityBoundResult:
    """Compute ``U(p) = min_j F_j(tau_j)`` and critical visit."""
    det = simulate_route_fixed(instance, route, config)
    positions = _station_positions(route, instance)
    station_ids = [route.stops[i].node_id for i in positions]  # type: ignore

    if not det.feasible:
        return ReliabilityBoundResult(
            route_id=route.route_id,
            det_feasible=False,
            num_charging_visits=len(positions),
            tau=[0.0] * len(positions),
            upper_bound_u=0.0,
            critical_visit_index=None,
            station_node_ids=station_ids,
            safe_reject=safe_reject(0.0, target),
            target=target,
        )

    if not positions:
        u = 1.0
        return ReliabilityBoundResult(
            route_id=route.route_id,
            det_feasible=True,
            num_charging_visits=0,
            tau=[],
            upper_bound_u=u,
            critical_visit_index=None,
            station_node_ids=[],
            safe_reject=safe_reject(u, target),
            target=target,
        )

    taus = isolated_wait_thresholds(instance, route, config)
    cdfs: list[float] = []
    for tau, sid in zip(taus, station_ids, strict=True):
        att = instance.station_attributes[sid]
        cdfs.append(_lognormal_cdf(tau, att.wait_mu, att.wait_sigma))
    u = float(min(cdfs)) if cdfs else 1.0
    crit = int(np.argmin(cdfs)) if cdfs else None
    return ReliabilityBoundResult(
        route_id=route.route_id,
        det_feasible=True,
        num_charging_visits=len(positions),
        tau=taus,
        upper_bound_u=u,
        critical_visit_index=crit,
        station_node_ids=station_ids,
        safe_reject=safe_reject(u, target),
        target=target,
    )


def safe_reject(upper_bound_u: float, target: float = 0.95) -> bool:
    """True if ``U(p) < target`` (necessary-condition infeasibility for target reliability)."""
    return upper_bound_u < target - 1e-12