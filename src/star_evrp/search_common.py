"""Lexicographic incumbent policy shared by STaR and baselines."""

from __future__ import annotations

from dataclasses import dataclass

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.types import Instance, Route


@dataclass
class SearchCandidate:
    route: Route
    det_feasible: bool
    reliability: float
    e_completion: float
    scenarios: int = 0
    meets_target: bool = False
    fingerprint: str = ""
    method_tag: str = ""

    def score_key(self, target: float) -> tuple:
        """Higher is better (for max selection)."""
        valid = 1 if self.det_feasible else 0
        if valid and self.reliability >= target:
            return (valid, 1, -self.e_completion, self.reliability)
        return (valid, 0, self.reliability, -self.e_completion)


def det_feasible(instance: Instance, route: Route, config: SimulatorConfig) -> bool:
    return simulate_route_fixed(instance, route, config).feasible


def meets_target_estimate(reliability: float, target: float, margin: float = 0.0) -> bool:
    return reliability >= target - margin


def is_better_incumbent(
    challenger: SearchCandidate,
    incumbent: SearchCandidate | None,
    *,
    target: float,
) -> bool:
    if incumbent is None:
        return challenger.det_feasible or challenger.reliability > 0
    return challenger.score_key(target) > incumbent.score_key(target)


def select_best(
    candidates: list[SearchCandidate],
    *,
    target: float,
) -> SearchCandidate | None:
    best: SearchCandidate | None = None
    for c in candidates:
        if is_better_incumbent(c, best, target=target):
            best = c
    return best
