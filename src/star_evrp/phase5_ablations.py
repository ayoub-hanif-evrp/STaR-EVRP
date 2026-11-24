"""Isolated one-switch variants of frozen STaR's search loop."""

from time import perf_counter

from star_evrp.budget import BudgetTracker
from star_evrp.charge_plan import ChargePlan
from star_evrp.competitive_search import Neighborhood, SearchResult, _score
from star_evrp.route_evaluator import RouteEvaluator


def optimize_component(instance, config, original, budget, *, seed, samples, target=.95, nearby=3,
                       prioritize=True, analytical=True, prefix=True):
    tracker = BudgetTracker(budget)
    evaluator = RouteEvaluator(instance, config, seed, "opt", budget=tracker)
    current = original
    current_entry = evaluator.prepare(current)
    if current_entry is None or not current_entry.trace.feasible:
        raise ValueError("Infeasible CON starting plan or insufficient starting budget")
    history = []
    rejected = prefix_rejected = 0

    def score(route, entry):
        if not evaluator.extend(route, entry, samples):
            return None
        return _score(route, float(entry.success.mean()), float(entry.completion.mean()), target)

    best = score(current, current_entry)
    if best is None:
        raise ValueError("Budget too small to score source plan")
    target_time = tracker.elapsed() if best[1] == 1 else None
    neighborhood = Neighborhood(instance, config, nearby)
    seen = {ChargePlan.from_route(instance, current)}
    generation_cap = 10 * budget.max_candidate_evals
    while not tracker.any_exceeded() and tracker.generated < generation_cap:
        proposals = neighborhood.proposals(
            current, current_entry, partial=True, topology=True, critical=prioritize)
        improved = False
        while not tracker.any_exceeded() and tracker.generated < generation_cap:
            started = perf_counter()
            try:
                move, candidate = next(proposals)
            except StopIteration:
                tracker.generation_seconds += perf_counter() - started
                break
            tracker.generated += 1
            tracker.generation_seconds += perf_counter() - started
            if candidate is None or tracker.wall_exceeded():
                continue
            identity = ChargePlan.from_route(instance, candidate)
            if identity in seen:
                tracker.record_cache_hit()
                continue
            seen.add(identity)
            entry = evaluator.prepare(candidate)
            if entry is None or not entry.trace.feasible or tracker.wall_exceeded():
                continue
            if analytical and best[1] == 1:
                started = perf_counter()
                bounds = entry.timing.marginal_bounds(entry.trace)
                tracker.screen_checks += 1
                tracker.screening_seconds += perf_counter() - started
                if bounds.min(initial=1.0) < target - 1e-12:
                    rejected += 1
                    continue
            if prefix and samples >= 128:
                initial = samples // 4
                if not evaluator.extend(candidate, entry, initial):
                    continue
                upper = (int(entry.success.sum()) + samples - initial) / samples
                lower = (entry.completion.sum() + (samples - initial) * entry.trace.end_clock) / samples
                optimistic = _score(candidate, upper, float(lower - 1e-8), target)
                if optimistic <= best:
                    prefix_rejected += 1
                    continue
            challenger = score(candidate, entry)
            if challenger is not None and not tracker.wall_exceeded() and challenger > best:
                best, current, current_entry = challenger, candidate, entry
                history.append(move)
                if best[1] == 1 and target_time is None:
                    target_time = tracker.elapsed()
                improved = True
                break
        if not improved:
            break
    return SearchResult(current, best, tracker.to_dict(), history, rejected, prefix_rejected, target_time)
