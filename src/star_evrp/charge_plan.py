"""Lossless identity and reconstruction for fixed charging plans."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from star_evrp.types import Instance, NodeType, Route, RouteStop


def customer_local_sequence(instance: Instance, route: Route) -> list[int]:
    if route.stops is None:
        return list(route.customer_indices or [])
    return [
        instance.customer_local_index(stop.node_id)
        for stop in route.stops
        if instance.node(stop.node_id).node_type == NodeType.CUSTOMER
    ]


def customer_node_ids(instance: Instance, route: Route) -> list[int]:
    return [instance.customer_node_ids[index] for index in customer_local_sequence(instance, route)]


def route_structure_error(instance: Instance, route: Route) -> str | None:
    stops = route.stops or []
    if len(stops) < 2 or stops[0].node_id != 0 or stops[-1].node_id != 0:
        return "route_requires_terminal_depots"
    if any(stop.node_id not in instance.node_id_to_index for stop in stops):
        return "unknown_route_node"
    if any(stop.node_id == 0 for stop in stops[1:-1]):
        return "intermediate_depot"
    if any(not math.isfinite(stop.wait_extra) or stop.wait_extra < 0 for stop in stops):
        return "invalid_fixed_wait"
    if any(
        (stop.energy_charged not in (None, 0.0) or stop.wait_extra)
        and instance.node(stop.node_id).node_type != NodeType.STATION
        for stop in stops
    ):
        return "nonstation_charge_or_wait"
    if route.customer_indices is not None and customer_local_sequence(instance, route) != route.customer_indices:
        return "customer_sequence_mismatch"
    return None


@dataclass(frozen=True, slots=True)
class ChargePlan:
    stops: tuple[tuple[int, str | None, str], ...]

    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps(self.stops, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def from_route(instance: Instance, route: Route) -> ChargePlan:
        if route.stops is None:
            raise ValueError("Plan requires explicit stops")
        return ChargePlan(tuple(
            (stop.node_id, None if stop.energy_charged is None else float(stop.energy_charged).hex(),
             float(stop.wait_extra).hex())
            for stop in route.stops
        ))

    def to_route(self, instance: Instance, route_id: int = 0) -> Route:
        route = Route(route_id=route_id, stops=[
            RouteStop(node, None if amount is None else float.fromhex(amount), float.fromhex(wait))
            for node, amount, wait in self.stops
        ])
        error = route_structure_error(instance, route)
        if error:
            raise ValueError(error)
        route.customer_indices = customer_local_sequence(instance, route)
        return route


def route_to_charge_plan_stops(instance: Instance, route: Route) -> ChargePlan:
    return ChargePlan.from_route(instance, route)


def charge_plan_to_route(instance: Instance, plan: ChargePlan, route_id: int) -> Route:
    return plan.to_route(instance, route_id)


def routes_share_customers(instance: Instance, first: Route, second: Route) -> bool:
    return customer_local_sequence(instance, first) == customer_local_sequence(instance, second)


def clone_route_stops(route: Route) -> list[RouteStop]:
    return [RouteStop(stop.node_id, stop.energy_charged, stop.wait_extra) for stop in route.stops or []]
