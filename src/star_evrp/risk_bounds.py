"""Safe stochastic infeasibility screen via isolated wait thresholds.

Phase 2 correction (P0-A): return an **upper** bracket ``tau_upper >= tau*``
so that ``F(tau_upper)`` is a valid upper envelope for the isolated-wait
CDF and ``U = min_j F_j(tau_upper[j])`` remains a necessary-condition
rejection test (never an acceptance certificate).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import stats

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.types import Instance, NodeType, Route, RouteStop

# Small outward slack so floating-point boundary cases remain conservative.
TAU_OUTWARD_SLACK = 1e-6


@dataclass
class ReliabilityBoundResult:
    route_id: int
    det_feasible: bool
    num_charging_visits: int
    tau: list[float]
    """Deprecated alias: same as ``tau_upper`` (kept for Phase 1 JSON compatibility)."""

    tau_upper: list[float] = field(default_factory=list)
    tau_lower: list[float] = field(default_factory=list)
    upper_bound_u: float = 0.0
    upper_bound_u_indep: float = 0.0
    critical_visit_index: int | None = None
    station_node_ids: list[int] = field(default_factory=list)
    safe_reject: bool = False
    target: float = 0.95
    certified: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "det_feasible": self.det_feasible,
            "num_charging_visits": self.num_charging_visits,
            "isolated_wait_thresholds": self.tau_upper or self.tau,
            "tau_upper": self.tau_upper or self.tau,
            "tau_lower": self.tau_lower,
            "upper_bound_u": self.upper_bound_u,
            "upper_bound_u_indep": self.upper_bound_u_indep,
            "critical_visit_index": self.critical_visit_index,
            "station_node_ids": self.station_node_ids,
            "safe_reject": self.safe_reject,
            "target": self.target,
            "certified": self.certified,
            "notes": self.notes,
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
    """Deterministic timing feasibility with one isolated wait (reference path)."""
    r2 = _route_with_isolated_wait(route, visit_pos, wait)
    return simulate_route_fixed(instance, r2, config).feasible


def isolated_wait_threshold(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    visit_pos: int,
    *,
    hi_cap: float | None = None,
    tol: float = 1e-3,
    max_iter: int = 64,
    outward_slack: float = TAU_OUTWARD_SLACK,
) -> float:
    """Return a **safe upper** isolated-wait threshold ``tau_upper >= tau*``.

    On a monotone feasible/infeasible bisection, return the infeasible upper
    bracket (plus outward slack). If the search never finds infeasibility up
    to ``hi_cap``, return ``+inf`` (CDF = 1; never reject on that visit).
    """
    if hi_cap is None:
        hi_cap = float(instance.depot_closing_time) + 1.0

    if not _feasible_with_wait(instance, route, config, visit_pos, 0.0):
        return 0.0

    lo = 0.0
    hi = 1.0
    while hi < hi_cap and _feasible_with_wait(instance, route, config, visit_pos, hi):
        lo = hi
        hi = min(hi_cap, hi * 2.0 if hi > 0 else 1.0)

    if hi >= hi_cap and _feasible_with_wait(instance, route, config, visit_pos, hi_cap):
        # Never observed infeasibility: infinite tolerance.
        return float("inf")

    # ``hi`` is an infeasible upper bracket; ``lo`` is feasible.
    for _ in range(max_iter):
        if hi - lo <= tol:
            break
        mid = 0.5 * (lo + hi)
        if _feasible_with_wait(instance, route, config, visit_pos, mid):
            lo = mid
        else:
            hi = mid

    # Conservative for an *upper* reliability bound: use infeasible bracket + slack.
    return float(hi + outward_slack)


def isolated_wait_threshold_brackets(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    visit_pos: int,
    *,
    hi_cap: float | None = None,
    tol: float = 1e-3,
    max_iter: int = 64,
    outward_slack: float = TAU_OUTWARD_SLACK,
) -> tuple[float, float]:
    """Return ``(tau_lower_feasible, tau_upper_safe)`` for diagnostics."""
    if hi_cap is None:
        hi_cap = float(instance.depot_closing_time) + 1.0
    if not _feasible_with_wait(instance, route, config, visit_pos, 0.0):
        return 0.0, 0.0

    lo = 0.0
    hi = 1.0
    while hi < hi_cap and _feasible_with_wait(instance, route, config, visit_pos, hi):
        lo = hi
        hi = min(hi_cap, hi * 2.0 if hi > 0 else 1.0)

    if hi >= hi_cap and _feasible_with_wait(instance, route, config, visit_pos, hi_cap):
        return hi_cap, float("inf")

    for _ in range(max_iter):
        if hi - lo <= tol:
            break
        mid = 0.5 * (lo + hi)
        if _feasible_with_wait(instance, route, config, visit_pos, mid):
            lo = mid
        else:
            hi = mid
    return float(lo), float(hi + outward_slack)


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
    if not math.isfinite(x):
        return 1.0 if x > 0 else 0.0
    if x <= 0.0:
        return 0.0
    if sigma <= 0.0:
        # Point mass at exp(mu)
        return 1.0 if x >= math.exp(mu) - 1e-12 else 0.0
    return float(stats.lognorm.cdf(x, s=sigma, scale=np.exp(mu)))


def reliability_upper_bound(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    target: float = 0.95,
) -> ReliabilityBoundResult:
    """Compute ``U(p) = min_j F_j(tau_upper_j)`` and product bound under independence."""
    det = simulate_route_fixed(instance, route, config)
    positions = _station_positions(route, instance)
    station_ids = [route.stops[i].node_id for i in positions]  # type: ignore

    if not det.feasible:
        return ReliabilityBoundResult(
            route_id=route.route_id,
            det_feasible=False,
            num_charging_visits=len(positions),
            tau=[0.0] * len(positions),
            tau_upper=[0.0] * len(positions),
            tau_lower=[0.0] * len(positions),
            upper_bound_u=0.0,
            upper_bound_u_indep=0.0,
            critical_visit_index=None,
            station_node_ids=station_ids,
            safe_reject=safe_reject(0.0, target),
            target=target,
            notes="deterministically_infeasible",
        )

    if not positions:
        u = 1.0
        return ReliabilityBoundResult(
            route_id=route.route_id,
            det_feasible=True,
            num_charging_visits=0,
            tau=[],
            tau_upper=[],
            tau_lower=[],
            upper_bound_u=u,
            upper_bound_u_indep=u,
            critical_visit_index=None,
            station_node_ids=[],
            safe_reject=safe_reject(u, target),
            target=target,
            notes="zero_charge_route",
        )

    tau_uppers: list[float] = []
    tau_lowers: list[float] = []
    cdfs: list[float] = []
    for pos, sid in zip(positions, station_ids, strict=True):
        lo, hi = isolated_wait_threshold_brackets(instance, route, config, pos)
        tau_lowers.append(lo)
        tau_uppers.append(hi)
        att = instance.station_attributes[sid]
        cdfs.append(_lognormal_cdf(hi, att.wait_mu, att.wait_sigma))

    u_min = float(min(cdfs)) if cdfs else 1.0
    u_prod = float(np.prod(cdfs)) if cdfs else 1.0
    # Dependence-robust necessary condition uses min; product is tighter under independence.
    u = u_min
    crit = int(np.argmin(cdfs)) if cdfs else None
    return ReliabilityBoundResult(
        route_id=route.route_id,
        det_feasible=True,
        num_charging_visits=len(positions),
        tau=list(tau_uppers),
        tau_upper=tau_uppers,
        tau_lower=tau_lowers,
        upper_bound_u=u,
        upper_bound_u_indep=u_prod,
        critical_visit_index=crit,
        station_node_ids=station_ids,
        safe_reject=safe_reject(u, target),
        target=target,
        notes="upper_bracket_min_cdf",
    )


def safe_reject(upper_bound_u: float, target: float = 0.95) -> bool:
    """True if ``U(p) < target`` (necessary-condition infeasibility for target reliability)."""
    return upper_bound_u < target - 1e-12


def isolated_wait_threshold_legacy_lower(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    visit_pos: int,
    *,
    hi_cap: float | None = None,
    tol: float = 1.0,
    max_iter: int = 40,
) -> float:
    """Phase-1 buggy behaviour: return feasible ``lo`` (unsafe for upper bounds).

    Kept only for counterexample tests demonstrating P0-A.
    """
    if hi_cap is None:
        hi_cap = float(instance.depot_closing_time) + 1.0
    if not _feasible_with_wait(instance, route, config, visit_pos, 0.0):
        return 0.0
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
