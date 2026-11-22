"""Development comparison of fixed-customer charging repair methods."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import chain, zip_longest
from time import perf_counter

import numpy as np

from star_evrp.budget import BudgetConfig, BudgetTracker
from star_evrp.charge_plan import ChargePlan, clone_route_stops
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.geometry import leg_distance
from star_evrp.route_evaluator import PlanEvaluation, RouteEvaluator
from star_evrp.search_common import SearchCandidate
from star_evrp.types import Instance, Route, RouteStop


METHODS = ("B0", "B1", "B2", "B3", "B4", "STaR", "STaR_no_partial")


@dataclass
class SearchResult:
    route: Route
    score: tuple
    budget: dict
    moves: list[str]
    screen_rejections: int
    prefix_rejections: int
    target_time: float | None


class Neighborhood:
    def __init__(self, instance: Instance, config: SimulatorConfig, nearby: int):
        self.instance, self.config, self.nearby = instance, config, nearby
        self.station_ids = set(instance.station_node_ids)
        self.station_nodes = np.array(instance.station_node_ids)
        self.station_rows = np.array([instance.index_of(node) for node in self.station_nodes], dtype=int)

    def positions(self, stops: list[RouteStop]) -> list[int]:
        return [index for index, stop in enumerate(stops) if stop.node_id in self.station_ids]

    def with_stops(self, route: Route, stops: list[RouteStop]) -> Route:
        return Route(route.route_id, route.customer_indices, stops)

    def allocation(self, route: Route, strategy: str) -> Route | None:
        """Rebuild feasible quantities using segment energy and downstream charging speeds."""
        stops = clone_route_stops(route)
        stations = self.positions(stops)
        boundaries = [0, *stations, len(stops) - 1]
        capacity = self.config.battery_capacity
        energy = [
            self.config.energy_consumption_rate * sum(
                leg_distance(self.instance, stops[index].node_id, stops[index + 1].node_id)
                for index in range(left, right)
            )
            for left, right in zip(boundaries, boundaries[1:])
        ]
        if max(energy) > capacity + 1e-9:
            return None
        rates = [self.instance.charging_rate(stops[index].node_id) for index in stations]
        battery = capacity
        for rank, index in enumerate(stations):
            battery = max(0.0, battery - energy[rank])
            reserve = energy[rank + 1]
            if strategy == "full":
                reserve = capacity
            elif strategy == "speed":
                for downstream in range(rank + 1, len(stations)):
                    if rates[downstream] >= rates[rank]:
                        break
                    reserve += energy[downstream + 1]
            amount = max(0.0, min(capacity, reserve) - battery)
            stops[index].energy_charged = amount
            battery += amount
        return self.with_stops(route, stops)

    def alternatives(self, left: int, right: int, excluded: set[int]) -> list[int]:
        matrix = self.instance.distance_matrix
        incoming = matrix[self.instance.index_of(left), self.station_rows]
        outgoing = matrix[self.station_rows, self.instance.index_of(right)]
        max_leg = self.config.battery_capacity
        eligible = (np.maximum(incoming, outgoing) * self.config.energy_consumption_rate <= max_leg + 1e-9)
        ranked = np.argsort(np.where(eligible, incoming + outgoing, np.inf), kind="stable")
        return [
            int(self.station_nodes[index]) for index in ranked
            if eligible[index] and self.station_nodes[index] not in excluded
        ][:self.nearby]

    def topologies(self, current: Route, order: list[int], gaps: list[int]):
        stops = current.stops

        def remove():
            for position in order:
                yield "remove", self.with_stops(current, stops[:position] + stops[position + 1:])

        def replace():
            for position in order:
                left, existing, right = [stop.node_id for stop in stops[position - 1:position + 2]]
                for station in self.alternatives(left, right, {left, right, existing}):
                    yield "replace", self.with_stops(current, stops[:position] + [RouteStop(station)] + stops[position + 1:])

        def insert():
            for gap in gaps:
                left, right = stops[gap].node_id, stops[gap + 1].node_id
                for station in self.alternatives(left, right, {left, right}):
                    yield "insert", self.with_stops(current, stops[:gap + 1] + [RouteStop(station)] + stops[gap + 1:])

        def relocate():
            for gap in gaps:
                for position in order:
                    if gap not in (position - 1, position) and stops[position].node_id not in (
                        stops[gap].node_id, stops[gap + 1].node_id,
                    ):
                        sequence = stops[:position] + stops[position + 1:]
                        index = gap + 1 - int(position <= gap)
                        yield "relocate", self.with_stops(current, sequence[:index] + [stops[position]] + sequence[index:])

        for group in zip_longest(remove(), replace(), relocate(), insert()):
            yield from (move for move in group if move is not None)

    def amounts(self, current: Route, entry: PlanEvaluation, order: list[int]):
        capacity = self.config.battery_capacity
        for strategy in ("minimal", "speed", "full"):
            yield strategy, self.allocation(current, strategy)
        for fraction in (1.0, 0.5, 0.25, 0.125):
            for position in order:
                trace = entry.trace.stops[position]
                amount = trace.energy_charged
                headroom = max(0.0, capacity - trace.battery_on_departure)
                for delta in (-fraction * amount, fraction * headroom):
                    if abs(delta) > 1e-8:
                        stops = clone_route_stops(current)
                        stops[position].energy_charged = amount + delta
                        yield "quantity", self.with_stops(current, stops)
                for other in order:
                    if other == position:
                        continue
                    transfer = fraction * min(headroom, entry.trace.stops[other].energy_charged)
                    if transfer > 1e-8:
                        stops = clone_route_stops(current)
                        for index in order:
                            stops[index].energy_charged = entry.trace.stops[index].energy_charged
                        stops[position].energy_charged += transfer
                        stops[other].energy_charged -= transfer
                        yield "transfer", self.with_stops(current, stops)

    def proposals(self, current, entry, *, partial, topology, critical):
        positions = self.positions(current.stops)
        if critical and positions:
            bounds = entry.timing.marginal_bounds(entry.trace)
            positions = [positions[index] for index in np.argsort(bounds, kind="stable")]
        gaps = list(range(len(current.stops) - 1))
        if critical and positions:
            gaps.sort(key=lambda gap: (abs(gap + 0.5 - positions[0]), gap >= positions[0]))
        quantities = self.amounts(current, entry, positions) if partial else iter(())

        def structural():
            if topology:
                for move, route in self.topologies(current, positions, gaps):
                    yield move, self.allocation(route, "minimal" if partial else "full")
                    if partial and len(self.positions(route.stops)) > 1:
                        yield move, self.allocation(route, "speed")

        for group in zip_longest(quantities, structural()):
            yield from (move for move in group if move is not None)


def _score(route: Route, reliability: float, completion: float, target: float) -> tuple:
    return SearchCandidate(route, True, reliability, completion).score_key(target)


def _surrogate(entry: PlanEvaluation, method: str, target: float) -> tuple:
    timing = entry.timing
    if method == "B1":
        waits = np.exp(timing.mus + 0.5 * timing.sigmas**2)
    else:
        from scipy.special import ndtri

        probability = target ** (1 / max(1, len(timing.mus)))
        waits = np.exp(timing.mus + timing.sigmas * ndtri(probability))
    success, completion = timing.evaluate(waits[None, :])
    return int(success[0]), -float(completion[0])


def optimize(
    instance: Instance, config: SimulatorConfig, original: Route, method: str, budget: BudgetConfig,
    *, seed: int, samples: int, target: float = 0.95, nearby: int = 3,
) -> SearchResult:
    if method not in METHODS:
        raise ValueError(f"Unknown method {method}")
    tracker = BudgetTracker(budget)
    evaluator = RouteEvaluator(instance, config, seed, "opt", budget=tracker)
    current = original
    current_entry = evaluator.prepare(current)
    if current_entry is None or not current_entry.trace.feasible:
        raise ValueError("Infeasible CON starting plan or insufficient starting budget")
    star = method.startswith("STaR")
    target_time = None
    rejected = prefix_rejected = 0
    history = []
    surrogate = method in ("B1", "B2")

    def score(route, entry):
        if surrogate:
            started = perf_counter()
            result = _surrogate(entry, method, target)
            tracker.simulation_seconds += perf_counter() - started
            return result
        if not evaluator.extend(route, entry, samples):
            return None
        return _score(route, float(entry.success.mean()), float(entry.completion.mean()), target)

    best = () if method == "B0" else score(current, current_entry)
    if best is None:
        raise ValueError("Budget too small to score source plan")
    if best and not surrogate and best[1] == 1:
        target_time = tracker.elapsed()
    if method == "B0":
        return SearchResult(current, best, tracker.to_dict(), history, 0, 0, target_time)
    neighborhood = Neighborhood(instance, config, nearby)
    seen = {ChargePlan.from_route(instance, current)}
    generation_cap = 10 * budget.max_candidate_evals

    while not tracker.any_exceeded() and tracker.generated < generation_cap:
        proposals = neighborhood.proposals(
            current, current_entry, partial=method != "STaR_no_partial", topology=method != "B4", critical=star,
        )
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
            if star and best[1] == 1:
                started = perf_counter()
                bounds = entry.timing.marginal_bounds(entry.trace)
                tracker.screen_checks += 1
                tracker.screening_seconds += perf_counter() - started
                if bounds.min(initial=1.0) < target - 1e-12:
                    rejected += 1
                    continue
            if star and samples >= 128:
                prefix = samples // 4
                if not evaluator.extend(candidate, entry, prefix):
                    continue
                upper = (int(entry.success.sum()) + samples - prefix) / samples
                lower = (entry.completion.sum() + (samples - prefix) * entry.trace.end_clock) / samples
                optimistic = _score(candidate, upper, float(lower - 1e-8), target)
                if optimistic <= best:
                    prefix_rejected += 1
                    continue
            challenger = score(candidate, entry)
            if challenger is not None and not tracker.wall_exceeded() and challenger > best:
                best, current, current_entry = challenger, candidate, entry
                history.append(move)
                if not surrogate and best[1] == 1 and target_time is None:
                    target_time = tracker.elapsed()
                improved = True
                break
        if not improved:
            break
    return SearchResult(current, best, tracker.to_dict(), history, rejected, prefix_rejected, target_time)
