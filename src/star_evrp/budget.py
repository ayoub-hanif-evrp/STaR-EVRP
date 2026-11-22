"""Computation budget caps for Phase-2 search."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class BudgetConfig:
    wall_seconds: float = 120.0
    max_candidate_evals: int = 200
    max_scenario_evals: int = 50_000
    progressive_stages: tuple[int, ...] = (64, 256, 1024)
    validation_scenarios: int = 5000


@dataclass
class BudgetTracker:
    """Monotonic counters; all methods share one tracker for fair comparison."""

    config: BudgetConfig
    t0: float = field(default_factory=time.perf_counter)
    candidates_evaluated: int = 0
    scenarios_evaluated: int = 0
    cache_hits: int = 0

    def elapsed(self) -> float:
        return time.perf_counter() - self.t0

    def wall_exceeded(self) -> bool:
        return self.elapsed() >= self.config.wall_seconds

    def candidate_exceeded(self) -> bool:
        return self.candidates_evaluated >= self.config.max_candidate_evals

    def scenario_exceeded(self) -> bool:
        return self.scenarios_evaluated >= self.config.max_scenario_evals

    def any_exceeded(self) -> bool:
        return self.wall_exceeded() or self.candidate_exceeded() or self.scenario_exceeded()

    def charge_candidates(self, n: int = 1) -> None:
        self.candidates_evaluated += n

    def charge_scenarios(self, n: int) -> None:
        self.scenarios_evaluated += n

    def record_cache_hit(self, n: int = 1) -> None:
        self.cache_hits += n

    def remaining_scenarios(self) -> int:
        return max(0, self.config.max_scenario_evals - self.scenarios_evaluated)

    def to_dict(self) -> dict:
        return {
            "wall_seconds_limit": self.config.wall_seconds,
            "elapsed_seconds": self.elapsed(),
            "candidates_evaluated": self.candidates_evaluated,
            "scenarios_evaluated": self.scenarios_evaluated,
            "cache_hits": self.cache_hits,
            "exceeded": self.any_exceeded(),
        }