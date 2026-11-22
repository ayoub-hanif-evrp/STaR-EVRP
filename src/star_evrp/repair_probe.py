"""Limited charging-repair opportunity probe (not full STaR)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.results_io import save_json
from star_evrp.stochastic_simulator import simulate_route_stochastic
from star_evrp.types import Instance, NodeType, Route, RouteStop, Solution


@dataclass
class RepairCandidate:
    route_id: int
    candidate_id: str
    action: str
    description: str
    det_feasible: bool
    reliability: float | None = None
    baseline_reliability: float | None = None
    e_completion: float | None = None
    failure_reason: str | None = None


@dataclass
class RepairProbeReport:
    instance_key: str
    variant: str
    routes_examined: int
    candidates: list[RepairCandidate] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_key": self.instance_key,
            "variant": self.variant,
            "routes_examined": self.routes_examined,
            "candidates": [c.__dict__ for c in self.candidates],
            "summary": self.summary,
        }


def _customer_sequence(instance: Instance, route: Route) -> list[int]:
    if route.customer_indices is not None:
        return list(route.customer_indices)
    return [
        instance.customer_local_index(s.node_id)
        for s in route.stops or []
        if instance.node(s.node_id).node_type == NodeType.CUSTOMER
    ]


def _nearest_stations(
    instance: Instance,
    station_id: int,
    k: int = 5,
) -> list[int]:
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


def _replace_station_visit(
    route: Route,
    visit_index: int,
    new_station_id: int,
) -> Route:
    stops = deepcopy(route.stops or [])
    old = stops[visit_index]
    stops[visit_index] = RouteStop(
        node_id=new_station_id,
        energy_charged=old.energy_charged,
        wait_extra=0.0,
    )
    return Route(route_id=route.route_id, stops=stops, customer_indices=route.customer_indices)


def _remove_station_visit(route: Route, visit_index: int) -> Route:
    stops = [deepcopy(s) for s in route.stops or []]
    del stops[visit_index]
    return Route(route_id=route.route_id, stops=stops, customer_indices=route.customer_indices)


def run_repair_probe(
    instance: Instance,
    solution: Solution,
    config: SimulatorConfig,
    *,
    unreliable_route_ids: list[int] | None = None,
    max_routes: int = 40,
    nearby_stations: int = 5,
    diagnostic_scenarios: int = 500,
    master_seed: int = 0,
    target_reliability: float = 0.95,
) -> RepairProbeReport:
    """Probe single-station replacements for unreliable charging routes."""
    report = RepairProbeReport(
        instance_key=instance.instance_key,
        variant=instance.variant,
        routes_examined=0,
    )

    routes = [r for r in solution.routes if r.stops]
    selected: list[Route] = []
    for route in routes:
        station_visits = [
            i
            for i, s in enumerate(route.stops or [])
            if instance.node(s.node_id).node_type == NodeType.STATION
        ]
        if not station_visits:
            continue
        base_m = simulate_route_stochastic(
            instance,
            route,
            config,
            num_scenarios=min(200, diagnostic_scenarios),
            master_seed=master_seed,
        )
        if unreliable_route_ids is not None and route.route_id not in unreliable_route_ids:
            if base_m.reliability >= target_reliability:
                continue
        elif base_m.reliability >= target_reliability:
            continue
        selected.append(route)
        if len(selected) >= max_routes:
            break

    report.routes_examined = len(selected)
    n_with_alt = 0
    n_improved_candidates = 0
    n_meet_target_candidates = 0
    routes_improved: set[int] = set()
    routes_meeting: set[int] = set()
    best_improvements: list[float] = []

    for route in selected:
        # Matched seed stream per route; candidate waits use same Z via shared seed
        # but station-specific (mu, sigma) through simulate_route_stochastic (no cross-station wait_matrix reuse).
        baseline = simulate_route_stochastic(
            instance,
            route,
            config,
            num_scenarios=diagnostic_scenarios,
            master_seed=master_seed,
        )
        report.candidates.append(
            RepairCandidate(
                route_id=route.route_id,
                candidate_id=f"r{route.route_id}_baseline",
                action="baseline",
                description="unchanged route",
                det_feasible=baseline.det_feasible,
                reliability=baseline.reliability,
                baseline_reliability=baseline.reliability,
                e_completion=baseline.e_completion,
            )
        )

        station_visits = [
            (i, s.node_id)
            for i, s in enumerate(route.stops or [])
            if instance.node(s.node_id).node_type == NodeType.STATION
        ]
        route_had_alt = False
        for visit_idx, sid in station_visits:
            for alt_id in _nearest_stations(instance, sid, nearby_stations):
                cand = _replace_station_visit(route, visit_idx, alt_id)
                tr = simulate_route_fixed(instance, cand, config)
                stoch: float | None = None
                if tr.feasible:
                    route_had_alt = True
                    m = simulate_route_stochastic(
                        instance,
                        cand,
                        config,
                        num_scenarios=diagnostic_scenarios,
                        master_seed=master_seed + 17 * route.route_id + visit_idx,
                    )
                    stoch = m.reliability
                    if baseline.reliability is not None and stoch > baseline.reliability + 1e-6:
                        n_improved_candidates += 1
                        routes_improved.add(route.route_id)
                        best_improvements.append(stoch - baseline.reliability)
                    if stoch is not None and stoch >= target_reliability:
                        n_meet_target_candidates += 1
                        routes_meeting.add(route.route_id)
                report.candidates.append(
                    RepairCandidate(
                        route_id=route.route_id,
                        candidate_id=f"r{route.route_id}_rep_{visit_idx}_{alt_id}",
                        action="replace_station",
                        description=f"visit {visit_idx}: {sid} -> {alt_id}",
                        det_feasible=tr.feasible,
                        reliability=stoch,
                        baseline_reliability=baseline.reliability,
                        e_completion=tr.end_clock if tr.feasible else None,
                        failure_reason=tr.failure_reason,
                    )
                )

            cand_rm = _remove_station_visit(route, visit_idx)
            tr_rm = simulate_route_fixed(instance, cand_rm, config)
            stoch_rm = None
            if tr_rm.feasible:
                route_had_alt = True
                m_rm = simulate_route_stochastic(
                    instance,
                    cand_rm,
                    config,
                    num_scenarios=diagnostic_scenarios,
                    master_seed=master_seed,
                )
                stoch_rm = m_rm.reliability
            report.candidates.append(
                RepairCandidate(
                    route_id=route.route_id,
                    candidate_id=f"r{route.route_id}_rm_{visit_idx}",
                    action="remove_charge",
                    description=f"remove station visit at index {visit_idx}",
                    det_feasible=tr_rm.feasible,
                    reliability=stoch_rm,
                    baseline_reliability=baseline.reliability,
                    failure_reason=tr_rm.failure_reason,
                )
            )

        if route_had_alt:
            n_with_alt += 1

    report.summary = {
        "unreliable_routes_examined": report.routes_examined,
        "routes_with_det_alternative": n_with_alt,
        "routes_with_improvement": len(routes_improved),
        "routes_meeting_target": len(routes_meeting),
        "candidates_improving_reliability": n_improved_candidates,
        "candidates_meeting_target": n_meet_target_candidates,
        "best_reliability_gain": max(best_improvements) if best_improvements else 0.0,
        "diagnostic_scenarios": diagnostic_scenarios,
    }
    return report


def save_repair_probe(path: Path | str, report: RepairProbeReport) -> None:
    save_json(path, report.to_dict())