"""Max-plus envelopes and restricted single-visit optimization."""

from dataclasses import dataclass
from math import exp, inf, log, log1p, nextafter
from time import perf_counter, process_time

import numpy as np
from scipy.special import log_ndtr, ndtr

from star_evrp.charge_plan import customer_node_ids
from star_evrp.deterministic_simulator import simulate_route_fixed
from star_evrp.route_validator import validate_repair
from star_evrp.timing import RouteTiming, TimingStep
from star_evrp.types import NUM_TOL, Route, RouteStop


@dataclass(frozen=True)
class Envelope:
    offset: float = 0.0
    floor: float = -inf
    latest: float = inf
    feasible_floor: bool = True


def start_limit(deadline):
    limit = deadline + NUM_TOL
    return nextafter(limit,-inf) if limit - deadline > NUM_TOL else limit


def prepend(step, tail):
    """Compose a wait-free timing step with a later segment."""
    limit = min(start_limit(step.start_deadline),
                step.end_deadline + NUM_TOL - step.duration, tail.latest - step.duration)
    return Envelope(
        step.travel + step.duration + tail.offset,
        max(step.ready + step.duration + tail.offset, tail.floor),
        limit - step.travel,
        tail.feasible_floor and step.ready <= limit,
    )


def segment(steps):
    tail = Envelope()
    for step in reversed(steps):
        tail = prepend(step, tail)
    return tail


def one_visit_clock(timing):
    """Return exact cap (None for empty) and the return envelope (a,b)."""
    if len(timing.mus) != 1:
        raise ValueError("One stochastic visit required")
    a, b, cap, feasible = -inf, 0.0, inf, True
    for step in timing.steps:
        a += step.travel
        b = max(b + step.travel, step.ready)
        if step.slot is not None:
            a, b = b, -inf
        deadline = start_limit(step.start_deadline)
        feasible &= b <= deadline
        if a != -inf:
            cap = min(cap, deadline - a)
        a += step.duration
        b += step.duration
        feasible &= b <= step.end_deadline + NUM_TOL
        if a != -inf:
            cap = min(cap, step.end_deadline + NUM_TOL - a)
    return (cap if feasible and cap >= 0 else None), a, b


def backward_cap(timing):
    """Invert each deadline/floor independently of the forward envelope."""
    if len(timing.mus) != 1:
        raise ValueError("One stochastic visit required")
    at = next(i for i, step in enumerate(timing.steps) if step.slot is not None)
    clock = 0.0
    for step in timing.steps[:at]:
        start = max(clock + step.travel, step.ready)
        clock = start + step.duration
        if start > start_limit(step.start_deadline) or clock > step.end_deadline + NUM_TOL:
            return None
    latest = inf
    for step in reversed(timing.steps[at + 1:]):
        limit = min(start_limit(step.start_deadline),
                    min(latest, step.end_deadline + NUM_TOL) - step.duration)
        if step.ready > limit:
            return None
        latest = limit - step.travel
    visit = timing.steps[at]
    cap = min(start_limit(visit.start_deadline),
              min(latest, visit.end_deadline + NUM_TOL) - visit.duration) - max(clock + visit.travel, visit.ready)
    return cap if cap >= 0 else None


def _exp(log_value):
    return exp(log_value) if log_value <= log(np.finfo(float).max) else inf


def lognormal_cdf(cap, mu, sigma):
    if cap is None or cap <= 0:
        return 0.0
    if cap == inf:
        return 1.0
    if sigma == 0:
        return float(_exp(mu) <= cap)
    return float(ndtr((log(cap) - mu) / sigma))


def expected_return(a, b, mu, sigma):
    """Unconditional stop-loss mean with subtraction in the log domain."""
    if sigma == 0:
        return max(a + _exp(mu), b)
    log_mean = mu + sigma * sigma / 2
    k = b - a
    if k <= 0:
        return a + _exp(log_mean)
    log_k = log(k)
    z = (mu - log_k) / sigma
    leading = log_mean + float(log_ndtr(z + sigma))
    deducted = log_k + float(log_ndtr(z))
    # At numerical equality the positive difference is below log-domain precision.
    if deducted >= leading:
        return b
    difference = deducted - leading
    factor = log(-float(np.expm1(difference))) if difference > -0.6931471805599453 else log1p(-exp(difference))
    return b + _exp(leading + factor)


def analytic(timing):
    if not len(timing.mus):
        success, clock = timing.evaluate(np.empty((1, 0)))
        return {"probability": float(success[0]), "mean_completion": float(clock[0]), "cap": None}
    cap, a, b = one_visit_clock(timing)
    mu, sigma = map(float, (timing.mus[0], timing.sigmas[0]))
    return {"probability": lognormal_cdf(cap, mu, sigma), "mean_completion": expected_return(a, b, mu, sigma),
            "cap": None if cap == inf else cap, "infinite_cap": cap == inf}


def minimum_charge(e_pre, e_post, capacity, *, tolerance=0.0):
    if max(e_pre, e_post) > capacity + tolerance:
        return None
    return max(0.0, e_pre + e_post - capacity - tolerance)


def _prefer(challenger, incumbent, target, probability_tol, clock_tol):
    if incumbent is None:
        return True
    p, clock = challenger
    old_p, old_clock = incumbent
    if (p >= target) != (old_p >= target):
        return p >= target
    if p >= target:
        return clock < old_clock - clock_tol or (abs(clock - old_clock) <= clock_tol and p > old_p + probability_tol)
    return p > old_p + probability_tol or (abs(p - old_p) <= probability_tol and clock < old_clock - clock_tol)


def exhaustive(instance, source, physics, *, target, probability_tol, clock_tol):
    """Enumerate the full zero/one-visit domain via O(1) gap timing checks."""
    if physics.enforce_station_time_windows:
        raise ValueError("Restricted optimizer assumes station operating windows disabled")
    start, cpu = perf_counter(), process_time()
    ids = [0, *customer_node_ids(instance, source), 0]
    indices = np.array([instance.index_of(node) for node in ids])
    matrix = instance.distance_matrix
    legs = matrix[indices[:-1], indices[1:]]
    distance = np.r_[0.0, np.cumsum(legs)]
    steps = [TimingStep(float(leg), node.ready_time, node.service_time, node.due_date, inf, None)
             for leg, node in zip(legs[:-1], (instance.node(key) for key in ids[1:-1]), strict=True)]
    steps.append(TimingStep(float(legs[-1]), -inf, 0.0, inf, instance.depot_closing_time, None))
    prefix, valid = [0.0], [True]
    for step in steps:
        begin = max(prefix[-1] + step.travel, step.ready)
        prefix.append(begin + step.duration)
        valid.append(valid[-1] and begin <= start_limit(step.start_deadline) and prefix[-1] <= step.end_deadline + NUM_TOL)
    tails = [Envelope()] * len(ids)
    for i in range(len(steps) - 1, -1, -1):
        tails[i] = prepend(steps[i], tails[i + 1])
    plain = Route(source.route_id, source.customer_indices, [RouteStop(i) for i in ids])
    trace = simulate_route_fixed(instance, plain, physics)
    best = plain if trace.feasible else None
    score = (1.0, trace.end_clock) if trace.feasible else None
    visits = sorted(instance.station_node_ids)
    station_indices = [instance.index_of(s) for s in visits]
    h, capacity = physics.energy_consumption_rate, physics.battery_capacity
    tally = {"total": 1 + len(legs)*len(visits), "energy_rejected": 0, "timing_rejected": 0,
             "evaluated": int(trace.feasible), "numeric_checks": 0}
    if not trace.feasible:
        tally["energy_rejected" if distance[-1]*h > capacity + NUM_TOL else "timing_rejected"] += 1
    for i in range(len(legs)):
        direct = steps[i]
        later = tails[i+1]
        for station, index in zip(visits, station_indices, strict=True):
            incoming, outgoing = float(matrix[indices[i], index]), float(matrix[index, indices[i+1]])
            pre = h * (distance[i] + incoming)
            post = h * (outgoing + distance[-1] - distance[i+1])
            # Screen with tolerance. Replay boundary cases with the frozen battery arithmetic.
            if max(pre, post) > capacity + NUM_TOL + 1e-10:
                tally["energy_rejected"] += 1
                continue
            amount = minimum_charge(pre, post, capacity)
            rate = instance.charging_rate(station)
            near = min(abs(pre-capacity), abs(post-capacity), abs(amount-NUM_TOL)) <= 2*NUM_TOL
            near |= pre + post >= capacity and amount > 0
            # In the active-energy regime use a compiled float64 cumulative subtraction
            # equivalent to legwise decrements to find the least charge allowed by NUM_TOL.
            if near:
                original_legs = matrix[indices[:i], indices[1:i+1]]
                battery = float(np.subtract.accumulate(np.r_[capacity, h*original_legs, h*incoming])[-1])
                rest = h * np.r_[outgoing, legs[i+1:]]
                need = float(np.add.accumulate(rest[::-1])[-1])
                amount = max(0.0, need - battery - NUM_TOL + 1e-11)
                amount = min(amount, max(0., capacity - battery + NUM_TOL))
            after = prefix[i] + incoming + (amount/rate if amount > NUM_TOL else 0.0)
            tail = prepend(TimingStep(outgoing, direct.ready, direct.duration, direct.start_deadline,
                                      direct.end_deadline, None), later)
            cap = tail.latest - after
            if not valid[i] or not tail.feasible_floor or cap < -1e-10:
                tally["timing_rejected"] += 1
                continue
            candidate = None
            if near or abs(cap) <= 1e-10:
                tally["numeric_checks"] += 1
                candidate = Route(source.route_id, source.customer_indices,
                                  plain.stops[:i+1]+[RouteStop(station, amount)]+plain.stops[i+1:])
                checked = simulate_route_fixed(instance,candidate,physics)
                if not checked.feasible:
                    tally["energy_rejected" if checked.failure_reason in ("battery","overcharge","insufficient_energy")
                          or "energy" in checked.failure_reason or "battery" in checked.failure_reason else "timing_rejected"] += 1
                    continue
            attr = instance.station_attributes[station]
            if candidate is not None:
                exact = analytic(RouteTiming.from_trace(instance, checked, physics))
                candidate_score = exact["probability"],exact["mean_completion"]
            else:
                candidate_score = (lognormal_cdf(max(0.,cap),attr.wait_mu,attr.wait_sigma),
                                   expected_return(after+tail.offset,tail.floor,attr.wait_mu,attr.wait_sigma))
            tally["evaluated"] += 1
            if _prefer(candidate_score,score,target,probability_tol,clock_tol):
                score = candidate_score
                best = candidate or Route(source.route_id,source.customer_indices,
                                          plain.stops[:i+1]+[RouteStop(station,amount)]+plain.stops[i+1:])
    if best is None:
        return None, {**tally,"status":"no_feasible_restricted_plan","wall_s":perf_counter()-start,"cpu_s":process_time()-cpu}
    trace = validate_repair(instance,source,best,physics)
    exact = analytic(RouteTiming.from_trace(instance,trace,physics))
    if abs(score[0]-exact["probability"]) > 1e-10 or abs(score[1]-exact["mean_completion"]) > 1e-8:
        raise ValueError("AS1 max-plus replay disagrees with candidate scoring")
    return best, {**tally,"status":"exhaustive","wall_s":perf_counter()-start,"cpu_s":process_time()-cpu,**exact}
