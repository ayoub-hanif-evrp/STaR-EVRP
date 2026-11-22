"""Deterministic checks and tape-driven stochastic evaluation with caching."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from star_evrp.budget import BudgetTracker
from star_evrp.charge_plan import route_to_charge_plan_stops
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.scenario_tapes import ScenarioSplit, waits_from_z, z_tape_for_route
from star_evrp.stochastic_simulator import evaluate_route_with_waits
from star_evrp.statistics import wilson_ci
from star_evrp.types import Instance, Route


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


class RouteEvaluator:
    """Evaluate routes under matched scenario tapes."""

    def __init__(
        self,
        instance: Instance,
        config: SimulatorConfig,
        master_seed: int,
        split: ScenarioSplit,
        budget: BudgetTracker | None = None,
        progressive_stages: tuple[int, ...] = (64, 256, 1024),
    ) -> None:
        self.instance = instance
        self.config = config
        self.master_seed = master_seed
        self.split = split
        self.budget = budget
        self.progressive_stages = progressive_stages
        self._cache: dict[tuple[str, int], StochasticEvalResult] = {}
        self._base_z: np.ndarray | None = None
        self._base_z_cap: int = 0

    def _fingerprint(self, route: Route) -> str:
        return route_to_charge_plan_stops(self.instance, route).fingerprint()

    def det_check(self, route: Route) -> bool:
        return simulate_route_fixed(self.instance, route, self.config).feasible

    def _ensure_z_tape(self, route: Route, min_cols: int) -> np.ndarray:
        need = max(min_cols, self._base_z_cap)
        if self._base_z is None or self._base_z.shape[1] < need:
            self._base_z = z_tape_for_route(
                self.master_seed,
                self.instance,
                route,
                self.split,
                num_scenarios=10_000,
                max_slots=need,
            )
            self._base_z_cap = int(self._base_z.shape[1])
        return self._base_z

    def evaluate_stochastic(
        self,
        route: Route,
        num_scenarios: int,
        *,
        use_cache: bool = True,
    ) -> StochasticEvalResult:
        fp = self._fingerprint(route)
        key = (fp, num_scenarios)
        if use_cache and key in self._cache:
            hit = self._cache[key]
            hit.from_cache = True
            if self.budget:
                self.budget.record_cache_hit()
            return hit

        det_ok = self.det_check(route)
        if not det_ok:
            res = StochasticEvalResult(
                det_feasible=False,
                reliability=0.0,
                e_completion=0.0,
                successes=0,
                scenarios=num_scenarios,
                wilson_ci_low=0.0,
                wilson_ci_high=0.0,
            )
            self._cache[key] = res
            return res

        if self.budget and self.budget.scenario_exceeded():
            return StochasticEvalResult(
                det_feasible=True,
                reliability=0.0,
                e_completion=0.0,
                successes=0,
                scenarios=0,
                wilson_ci_low=0.0,
                wilson_ci_high=0.0,
            )

        z = self._ensure_z_tape(route, num_scenarios)
        waits = waits_from_z(self.instance, route, z[:num_scenarios])
        Q = float(self.config.battery_capacity)
        h = float(self.config.energy_consumption_rate)
        enforce = bool(self.config.enforce_station_time_windows)

        successes = 0
        completions: list[float] = []
        for k in range(num_scenarios):
            out = evaluate_route_with_waits(
                self.instance,
                route,
                waits[k],
                Q=Q,
                h=h,
                enforce_station_time_windows=enforce,
            )
            completions.append(out.completion)
            if out.success:
                successes += 1

        if self.budget:
            self.budget.charge_scenarios(num_scenarios)
            self.budget.charge_candidates(1)

        rel = successes / num_scenarios if num_scenarios > 0 else 0.0
        ci = wilson_ci(successes, num_scenarios)
        res = StochasticEvalResult(
            det_feasible=True,
            reliability=rel,
            e_completion=float(np.mean(completions)) if completions else 0.0,
            successes=successes,
            scenarios=num_scenarios,
            wilson_ci_low=ci[0],
            wilson_ci_high=ci[1],
        )
        self._cache[key] = res
        return res

    def evaluate_progressive(
        self,
        route: Route,
        *,
        stages: tuple[int, ...] | None = None,
        min_reliability: float | None = None,
    ) -> ProgressiveResult:
        st = stages or self.progressive_stages
        results: list[StochasticEvalResult] = []
        passed = True
        for n in st:
            if self.budget and self.budget.any_exceeded():
                break
            ev = self.evaluate_stochastic(route, n)
            results.append(ev)
            if min_reliability is not None and ev.reliability < min_reliability:
                passed = False
                break
        best = results[-1] if results else None
        return ProgressiveResult(passed=passed, stages=results, best_stage=best)