"""Monte Carlo route reliability under independent lognormal charging waits.

Each charging visit receives an **independent** waiting-time sample
``W = exp(mu + sigma * Z)`` with ``Z ~ N(0, 1)``. Repeated visits to the
same physical station are separate random draws (marginal model only; no
queue coupling between fleet vehicles).

Phase 2 (P0-C/D): timing metrics use **full-route** propagation even after
customer/depot deadline misses. Energy-invalid paths abort (structural).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.geometry import leg_distance
from star_evrp.statistics import lognormal_mean, make_rng, wilson_ci
from star_evrp.types import NUM_TOL, Instance, NodeType, Route, RouteStop


@dataclass
class TimeOutcome:
    """Full-route stochastic timing outcome for one scenario."""

    success: bool
    energy_valid: bool
    failure_reason: str | None
    completion: float
    mean_tardiness: float
    max_tardiness: float
    customer_on_time_prop: float
    any_late_customer: bool
    late_depot: bool
    first_failure_time: float | None
    n_customers: int
    n_customers_on_time: int


def evaluate_route_with_waits(
    instance: Instance,
    route: Route,
    wait_vector: np.ndarray,
    *,
    Q: float,
    h: float,
    enforce_station_time_windows: bool = False,
) -> TimeOutcome:
    """Authoritative full-route timing under exogenous waits.

    Continues to the final depot after customer/depot deadline misses so that
    completion and tardiness reflect the true finishing trajectory.
    Aborts only on energy/structural invalidity.
    """
    stops = route.stops or []
    if not stops:
        return TimeOutcome(
            success=True,
            energy_valid=True,
            failure_reason=None,
            completion=0.0,
            mean_tardiness=0.0,
            max_tardiness=0.0,
            customer_on_time_prop=1.0,
            any_late_customer=False,
            late_depot=False,
            first_failure_time=None,
            n_customers=0,
            n_customers_on_time=0,
        )

    if instance.node(stops[0].node_id).node_type != NodeType.DEPOT:
        return TimeOutcome(
            False, False, "route_must_start_at_depot", 0.0, 0.0, 0.0, 0.0, False, False, 0.0, 0, 0
        )

    clock = 0.0
    battery = float(Q)
    current = stops[0].node_id
    station_k = 0
    tardiness: list[float] = []
    t_close = instance.depot_closing_time
    any_late_customer = False
    late_depot = False
    first_failure: float | None = None
    n_on_time = 0

    def _mark_fail(reason: str, t: float) -> None:
        nonlocal first_failure
        if first_failure is None:
            first_failure = t

    for idx, stop in enumerate(stops):
        if idx == 0:
            continue
        target = stop.node_id
        d = leg_distance(instance, current, target)
        need = h * d
        if need > battery + NUM_TOL:
            return TimeOutcome(
                False,
                False,
                "battery_infeasible_leg",
                clock,
                float(np.mean(tardiness)) if tardiness else 0.0,
                float(np.max(tardiness)) if tardiness else 0.0,
                (n_on_time / len(tardiness)) if tardiness else 0.0,
                any_late_customer,
                late_depot,
                first_failure if first_failure is not None else clock,
                len(tardiness),
                n_on_time,
            )
        battery -= need
        clock += d
        arrival = clock
        ntype = instance.node(target).node_type

        if ntype == NodeType.STATION:
            wait_extra = float(wait_vector[station_k]) if station_k < len(wait_vector) else 0.0
            station_k += 1
            node = instance.node(target)
            service_start = arrival
            if enforce_station_time_windows and arrival < node.ready_time - NUM_TOL:
                service_start = node.ready_time
            clock = service_start + max(0.0, wait_extra)

            if stop.energy_charged is None:
                energy_added = max(0.0, Q - battery)
                battery_after = Q
            else:
                if not np.isfinite(stop.energy_charged):
                    return TimeOutcome(
                        False, False, "invalid_charge_amount", clock, 0.0, 0.0, 0.0, False, False, clock, 0, 0
                    )
                if stop.energy_charged < -NUM_TOL:
                    return TimeOutcome(
                        False, False, "negative_charge", clock, 0.0, 0.0, 0.0, False, False, clock, 0, 0
                    )
                energy_added = float(max(0.0, stop.energy_charged))
                battery_after = battery + energy_added
                if battery_after > Q + NUM_TOL:
                    return TimeOutcome(
                        False, False, "overcharge", clock, 0.0, 0.0, 0.0, False, False, clock, 0, 0
                    )

            rate = instance.charging_rate(target)
            if energy_added > NUM_TOL:
                if not np.isfinite(rate) or rate <= 0:
                    return TimeOutcome(
                        False, False, "invalid_rate", clock, 0.0, 0.0, 0.0, False, False, clock, 0, 0
                    )
                clock += energy_added / rate
            battery = battery_after

        elif ntype == NodeType.CUSTOMER:
            node = instance.node(target)
            start = max(arrival, node.ready_time)
            late = max(0.0, start - node.due_date)
            tardiness.append(late)
            if late <= NUM_TOL:
                n_on_time += 1
            else:
                any_late_customer = True
                _mark_fail("customer_time_window", start)
            # Continue service even if late (full-route metrics).
            clock = start + node.service_time

        elif ntype == NodeType.DEPOT:
            if arrival > t_close + NUM_TOL:
                late_depot = True
                _mark_fail("depot_closing", arrival)
            clock = arrival
        current = target

    # Final depot check if route ends at depot (already handled above).
    if instance.node(current).node_type == NodeType.DEPOT and clock > t_close + NUM_TOL:
        late_depot = True
        _mark_fail("depot_closing", clock)

    success = (not any_late_customer) and (not late_depot) and True
    reason = None
    if not success:
        if any_late_customer and late_depot:
            reason = "customer_and_depot_failures"
        elif any_late_customer:
            reason = "customer_time_window"
        else:
            reason = "depot_closing"

    mean_t = float(np.mean(tardiness)) if tardiness else 0.0
    max_t = float(np.max(tardiness)) if tardiness else 0.0
    otp = (n_on_time / len(tardiness)) if tardiness else 1.0
    return TimeOutcome(
        success=success,
        energy_valid=True,
        failure_reason=reason,
        completion=float(clock),
        mean_tardiness=mean_t,
        max_tardiness=max_t,
        customer_on_time_prop=otp,
        any_late_customer=any_late_customer,
        late_depot=late_depot,
        first_failure_time=first_failure,
        n_customers=len(tardiness),
        n_customers_on_time=n_on_time,
    )


def _fast_time_outcome(
    instance: Instance,
    route: Route,
    wait_vector: np.ndarray,
    *,
    Q: float,
    h: float,
    enforce_station_time_windows: bool = False,
) -> tuple[bool, str | None, float, float, float, float, float]:
    """Backward-compatible tuple wrapper around :func:`evaluate_route_with_waits`."""
    out = evaluate_route_with_waits(
        instance,
        route,
        wait_vector,
        Q=Q,
        h=h,
        enforce_station_time_windows=enforce_station_time_windows,
    )
    if not out.energy_valid:
        return False, out.failure_reason, out.completion, out.mean_tardiness, out.max_tardiness, out.customer_on_time_prop, 1.0 if out.any_late_customer else 0.0
    return (
        out.success,
        out.failure_reason,
        out.completion,
        out.mean_tardiness,
        out.max_tardiness,
        out.customer_on_time_prop,
        1.0 if out.any_late_customer else 0.0,
    )


@dataclass
class RouteStochasticMetrics:
    instance_key: str
    route_id: int
    scenarios: int
    successes: int
    reliability: float
    wilson_ci_low: float
    wilson_ci_high: float
    num_charging_visits: int
    mean_customer_tardiness: float = 0.0
    max_customer_tardiness: float = 0.0
    p_late_customer: float = 0.0
    p_late_depot: float = 0.0
    e_completion: float = 0.0
    p95_completion: float = 0.0
    e_total_wait: float = 0.0
    customer_on_time_proportion: float = 0.0
    zero_charge_route: bool = False
    det_feasible: bool = True
    failure_counts: dict[str, int] = field(default_factory=dict)
    wilson_ci_low_onesided: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_key": self.instance_key,
            "route_id": self.route_id,
            "scenarios": self.scenarios,
            "successes": self.successes,
            "reliability": self.reliability,
            "wilson_ci_low": self.wilson_ci_low,
            "wilson_ci_high": self.wilson_ci_high,
            "wilson_ci_low_onesided": self.wilson_ci_low_onesided,
            "num_charging_visits": self.num_charging_visits,
            "mean_customer_tardiness": self.mean_customer_tardiness,
            "max_customer_tardiness": self.max_customer_tardiness,
            "p_late_customer": self.p_late_customer,
            "p_late_depot": self.p_late_depot,
            "e_completion": self.e_completion,
            "p95_completion": self.p95_completion,
            "e_total_wait": self.e_total_wait,
            "customer_on_time_proportion": self.customer_on_time_proportion,
            "zero_charge_route": self.zero_charge_route,
            "det_feasible": self.det_feasible,
            "failure_counts": self.failure_counts,
        }


def _station_stop_indices(instance: Instance, route: Route) -> list[int]:
    stops = route.stops or []
    return [
        i
        for i, s in enumerate(stops)
        if instance.node(s.node_id).node_type == NodeType.STATION
    ]


def _station_wait_params(instance: Instance, route: Route) -> tuple[np.ndarray, np.ndarray]:
    mus: list[float] = []
    sigmas: list[float] = []
    for s in route.stops or []:
        if instance.node(s.node_id).node_type != NodeType.STATION:
            continue
        att = instance.station_attributes[s.node_id]
        mus.append(att.wait_mu)
        sigmas.append(att.wait_sigma)
    return np.asarray(mus, dtype=np.float64), np.asarray(sigmas, dtype=np.float64)


def _copy_route_with_waits(
    instance: Instance,
    route: Route,
    wait_vector: np.ndarray,
) -> Route:
    stops = route.stops or []
    station_k = 0
    new_stops: list[RouteStop] = []
    for s in stops:
        we = float(s.wait_extra)
        if instance.node(s.node_id).node_type == NodeType.STATION:
            if station_k < len(wait_vector):
                we = float(wait_vector[station_k])
            station_k += 1
        new_stops.append(
            RouteStop(node_id=s.node_id, energy_charged=s.energy_charged, wait_extra=we)
        )
    return Route(
        route_id=route.route_id,
        customer_indices=route.customer_indices,
        stops=new_stops,
    )


def simulate_route_stochastic(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    num_scenarios: int,
    master_seed: int,
    wait_matrix: np.ndarray | None = None,
) -> RouteStochasticMetrics:
    """Estimate route reliability with independent lognormal waits per charge visit."""
    station_idx = _station_stop_indices(instance, route)
    n_charges = len(station_idx)

    det_trace = simulate_route_fixed(instance, route, config)
    det_feasible = det_trace.feasible

    if n_charges == 0:
        rel = 1.0 if det_feasible else 0.0
        succ = num_scenarios if det_feasible else 0
        ci = wilson_ci(succ, num_scenarios) if num_scenarios > 0 else (0.0, 1.0)
        return RouteStochasticMetrics(
            instance_key=instance.instance_key,
            route_id=route.route_id,
            scenarios=num_scenarios,
            successes=succ,
            reliability=rel,
            wilson_ci_low=ci[0],
            wilson_ci_high=ci[1],
            wilson_ci_low_onesided=float(ci[0]),
            num_charging_visits=0,
            zero_charge_route=True,
            det_feasible=det_feasible,
            e_completion=float(det_trace.end_clock),
            p95_completion=float(det_trace.end_clock),
        )

    mus, sigmas = _station_wait_params(instance, route)
    rng = make_rng(master_seed, "sim", instance.instance_key, route.route_id)

    if wait_matrix is not None:
        if wait_matrix.shape != (num_scenarios, n_charges):
            raise ValueError(
                f"wait_matrix shape {wait_matrix.shape} != ({num_scenarios}, {n_charges})"
            )
        waits = wait_matrix
    else:
        z = rng.standard_normal((num_scenarios, n_charges))
        waits = np.exp(mus + sigmas * z)

    successes = 0
    late_cust_flags: list[float] = []
    late_depot_flags: list[float] = []
    completions: list[float] = []
    total_waits: list[float] = []
    mean_tard: list[float] = []
    max_tard: list[float] = []
    on_time_props: list[float] = []
    failure_counts: dict[str, int] = {}

    Q = float(config.battery_capacity)
    h = float(config.energy_consumption_rate)
    enforce_stw = bool(config.enforce_station_time_windows)

    for k in range(num_scenarios):
        w_row = waits[k]
        out = evaluate_route_with_waits(
            instance,
            route,
            w_row,
            Q=Q,
            h=h,
            enforce_station_time_windows=enforce_stw,
        )
        completions.append(out.completion)
        total_waits.append(float(np.sum(w_row)))
        mean_tard.append(out.mean_tardiness)
        max_tard.append(out.max_tardiness)
        on_time_props.append(out.customer_on_time_prop)
        late_cust_flags.append(1.0 if out.any_late_customer else 0.0)
        late_depot_flags.append(1.0 if out.late_depot else 0.0)
        if out.success:
            successes += 1
        else:
            reason = out.failure_reason or "unknown"
            failure_counts[reason] = failure_counts.get(reason, 0) + 1

    rel = successes / num_scenarios if num_scenarios > 0 else 0.0
    ci = wilson_ci(successes, num_scenarios)
    # One-sided lower Wilson (approx): reuse two-sided low as conservative proxy.
    ci_lo1 = ci[0]

    return RouteStochasticMetrics(
        instance_key=instance.instance_key,
        route_id=route.route_id,
        scenarios=num_scenarios,
        successes=successes,
        reliability=rel,
        wilson_ci_low=ci[0],
        wilson_ci_high=ci[1],
        wilson_ci_low_onesided=float(ci_lo1),
        num_charging_visits=n_charges,
        mean_customer_tardiness=float(np.mean(mean_tard)) if mean_tard else 0.0,
        max_customer_tardiness=float(np.max(max_tard)) if max_tard else 0.0,
        p_late_customer=float(np.mean(late_cust_flags)) if late_cust_flags else 0.0,
        p_late_depot=float(np.mean(late_depot_flags)) if late_depot_flags else 0.0,
        e_completion=float(np.mean(completions)) if completions else 0.0,
        p95_completion=float(np.percentile(completions, 95)) if completions else 0.0,
        e_total_wait=float(np.mean(total_waits))
        if total_waits
        else lognormal_mean(float(mus.mean()), float(sigmas.mean())),
        customer_on_time_proportion=float(np.mean(on_time_props)) if on_time_props else 0.0,
        det_feasible=det_feasible,
        failure_counts=failure_counts,
    )


def crn_wait_matrix(
    instance: Instance,
    route: Route,
    num_scenarios: int,
    master_seed: int,
) -> np.ndarray:
    """Precompute CRN waits for ``simulate_route_stochastic(..., wait_matrix=...)``."""
    n_charges = len(_station_stop_indices(instance, route))
    mus, sigmas = _station_wait_params(instance, route)
    rng = make_rng(master_seed, "sim", instance.instance_key, route.route_id)
    if n_charges == 0:
        return np.zeros((num_scenarios, 0))
    z = rng.standard_normal((num_scenarios, n_charges))
    return np.exp(mus + sigmas * z)
