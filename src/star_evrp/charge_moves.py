"""Local charging edits preserving customer visit order."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum

from star_evrp.charge_plan import clone_route_stops, customer_local_sequence, routes_share_customers
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.geometry import leg_distance
from star_evrp.types import NUM_TOL, Instance, NodeType, Route, RouteStop


class MoveKind(str, Enum):
    REPLACE = "replace"
    REMOVE = "remove"
    INSERT = "insert"
    RELOCATE = "relocate"
    CHARGE_AMOUNT = "charge_amount"
    TWO_EDIT = "two_edit"


@dataclass
class MoveResult:
    route: Route | None
    feasible: bool
    reason: str | None = None
    move: MoveKind | None = None


def _assert_customers_preserved(instance: Instance, base: Route, cand: Route) -> bool:
    return routes_share_customers(instance, base, cand)


def _make_route(route_id: int, stops: list[RouteStop], base: Route) -> Route:
    return Route(
        route_id=route_id,
        stops=stops,
        customer_indices=base.customer_indices,
    )


def validate_energy_route(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
) -> MoveResult:
    tr = simulate_route_fixed(instance, route, config)
    if not tr.feasible:
        return MoveResult(route=None, feasible=False, reason=tr.failure_reason or "det_infeasible")
    return MoveResult(route=route, feasible=True)


def replace_station(
    instance: Instance,
    base: Route,
    visit_index: int,
    new_station_id: int,
    config: SimulatorConfig,
) -> MoveResult:
    stops = clone_route_stops(base)
    if visit_index <= 0 or visit_index >= len(stops):
        return MoveResult(None, False, "bad_index", MoveKind.REPLACE)
    if instance.node(stops[visit_index].node_id).node_type != NodeType.STATION:
        return MoveResult(None, False, "not_station", MoveKind.REPLACE)
    old = stops[visit_index]
    stops[visit_index] = RouteStop(
        node_id=new_station_id,
        energy_charged=old.energy_charged,
        wait_extra=0.0,
    )
    cand = _make_route(base.route_id, stops, base)
    if not _assert_customers_preserved(instance, base, cand):
        return MoveResult(None, False, "customers_changed", MoveKind.REPLACE)
    out = validate_energy_route(instance, cand, config)
    out.move = MoveKind.REPLACE
    return out


def remove_station(
    instance: Instance,
    base: Route,
    visit_index: int,
    config: SimulatorConfig,
) -> MoveResult:
    stops = clone_route_stops(base)
    if visit_index <= 0 or visit_index >= len(stops):
        return MoveResult(None, False, "bad_index", MoveKind.REMOVE)
    if instance.node(stops[visit_index].node_id).node_type != NodeType.STATION:
        return MoveResult(None, False, "not_station", MoveKind.REMOVE)
    del stops[visit_index]
    cand = _make_route(base.route_id, stops, base)
    if not _assert_customers_preserved(instance, base, cand):
        return MoveResult(None, False, "customers_changed", MoveKind.REMOVE)
    out = validate_energy_route(instance, cand, config)
    out.move = MoveKind.REMOVE
    return out


def insert_station(
    instance: Instance,
    base: Route,
    after_index: int,
    station_id: int,
    energy_charged: float | None,
    config: SimulatorConfig,
) -> MoveResult:
    stops = clone_route_stops(base)
    if after_index < 0 or after_index >= len(stops):
        return MoveResult(None, False, "bad_gap", MoveKind.INSERT)
    if station_id not in instance.station_node_ids:
        return MoveResult(None, False, "unknown_station", MoveKind.INSERT)
    if energy_charged is not None and (
        not __import__("math").isfinite(energy_charged) or energy_charged < -NUM_TOL
    ):
        return MoveResult(None, False, "invalid_charge", MoveKind.INSERT)
    stops.insert(
        after_index + 1,
        RouteStop(node_id=station_id, energy_charged=energy_charged, wait_extra=0.0),
    )
    cand = _make_route(base.route_id, stops, base)
    if not _assert_customers_preserved(instance, base, cand):
        return MoveResult(None, False, "customers_changed", MoveKind.INSERT)
    out = validate_energy_route(instance, cand, config)
    out.move = MoveKind.INSERT
    return out


def relocate_station(
    instance: Instance,
    base: Route,
    from_index: int,
    after_index: int,
    config: SimulatorConfig,
) -> MoveResult:
    stops = clone_route_stops(base)
    if from_index <= 0 or from_index >= len(stops):
        return MoveResult(None, False, "bad_from", MoveKind.RELOCATE)
    if instance.node(stops[from_index].node_id).node_type != NodeType.STATION:
        return MoveResult(None, False, "not_station", MoveKind.RELOCATE)
    stop = stops.pop(from_index)
    insert_at = after_index + 1 if after_index < from_index else after_index
    if insert_at < 0 or insert_at > len(stops):
        return MoveResult(None, False, "bad_to", MoveKind.RELOCATE)
    stops.insert(insert_at, stop)
    cand = _make_route(base.route_id, stops, base)
    if not _assert_customers_preserved(instance, base, cand):
        return MoveResult(None, False, "customers_changed", MoveKind.RELOCATE)
    out = validate_energy_route(instance, cand, config)
    out.move = MoveKind.RELOCATE
    return out


def set_charge_amount(
    instance: Instance,
    base: Route,
    visit_index: int,
    energy_charged: float | None,
    config: SimulatorConfig,
) -> MoveResult:
    stops = clone_route_stops(base)
    if visit_index <= 0 or visit_index >= len(stops):
        return MoveResult(None, False, "bad_index", MoveKind.CHARGE_AMOUNT)
    if instance.node(stops[visit_index].node_id).node_type != NodeType.STATION:
        return MoveResult(None, False, "not_station", MoveKind.CHARGE_AMOUNT)
    if energy_charged is not None:
        import math

        if not math.isfinite(energy_charged) or energy_charged < -NUM_TOL:
            return MoveResult(None, False, "invalid_charge", MoveKind.CHARGE_AMOUNT)
        Q = config.battery_capacity
        if energy_charged > Q + NUM_TOL:
            return MoveResult(None, False, "overcharge", MoveKind.CHARGE_AMOUNT)
    stops[visit_index] = RouteStop(
        node_id=stops[visit_index].node_id,
        energy_charged=energy_charged,
        wait_extra=0.0,
    )
    cand = _make_route(base.route_id, stops, base)
    out = validate_energy_route(instance, cand, config)
    out.move = MoveKind.CHARGE_AMOUNT
    return out


def two_edit_compose(
    instance: Instance,
    base: Route,
    first: MoveResult,
    second: MoveResult,
    config: SimulatorConfig,
) -> MoveResult:
    """Apply two feasible edits sequentially."""
    if not first.feasible or first.route is None:
        return MoveResult(None, False, "first_failed", MoveKind.TWO_EDIT)
    if not second.feasible or second.route is None:
        return MoveResult(None, False, "second_failed", MoveKind.TWO_EDIT)
    # second should be built from first.route externally; validate final
    cand = second.route
    if not _assert_customers_preserved(instance, base, cand):
        return MoveResult(None, False, "customers_changed", MoveKind.TWO_EDIT)
    out = validate_energy_route(instance, cand, config)
    out.move = MoveKind.TWO_EDIT
    return out


def nearest_reachable_stations(
    instance: Instance,
    route: Route,
    gap_after_index: int,
    config: SimulatorConfig,
    k: int = 8,
) -> list[int]:
    """Stations sorted by travel distance from leg (gap_after_index, gap_after_index+1)."""
    stops = route.stops or []
    if gap_after_index < 0 or gap_after_index + 1 >= len(stops):
        return []
    a, b = stops[gap_after_index].node_id, stops[gap_after_index + 1].node_id
    Q, h = config.battery_capacity, config.energy_consumption_rate
    d_ab = leg_distance(instance, a, b)
    arr_batt = Q  # optimistic; caller may re-check
    scores: list[tuple[float, int]] = []
    for sid in instance.station_node_ids:
        d_as = leg_distance(instance, a, sid)
        d_sb = leg_distance(instance, sid, b)
        if h * (d_as + d_sb) > arr_batt + NUM_TOL + h * d_ab:
            continue
        scores.append((d_as + d_sb, sid))
    scores.sort(key=lambda t: t[0])
    return [sid for _, sid in scores[:k]]


def partial_charge_targets(
    instance: Instance,
    route: Route,
    visit_index: int,
    config: SimulatorConfig,
) -> list[float | None]:
    """A few meaningful charge amounts: min-to-next, half-gap-to-Q, full."""
    Q = config.battery_capacity
    h = config.energy_consumption_rate
    stops = route.stops or []
    if visit_index <= 0 or visit_index >= len(stops):
        return []
    targets: list[float | None] = [None]
    # rough minimum to reach next stop
    next_id = stops[visit_index + 1].node_id if visit_index + 1 < len(stops) else 0
    d = leg_distance(instance, stops[visit_index].node_id, next_id)
    need = h * d * 1.05
    targets.append(min(Q, need))
    targets.append(min(Q, 0.5 * Q))
    return targets


def enumerate_station_indices(route: Route, instance: Instance) -> list[int]:
    return [
        i
        for i, s in enumerate(route.stops or [])
        if instance.node(s.node_id).node_type == NodeType.STATION
    ]


def customer_sequence_checksum(instance: Instance, route: Route) -> tuple[int, ...]:
    return tuple(customer_local_sequence(instance, route))