"""Plan validation, stable common random numbers, and incremental evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

import numpy as np

from star_evrp.budget import BudgetTracker
from star_evrp.charge_plan import ChargePlan
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.scenario_tapes import ScenarioSplit, z_tape_for_route
from star_evrp.statistics import wilson_ci
from star_evrp.timing import RouteTiming
from star_evrp.types import Instance, Route, RouteTrace


@dataclass
class StochasticEvalResult:
    det_feasible: bool
    reliability: float
    e_completion: float
    successes: int
    scenarios: int
    wilson_ci_low: float
    wilson_ci_high: float
    from_cache: bool = False


@dataclass
class ProgressiveResult:
    passed: bool
    stages: list[StochasticEvalResult] = field(default_factory=list)
    best_stage: StochasticEvalResult | None = None


@dataclass
class PlanEvaluation:
    trace: RouteTrace
    timing: RouteTiming | None
    success: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=bool))
    completion: np.ndarray = field(default_factory=lambda: np.empty(0))


class RouteEvaluator:
    def __init__(
        self, instance: Instance, config: SimulatorConfig, master_seed: int, split: ScenarioSplit,
        budget: BudgetTracker | None = None, progressive_stages: tuple[int, ...] = (64, 256, 1024),
    ) -> None:
        self.instance, self.config, self.master_seed, self.split = instance, config, master_seed, split
        self.budget, self.progressive_stages = budget, progressive_stages
        self._plans: dict[tuple[int, ChargePlan], PlanEvaluation] = {}
        self._tapes: dict[int, np.ndarray] = {}

    def prepare(self, route: Route) -> PlanEvaluation | None:
        key = route.route_id, ChargePlan.from_route(self.instance, route)
        if key in self._plans:
            if self.budget:
                self.budget.record_cache_hit()
            return self._plans[key]
        if self.budget and (self.budget.wall_exceeded() or self.budget.candidate_exceeded()):
            return None
        start = perf_counter()
        if any(stop.wait_extra for stop in route.stops or []):
            raise ValueError("Stochastic plans must not contain prefilled waits")
        trace = simulate_route_fixed(self.instance, route, self.config)
        timing = RouteTiming.from_trace(self.instance, trace, self.config) if trace.feasible else None
        entry = self._plans[key] = PlanEvaluation(trace, timing)
        if self.budget:
            self.budget.charge_candidates()
            self.budget.deterministic_checks += 1
            self.budget.deterministic_seconds += perf_counter() - start
        return entry

    def _ensure_z_tape(self, route: Route, rows: int, cols: int) -> np.ndarray:
        tape = self._tapes.get(route.route_id)
        if tape is None or tape.shape[0] < rows or tape.shape[1] < cols:
            tape = z_tape_for_route(
                self.master_seed, self.instance, route, self.split,
                max(rows, 0 if tape is None else tape.shape[0]),
                max_slots=max(cols, 0 if tape is None else tape.shape[1]),
            )
            self._tapes[route.route_id] = tape
        return tape

    def extend(self, route: Route, entry: PlanEvaluation, count: int) -> bool:
        previous = len(entry.success)
        extra = count - previous
        if extra <= 0:
            return True
        if entry.timing is None or (
            self.budget and (self.budget.wall_exceeded() or extra > self.budget.remaining_scenarios())
        ):
            return False
        start = perf_counter()
        tape = self._ensure_z_tape(route, count, len(entry.timing.mus))
        success, completion = entry.timing.evaluate(entry.timing.waits(tape[previous:count]))
        entry.success = np.concatenate((entry.success, success))
        entry.completion = np.concatenate((entry.completion, completion))
        if self.budget:
            self.budget.charge_scenarios(extra)
            self.budget.simulation_seconds += perf_counter() - start
        return True

    def evaluate_stochastic(
        self, route: Route, num_scenarios: int, *, use_cache: bool = True,
    ) -> StochasticEvalResult:
        if not use_cache:
            self._plans.pop((route.route_id, ChargePlan.from_route(self.instance, route)), None)
        entry = self.prepare(route)
        if entry is None or not self.extend(route, entry, num_scenarios):
            return StochasticEvalResult(False, 0.0, float("inf"), 0, 0, 0.0, 1.0)
        wins = int(entry.success[:num_scenarios].sum())
        count = min(num_scenarios, len(entry.success))
        low, high = wilson_ci(wins, count)
        return StochasticEvalResult(
            entry.trace.feasible, wins / count if count else 0.0,
            float(entry.completion[:count].mean()) if count else float("inf"), wins, count, low, high,
        )

    def evaluate_progressive(
        self, route: Route, *, stages: tuple[int, ...] | None = None,
        min_reliability: float | None = None,
    ) -> ProgressiveResult:
        results = []
        passed = True
        for count in stages or self.progressive_stages:
            result = self.evaluate_stochastic(route, count)
            if not result.det_feasible or result.scenarios != count:
                break
            results.append(result)
            if min_reliability is not None and result.reliability < min_reliability:
                passed = False
                break
        return ProgressiveResult(passed, results, results[-1] if results else None)
