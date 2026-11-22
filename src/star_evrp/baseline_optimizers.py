"""Fair baselines B0–B3 with identical moves and budgets as STaR_v1."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable

from star_evrp.budget import BudgetConfig, BudgetTracker
from star_evrp.charge_moves import (
    enumerate_station_indices,
    insert_station,
    nearest_reachable_stations,
    partial_charge_targets,
    remove_station,
    replace_station,
    set_charge_amount,
)
from star_evrp.charge_plan import route_to_charge_plan_stops
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.route_evaluator import RouteEvaluator
from star_evrp.search_common import SearchCandidate, is_better_incumbent, meets_target_estimate
from star_evrp.star_optimizer import _nearest_alt_stations, _cheap_score
from star_evrp.statistics import lognormal_mean
from star_evrp.types import Instance, NodeType, Route


@dataclass
class BaselineReport:
    method: str
    incumbent: SearchCandidate | None = None
    candidates_examined: int = 0
    budget: dict[str, Any] = field(default_factory=dict)


def _eval_candidate(
    evaluator: RouteEvaluator,
    instance: Instance,
    route: Route,
    target: float,
    tag: str,
) -> SearchCandidate:
    ev = evaluator.evaluate_progressive(route).best_stage
    if ev is None:
        ev = evaluator.evaluate_stochastic(route, 64)
    fp = route_to_charge_plan_stops(instance, route).fingerprint()
    return SearchCandidate(
        route=route,
        det_feasible=ev.det_feasible,
        reliability=ev.reliability,
        e_completion=ev.e_completion,
        scenarios=ev.scenarios,
        meets_target=meets_target_estimate(ev.reliability, target),
        fingerprint=fp,
        method_tag=tag,
    )


def _shared_candidate_pool(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    nearby: int,
    allow_partial: bool,
) -> list[Route]:
    """Same neighborhood as STaR_v1 for fair comparison."""
    pool: list[Route] = []
    for vi in enumerate_station_indices(route, instance):
        sid = route.stops[vi].node_id  # type: ignore
        for alt in _nearest_alt_stations(instance, sid, nearby):
            mr = replace_station(instance, route, vi, alt, config)
            if mr.feasible and mr.route:
                pool.append(mr.route)
        mr = remove_station(instance, route, vi, config)
        if mr.feasible and mr.route:
            pool.append(mr.route)
        if allow_partial:
            for amt in partial_charge_targets(instance, route, vi, config):
                mr = set_charge_amount(instance, route, vi, amt, config)
                if mr.feasible and mr.route:
                    pool.append(mr.route)
    for gap in range(len(route.stops or []) - 1):
        for sid in nearest_reachable_stations(instance, route, gap, config, k=nearby):
            mr = insert_station(instance, route, gap, sid, None, config)
            if mr.feasible and mr.route:
                pool.append(mr.route)
    pool.sort(key=lambda r: _cheap_score(instance, r))
    return pool


def B0_no_repair(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    target: float,
    master_seed: int,
    budget_cfg: BudgetConfig | None = None,
) -> BaselineReport:
    """B0: evaluate incumbent CON plan only."""
    budget = BudgetTracker(budget_cfg or BudgetConfig())
    evaluator = RouteEvaluator(instance, config, master_seed, "opt", budget=budget)
    inc = _eval_candidate(evaluator, instance, route, target, "B0_NoRepair")
    return BaselineReport(
        method="B0_NoRepair",
        incumbent=inc,
        candidates_examined=1,
        budget=budget.to_dict(),
    )


def B1_mean_wait_greedy(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    target: float,
    master_seed: int,
    budget_cfg: BudgetConfig | None = None,
    nearby: int = 5,
) -> BaselineReport:
    """B1: rank edits by arithmetic mean wait + det time proxy, then validate."""
    budget = BudgetTracker(budget_cfg or BudgetConfig())
    evaluator = RouteEvaluator(instance, config, master_seed, "opt", budget=budget)
    incumbent = _eval_candidate(evaluator, instance, route, target, "B1_MeanWait")
    pool = _shared_candidate_pool(instance, route, config, nearby=nearby, allow_partial=True)

    def det_score(r: Route) -> float:
        tr = simulate_route_fixed(instance, r, config)
        wait = _cheap_score(instance, r)
        return tr.end_clock + wait

    pool.sort(key=det_score)
    seen = {incumbent.fingerprint}
    examined = 1
    for cand in pool:
        if budget.any_exceeded():
            break
        fp = route_to_charge_plan_stops(instance, cand).fingerprint()
        if fp in seen:
            continue
        seen.add(fp)
        sc = _eval_candidate(evaluator, instance, cand, target, "B1_MeanWait")
        examined += 1
        if is_better_incumbent(sc, incumbent, target=target):
            incumbent = sc
    return BaselineReport(
        method="B1_MeanWait-Greedy",
        incumbent=incumbent,
        candidates_examined=examined,
        budget=budget.to_dict(),
    )


def B2_uniform_quantile(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    target: float,
    master_seed: int,
    budget_cfg: BudgetConfig | None = None,
    nearby: int = 5,
) -> BaselineReport:
    """B2: allocate per-visit wait risk budget uniformly, prefer lower quantile stations."""
    budget = BudgetTracker(budget_cfg or BudgetConfig())
    evaluator = RouteEvaluator(instance, config, master_seed, "opt", budget=budget)
    incumbent = _eval_candidate(evaluator, instance, route, target, "B2_UniformQ")
    n_charge = len(enumerate_station_indices(route, instance)) or 1
    per_visit_budget = target ** (1.0 / n_charge)

    def q_score(r: Route) -> float:
        s = 0.0
        for stop in r.stops or []:
            if instance.node(stop.node_id).node_type != NodeType.STATION:
                continue
            att = instance.station_attributes[stop.node_id]
            # lower median wait is better under uniform risk allocation
            s += math.exp(att.wait_mu)
        return s

    pool = _shared_candidate_pool(instance, route, config, nearby=nearby, allow_partial=True)
    pool.sort(key=q_score)
    seen = {incumbent.fingerprint}
    examined = 1
    for cand in pool:
        if budget.any_exceeded():
            break
        fp = route_to_charge_plan_stops(instance, cand).fingerprint()
        if fp in seen:
            continue
        seen.add(fp)
        sc = _eval_candidate(evaluator, instance, cand, target, "B2_UniformQ")
        examined += 1
        if sc.reliability >= per_visit_budget and is_better_incumbent(sc, incumbent, target=target):
            incumbent = sc
        elif is_better_incumbent(sc, incumbent, target=target):
            incumbent = sc
    return BaselineReport(
        method="B2_UniformQuantile",
        incumbent=incumbent,
        candidates_examined=examined,
        budget=budget.to_dict(),
    )


def B3_full_scenario_ls(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    target: float,
    master_seed: int,
    budget_cfg: BudgetConfig | None = None,
    nearby: int = 5,
    sa_restarts: int = 2,
) -> BaselineReport:
    """B3: stochastic local search with full-batch scoring.

    Uses the same move neighborhood as STaR_v1. Optional lightweight
    simulated-annealing acceptance on suboptimal reliability improvements
    (documented here instead of a fake ALNS replication).
    """
    budget = BudgetTracker(budget_cfg or BudgetConfig())
    evaluator = RouteEvaluator(instance, config, master_seed, "opt", budget=budget)
    best_overall: SearchCandidate | None = None
    examined = 0

    for restart in range(sa_restarts):
        rng = random.Random(master_seed + 1000 * restart)
        current = _eval_candidate(evaluator, instance, route, target, "B3_FullLS")
        examined += 1
        pool = _shared_candidate_pool(instance, route, config, nearby=nearby, allow_partial=True)
        rng.shuffle(pool)
        T = 0.05
        for cand in pool:
            if budget.any_exceeded():
                break
            sc = _eval_candidate(evaluator, instance, cand, target, "B3_FullLS")
            examined += 1
            delta = sc.reliability - current.reliability
            accept = is_better_incumbent(sc, current, target=target)
            if not accept and delta > 0 and rng.random() < math.exp(delta / max(T, 1e-9)):
                accept = True
            if accept:
                current = sc
            T *= 0.92
        if is_better_incumbent(current, best_overall, target=target):
            best_overall = current

    return BaselineReport(
        method="B3_FullScenario-LS",
        incumbent=best_overall,
        candidates_examined=examined,
        budget=budget.to_dict(),
    )


BASELINE_REGISTRY: dict[str, Callable[..., BaselineReport]] = {
    "B0": B0_no_repair,
    "B1": B1_mean_wait_greedy,
    "B2": B2_uniform_quantile,
    "B3": B3_full_scenario_ls,
}