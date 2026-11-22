"""Criticality scores for prioritizing charging visits and gaps."""

from __future__ import annotations

from dataclasses import dataclass

from scipy import stats

import numpy as np

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.risk_bounds import isolated_wait_threshold_brackets
from star_evrp.types import Instance, NodeType, Route


@dataclass
class VisitCriticality:
    stop_index: int
    station_id: int
    tau_upper: float
    criticality: float
    """``1 - F(tau_upper)`` — prioritization score, not causal failure rate."""


@dataclass
class GapCandidate:
    after_stop_index: int
    score: float


def station_criticalities(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
) -> list[VisitCriticality]:
    trace = simulate_route_fixed(instance, route, config)
    if not trace.feasible:
        return []
    out: list[VisitCriticality] = []
    for i, stop in enumerate(route.stops or []):
        if instance.node(stop.node_id).node_type != NodeType.STATION:
            continue
        _, tau_hi = isolated_wait_threshold_brackets(instance, route, config, i)
        att = instance.station_attributes[stop.node_id]
        sigma = float(att.wait_sigma)
        mu = float(att.wait_mu)
        if sigma <= 0:
            cdf = 1.0 if tau_hi >= float(np.exp(mu)) else 0.0
        else:
            cdf = float(stats.lognorm.cdf(tau_hi, s=sigma, scale=np.exp(mu)))
        crit = max(0.0, 1.0 - cdf)
        out.append(
            VisitCriticality(
                stop_index=i,
                station_id=stop.node_id,
                tau_upper=tau_hi,
                criticality=crit,
            )
        )
    out.sort(key=lambda v: v.criticality, reverse=True)
    return out


def gap_priorities(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
) -> list[GapCandidate]:
    """Rank legal insertion gaps using downstream time-window slack."""
    stops = route.stops or []
    if len(stops) < 2:
        return []
    trace = simulate_route_fixed(instance, route, config)
    if not trace.feasible:
        return []
    slack_by_node: dict[int, float] = {}
    for ts in trace.stops:
        slack_by_node[ts.node_id] = ts.tw_slack_remaining

    gaps: list[GapCandidate] = []
    for j in range(len(stops) - 1):
        a, b = stops[j], stops[j + 1]
        sa = slack_by_node.get(a.node_id, 0.0)
        sb = slack_by_node.get(b.node_id, 0.0)
        score = min(sa, sb)
        gaps.append(GapCandidate(after_stop_index=j, score=score))
    gaps.sort(key=lambda g: g.score)
    return gaps