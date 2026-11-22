"""Monte Carlo route reliability under independent lognormal charging waits.

Each charging visit receives an **independent** waiting-time sample
``W = exp(mu + sigma * Z)`` with ``Z ~ N(0, 1)``. Repeated visits to the
same physical station are separate random draws (marginal model only; no
queue coupling between fleet vehicles).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.geometry import leg_distance
from star_evrp.statistics import lognormal_mean, make_rng, wilson_ci
from star_evrp.types import NUM_TOL, Instance, NodeType, Route, RouteStop


def _fast_time_outcome(
    instance: Instance,
    route: Route,
    wait_vector: np.ndarray,
    *,
    Q: float,
    h: float,
) -> tuple[bool, str | None, float, float, float, float, float]:
    """Lightweight timing evaluation under wait samples (energy path assumed det-feasible).

    Returns:
        feasible, reason, completion, mean_tardiness, max_tardiness,
        customer_on_time_prop, any_late_customer (0/1).
    """
    stops = route.stops or []
    if not stops:
        return True, None, 0.0, 0.0, 0.0, 1.0, 0.0

    clock = 0.0
    battery = float(Q)
    current = stops[0].node_id
    station_k = 0
    tardiness: list[float] = []
    t_close = instance.depot_closing_time

    for idx, stop in enumerate(stops):
        if idx == 0:
            continue
        target = stop.node_id
        d = leg_distance(instance, current, target)
        need = h * d
        if need > battery + NUM_TOL:
            return False, "battery_infeasible_leg", clock, 0.0, 0.0, 0.0, 0.0
        battery -= need
        clock += d
        arrival = clock
        ntype = instance.node(target).node_type
        if ntype == NodeType.STATION:
            wait_extra = float(wait_vector[station_k]) if station_k < len(wait_vector) else 0.0
            station_k += 1
            clock = arrival + max(0.0, wait_extra)
            if stop.energy_charged is None:
                energy_added = max(0.0, Q - battery)
            else:
                energy_added = max(0.0, float(stop.energy_charged))
            rate = instance.charging_rate(target)
            if energy_added > NUM_TOL:
                if rate <= 0:
                    return False, "invalid_rate", clock, 0.0, 0.0, 0.0, 0.0
                clock += energy_added / rate
            battery = min(Q, battery + energy_added)
        elif ntype == NodeType.CUSTOMER:
            node = instance.node(target)
            start = max(arrival, node.ready_time)
            late = max(0.0, start - node.due_date)
            tardiness.append(late)
            if start > node.due_date + NUM_TOL:
                mean_t = float(np.mean(tardiness))
                max_t = float(np.max(tardiness))
                otp = float(np.mean([t <= NUM_TOL for t in tardiness]))
                return False, "customer_time_window", arrival, mean_t, max_t, otp, 1.0
            clock = start + node.service_time
            if clock > t_close + NUM_TOL:
                mean_t = float(np.mean(tardiness)) if tardiness else 0.0
                max_t = float(np.max(tardiness)) if tardiness else 0.0
                otp = float(np.mean([t <= NUM_TOL for t in tardiness])) if tardiness else 1.0
                return False, "depot_closing", clock, mean_t, max_t, otp, 0.0
        elif ntype == NodeType.DEPOT:
            if arrival > t_close + NUM_TOL:
                mean_t = float(np.mean(tardiness)) if tardiness else 0.0
                max_t = float(np.max(tardiness)) if tardiness else 0.0
                otp = float(np.mean([t <= NUM_TOL for t in tardiness])) if tardiness else 1.0
                return False, "depot_closing", arrival, mean_t, max_t, otp, 0.0
            clock = arrival
        current = target

    mean_t = float(np.mean(tardiness)) if tardiness else 0.0
    max_t = float(np.max(tardiness)) if tardiness else 0.0
    otp = float(np.mean([t <= NUM_TOL for t in tardiness])) if tardiness else 1.0
    any_late = 1.0 if any(t > NUM_TOL for t in tardiness) else 0.0
    return True, None, clock, mean_t, max_t, otp, any_late


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_key": self.instance_key,
            "route_id": self.route_id,
            "scenarios": self.scenarios,
            "successes": self.successes,
            "reliability": self.reliability,
            "wilson_ci_low": self.wilson_ci_low,
            "wilson_ci_high": self.wilson_ci_high,
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


def _charging_visit_indices(route: Route) -> list[int]:
    stops = route.stops or []
    return [
        i
        for i, s in enumerate(stops)
        if stops
        and s.node_id != 0  # will also match station nodes
    ]


def _station_stop_indices(instance: Instance, route: Route) -> list[int]:
    stops = route.stops or []
    out: list[int] = []
    for i, s in enumerate(stops):
        if instance.node(s.node_id).node_type == NodeType.STATION:
            out.append(i)
    return out


def _station_wait_params(instance: Instance, route: Route) -> tuple[np.ndarray, np.ndarray]:
    mus: list[float] = []
    sigmas: list[float] = []
    for s in route.stops or []:
        nid = s.node_id
        if instance.node(nid).node_type != NodeType.STATION:
            continue
        att = instance.station_attributes[nid]
        mus.append(att.wait_mu)
        sigmas.append(att.wait_sigma)
    return np.asarray(mus, dtype=np.float64), np.asarray(sigmas, dtype=np.float64)


def _copy_route_with_waits(
    instance: Instance,
    route: Route,
    wait_vector: np.ndarray,
) -> Route:
    """Apply wait samples to station stops only (identified by node type)."""
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


def _customer_tardiness(instance: Instance, trace) -> tuple[float, float, float, float]:
    """Return mean tardiness, max tardiness, on-time proportion, any_late flag."""
    tardiness: list[float] = []
    n_cust = 0
    on_time = 0
    for st in trace.stops:
        node = instance.node(st.node_id)
        if node.node_type != NodeType.CUSTOMER:
            continue
        n_cust += 1
        late = max(0.0, st.service_start_time - node.due_date)
        tardiness.append(late)
        if late <= 1e-9:
            on_time += 1
    if not tardiness:
        return 0.0, 0.0, 1.0, 0.0
    arr = np.asarray(tardiness)
    prop = on_time / n_cust if n_cust else 1.0
    return float(np.mean(arr)), float(np.max(arr)), prop, float(np.any(arr > 1e-9))


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

    for k in range(num_scenarios):
        w_row = waits[k]
        ok, reason, completion, mt, xt, otp, any_late = _fast_time_outcome(
            instance, route, w_row, Q=Q, h=h
        )
        completions.append(completion)
        total_waits.append(float(np.sum(w_row)))
        if ok:
            successes += 1
            mean_tard.append(mt)
            max_tard.append(xt)
            on_time_props.append(otp)
            late_cust_flags.append(0.0)
            late_depot_flags.append(0.0)
        else:
            reason = reason or "unknown"
            failure_counts[reason] = failure_counts.get(reason, 0) + 1
            late_cust_flags.append(
                1.0 if reason == "customer_time_window" else float(any_late)
            )
            late_depot_flags.append(1.0 if reason == "depot_closing" else 0.0)
            mean_tard.append(mt)
            max_tard.append(xt)
            on_time_props.append(otp)

    rel = successes / num_scenarios if num_scenarios > 0 else 0.0
    ci = wilson_ci(successes, num_scenarios)

    return RouteStochasticMetrics(
        instance_key=instance.instance_key,
        route_id=route.route_id,
        scenarios=num_scenarios,
        successes=successes,
        reliability=rel,
        wilson_ci_low=ci[0],
        wilson_ci_high=ci[1],
        num_charging_visits=n_charges,
        mean_customer_tardiness=float(np.mean(mean_tard)) if mean_tard else 0.0,
        max_customer_tardiness=float(np.max(max_tard)) if max_tard else 0.0,
        p_late_customer=float(np.mean(late_cust_flags)) if late_cust_flags else 0.0,
        p_late_depot=float(np.mean(late_depot_flags)) if late_depot_flags else 0.0,
        e_completion=float(np.mean(completions)) if completions else 0.0,
        p95_completion=float(np.percentile(completions, 95)) if completions else 0.0,
        e_total_wait=float(np.mean(total_waits)) if total_waits else lognormal_mean(float(mus.mean()), float(sigmas.mean())),
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
    z = rng.standard_normal((num_scenarios, max(n_charges, 1)))
    if n_charges == 0:
        return np.zeros((num_scenarios, 0))
    return np.exp(mus + sigmas * z[:, :n_charges])