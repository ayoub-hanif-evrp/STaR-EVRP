"""Bounded sample-average optimization of a fixed ordered charging topology."""

from math import ceil, inf
from time import perf_counter, process_time
import warnings

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_array

from star_evrp.charge_plan import clone_route_stops
from star_evrp.deterministic_simulator import simulate_route_fixed
from star_evrp.phase6_math import minimum_charge, segment
from star_evrp.search_common import SearchCandidate
from star_evrp.timing import RouteTiming
from star_evrp.types import NUM_TOL, Route


def model_components(timing):
    if any(step.ready != -inf or step.start_deadline != inf or step.end_deadline != inf
           for step in timing.steps if step.slot is not None):
        raise ValueError("FT-SAA assumes station hours disabled")
    segments, incoming, current = [], [], []
    for step in timing.steps:
        if step.slot is None:
            current.append(step)
        else:
            segments.append(segment(current))
            incoming.append(step.travel)
            current = []
    segments.append(segment(current))
    return segments, incoming


class ConstraintRows:
    def __init__(self):
        self.rows, self.columns, self.values, self.low, self.high = [], [], [], [], []

    def add(self, terms, low=-inf, high=inf):
        index = len(self.low)
        for col, coef in terms:
            self.rows.append(index)
            self.columns.append(col)
            self.values.append(coef)
        self.low.append(low)
        self.high.append(high)

    def constraint(self, dimensions):
        matrix = coo_array((self.values, (self.rows, self.columns)), shape=(len(self.low), dimensions)).tocsc()
        return LinearConstraint(matrix, self.low, self.high)


def build_milp(timing, rates, energy, capacity, waits):
    """Build baseline, sampled timing and capacity constraints with finite scenario bounds."""
    segment_models, incoming = model_components(timing)
    size, visits = waits.shape
    if any(not block.feasible_floor for block in segment_models):
        raise ValueError("Fixed topology has impossible deterministic floors")
    if len(energy) != visits + 1 or len(rates) != visits or not all(rate > 0 for rate in rates):
        raise ValueError("Bad battery or charging segment model")
    # Row zero carries zero waits; the last variable of each row is the unconditional full return.
    clock_ids = np.arange(visits, visits + (size+1)*(visits+1)).reshape(size+1, visits+1)
    binary_ids = np.arange(clock_ids.max()+1, clock_ids.max()+1+size)
    dimensions = int(binary_ids[-1]+1)
    lower, upper = np.zeros(dimensions), np.zeros(dimensions)
    charge_upper = capacity + 2*NUM_TOL
    upper[:visits] = charge_upper
    upper[binary_ids] = 1
    integer = np.zeros(dimensions)
    integer[binary_ids] = 1
    rows = ConstraintRows()
    consumed = 0.0
    for j in range(visits):
        consumed += energy[j]
        # Arrival and postcharge. Cumulative consumed is monotone inside each leg segment.
        earlier = [(i, 1) for i in range(j)]
        rows.add(earlier, consumed-capacity-NUM_TOL)
        rows.add([*earlier,(j,1)], high=consumed+NUM_TOL)
    rows.add([(i,1) for i in range(visits)], sum(energy)-capacity-NUM_TOL)
    big_m = 0.0
    for i, draw in enumerate(np.vstack((np.zeros(visits), waits))):
        ids = clock_ids[i]
        ceiling = 0.0
        for j, block in enumerate(segment_models):
            previous = [] if j == 0 else [(ids[j-1],1)]
            if np.isfinite(block.latest):
                if i == 0:
                    rows.add(previous, high=block.latest)
                else:
                    padding = max(0.0, ceiling-block.latest)
                    big_m = max(big_m, padding)
                    rows.add([*previous,(binary_ids[i-1],-padding)], high=block.latest)
            if j == visits:
                increment, additional = block.offset, []
            else:
                increment = incoming[j] + draw[j] + block.offset
                additional = [(j, 1/rates[j])]
            rows.add([*previous,*additional,(ids[j],-1)], high=-increment)
            added = 0.0 if j == visits else incoming[j] + draw[j]
            if np.isfinite(block.floor):
                rows.add([*additional,(ids[j],-1)], high=-block.floor-added)
            ceiling = max(ceiling+increment,block.floor+added)
            if j < visits:
                ceiling += charge_upper / rates[j]
            # Include a scale-dependent floating-point cushion in upper bounds and later M.
            ceiling += 1e-12 * max(1., abs(ceiling))
            upper[ids[j]] = ceiling
    completion = np.zeros(dimensions)
    completion[clock_ids[1:,-1]] = 1.0/size
    count_failed = np.zeros(dimensions)
    count_failed[binary_ids] = 1.0
    return rows, Bounds(lower,upper), integer, completion, count_failed, big_m


def _score(instance, route, physics, tape, target):
    trace = simulate_route_fixed(instance,route,physics)
    if not trace.feasible:
        return None
    timing = RouteTiming.from_trace(instance,trace,physics)
    success, full = timing.evaluate(timing.waits(tape))
    wins, completion = int(success.sum()),float(full.mean())
    return SearchCandidate(route,True,wins/len(tape),completion).score_key(target), wins, completion


def fixed_topology(instance, source, fspc, physics, tape, policy, target):
    start,cpu = perf_counter(), process_time()
    source_trace = simulate_route_fixed(instance,source,physics)
    timing = RouteTiming.from_trace(instance,source_trace,physics)
    slots = [i for i,step in enumerate(timing.steps,1) if step.slot is not None]
    rates = [instance.charging_rate(source.stops[i].node_id) for i in slots]
    energy = []
    running = 0.0
    for step in timing.steps:
        running += physics.energy_consumption_rate * step.travel
        if step.slot is not None:
            energy.append(running)
            running = 0.0
    energy.append(running)
    attempts = []
    chosen = None

    def consider(route,label):
        nonlocal chosen
        score = _score(instance,route,physics,tape,target)
        if score is not None and (chosen is None or score[0] > chosen[1][0]):
            chosen = route,score,label
        return score

    def candidate(amounts):
        stops = clone_route_stops(source)
        for i,amount in zip(slots,amounts,strict=True):
            stops[i].energy_charged = max(0.0,float(amount))
        return Route(source.route_id,source.customer_indices,stops)

    consider(source,"CON")
    consider(fspc,"FSPC")
    status, peak_m = "fallback", None
    if len(slots) == 1:
        arrival = source_trace.stops[slots[0]].battery_on_arrival
        amount = minimum_charge(*energy,physics.battery_capacity,tolerance=NUM_TOL)
        oracle = candidate([min(amount+1e-11,physics.battery_capacity-arrival+NUM_TOL)])
        score = consider(oracle,"single_visit_oracle")
        comparator = chosen[1]
        if score is not None and score[1] == comparator[1] and abs(score[2]-comparator[2]) <= 1e-8:
            status = "single_visit_oracle"
        else:
            status = "oracle_replay_fallback"
    else:
        rows,bounds,integrality,completion,failures,peak_m = build_milp(
            timing,rates,energy,physics.battery_capacity,timing.waits(tape))
        maximum_failures = len(tape)-ceil(target*len(tape))

        def solve(name, objective, extra=None):
            remain = policy["solver_seconds"] - (perf_counter()-start)
            if remain <= 0:
                return None,None
            constraints = [rows.constraint(len(completion))]
            if extra is not None:
                constraints.append(extra)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore",message="Unrecognized options detected")
                ans = milp(objective,integrality=integrality,bounds=bounds,constraints=constraints,
                           options={"time_limit":remain, "mip_rel_gap":policy["solver_mip_gap"],
                                    "threads":1,"random_seed":policy["solver_seed"],"mip_feasibility_tolerance":1e-9})
            attempts.append({field: getattr(ans,field,None) for field in
                             ("status","message","fun","mip_gap","mip_dual_bound","mip_node_count")} | {"stage":name})
            score = consider(candidate(ans.x[:len(slots)]),name) if ans.x is not None else None
            if score is not None:
                attempts[-1].update(replay_successes=score[1],replay_completion=score[2],
                                    certified_min_successes=len(tape)-int(round(float(failures@ans.x))))
            return ans,score

        primary, first = solve("target_completion",completion,LinearConstraint(failures,0,maximum_failures))
        if primary is not None and primary.status == 0 and first is not None and first[1] >= len(tape)-maximum_failures:
            if abs(first[2]-primary.fun) <= policy["solver_tie_completion"]:
                tied, _ = solve("target_reliability_tie",failures,
                                LinearConstraint(completion,0,primary.fun+policy["solver_tie_completion"]))
                status = "target_certified" if tied is not None and tied.status == 0 else "target_completion_only"
            else:
                status = "solver_replay_disagreement"
        elif primary is not None and primary.status == 2:
            maximum, max_score = solve("maximize_success",failures)
            if maximum is not None and maximum.status == 0 and max_score is not None and max_score[1] == len(tape)-round(maximum.fun):
                refined, refine_score = solve("best_success_completion",completion,
                                              LinearConstraint(failures,0,round(maximum.fun)))
                if (refined is not None and refined.status == 0 and refine_score is not None
                        and refine_score[1]==max_score[1] and abs(refine_score[2]-refined.fun)<=policy["solver_tie_completion"]):
                    status = "below_target_certified"
                else:
                    status = "best_success_only"
            else:
                status = "replay_or_time_limit"
        elif primary is not None and primary.status == 1:
            status = "time_limit"
        elif primary is not None:
            status = "replay_or_solver_failure"
    route, (_, wins, clock), provenance = chosen
    return route, {"status":status,"origin":provenance,"attempts":attempts,"max_big_m":peak_m,
                   "work_tape":len(tape),"opt_successes":wins,"opt_completion":clock,
                   "elapsed_s":perf_counter()-start,"cpu_s":process_time()-cpu,"visits":len(slots)}
