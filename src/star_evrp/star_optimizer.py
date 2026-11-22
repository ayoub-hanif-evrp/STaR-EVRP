"""STaR_v1 charging-only stochastic repair optimizer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
from star_evrp.criticality import gap_priorities, station_criticalities
from star_evrp.route_evaluator import RouteEvaluator
from star_evrp.safe_screen import ScreenMode, screen_candidate
from star_evrp.search_common import SearchCandidate, is_better_incumbent, meets_target_estimate
from star_evrp.statistics import lognormal_mean
from star_evrp.types import Instance, NodeType, Route
from star_evrp.deterministic_simulator import SimulatorConfig


@dataclass
class STaRConfig:
    target_reliability: float = 0.95
    master_seed: int = 20261122
    use_certified_reject: bool = True
    use_criticality: bool = True
    use_progressive: bool = True
    allow_partial_charge: bool = True
    allow_multi_edit: bool = True
    nearby_stations: int = 5
    budget: BudgetConfig = field(default_factory=BudgetConfig)


@dataclass
class STaRReport:
    method: str = "STaR_v1"
    incumbent: SearchCandidate | None = None
    candidates_examined: int = 0
    screen_rejects: int = 0
    budget: dict[str, Any] = field(default_factory=dict)
    notes: str = ""


def _nearest_alt_stations(instance: Instance, station_id: int, k: int) -> list[int]:
    dist = instance.distance_matrix
    si = instance.index_of(station_id)
    scores: list[tuple[float, int]] = []
    for sid in instance.station_node_ids:
        if sid == station_id:
            continue
        sj = instance.index_of(sid)
        scores.append((float(dist[si, sj]), sid))
    scores.sort(key=lambda t: t[0])
    return [sid for _, sid in scores[:k]]


def _cheap_score(instance: Instance, route: Route) -> float:
    total = 0.0
    for stop in route.stops or []:
        if instance.node(stop.node_id).node_type == NodeType.STATION:
            att = instance.station_attributes[stop.node_id]
            total += lognormal_mean(att.wait_mu, att.wait_sigma)
    return total


def optimize_route_star(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    star_cfg: STaRConfig | None = None,
) -> STaRReport:
    """Bounded local search on one fixed-customer route."""
    sc = star_cfg or STaRConfig()
    budget = BudgetTracker(sc.budget)
    evaluator = RouteEvaluator(
        instance,
        config,
        sc.master_seed,
        "opt",
        budget=budget,
        progressive_stages=sc.budget.progressive_stages if sc.use_progressive else (sc.budget.validation_scenarios,),
    )
    target = sc.target_reliability
    report = STaRReport()

    def eval_route(r: Route) -> SearchCandidate:
        if sc.use_progressive:
            prog = evaluator.evaluate_progressive(r)
            ev = prog.best_stage or evaluator.evaluate_stochastic(r, sc.budget.progressive_stages[0])
        else:
            ev = evaluator.evaluate_stochastic(r, sc.budget.progressive_stages[-1])
        fp = route_to_charge_plan_stops(instance, r).fingerprint()
        return SearchCandidate(
            route=r,
            det_feasible=ev.det_feasible,
            reliability=ev.reliability,
            e_completion=ev.e_completion,
            scenarios=ev.scenarios,
            meets_target=meets_target_estimate(ev.reliability, target),
            fingerprint=fp,
            method_tag="STaR_v1",
        )

    incumbent = eval_route(route)
    report.candidates_examined = 1
    seen = {incumbent.fingerprint}

    # Candidate pool
    pool: list[Route] = []
    station_idxs = enumerate_station_indices(route, instance)
    if sc.use_criticality:
        crit = station_criticalities(instance, route, config)
        station_idxs = [c.stop_index for c in crit] or station_idxs
        gaps = gap_priorities(instance, route, config)
        gap_list = [g.after_stop_index for g in gaps[:8]]
    else:
        gap_list = list(range(len(route.stops or []) - 1))

    for vi in station_idxs:
        sid = route.stops[vi].node_id  # type: ignore
        for alt in _nearest_alt_stations(instance, sid, sc.nearby_stations):
            mr = replace_station(instance, route, vi, alt, config)
            if mr.feasible and mr.route:
                pool.append(mr.route)
        mr = remove_station(instance, route, vi, config)
        if mr.feasible and mr.route:
            pool.append(mr.route)
        if sc.allow_partial_charge:
            for amt in partial_charge_targets(instance, route, vi, config):
                mr = set_charge_amount(instance, route, vi, amt, config)
                if mr.feasible and mr.route:
                    pool.append(mr.route)

    for gap in gap_list:
        for sid in nearest_reachable_stations(instance, route, gap, config, k=sc.nearby_stations):
            energy: float | None = None
            if sc.allow_partial_charge:
                opts = partial_charge_targets(
                    instance,
                    insert_station(instance, route, gap, sid, None, config).route or route,
                    gap + 1,
                    config,
                )
                for energy in opts[:2]:
                    mr = insert_station(instance, route, gap, sid, energy, config)
                    if mr.feasible and mr.route:
                        pool.append(mr.route)
            else:
                mr = insert_station(instance, route, gap, sid, energy, config)
                if mr.feasible and mr.route:
                    pool.append(mr.route)

    pool.sort(key=lambda r: _cheap_score(instance, r))

    for cand_route in pool:
        if budget.any_exceeded():
            break
        fp = route_to_charge_plan_stops(instance, cand_route).fingerprint()
        if fp in seen:
            continue
        seen.add(fp)

        mode = ScreenMode.CERTIFIED if sc.use_certified_reject else ScreenMode.EXPLORATION
        scr = screen_candidate(instance, cand_route, config, target=target, mode=mode)
        if sc.use_certified_reject and scr.certified_reject and scr.mode == ScreenMode.CERTIFIED:
            report.screen_rejects += 1
            continue

        sc_cand = eval_route(cand_route)
        report.candidates_examined += 1
        if is_better_incumbent(sc_cand, incumbent, target=target):
            incumbent = sc_cand

        if sc.allow_multi_edit and not budget.any_exceeded():
            # one bounded two-edit: replace + charge tweak on same route
            for vi2 in enumerate_station_indices(cand_route, instance)[:2]:
                for amt in partial_charge_targets(instance, cand_route, vi2, config)[:1]:
                    mr2 = set_charge_amount(instance, cand_route, vi2, amt, config)
                    if not mr2.feasible or not mr2.route:
                        continue
                    fp2 = route_to_charge_plan_stops(instance, mr2.route).fingerprint()
                    if fp2 in seen:
                        continue
                    seen.add(fp2)
                    sc2 = eval_route(mr2.route)
                    report.candidates_examined += 1
                    if is_better_incumbent(sc2, incumbent, target=target):
                        incumbent = sc2

    report.incumbent = incumbent
    report.budget = budget.to_dict()
    if incumbent and not incumbent.meets_target:
        report.notes = "below_target_incumbent"
    return report