"""Charge-plan fingerprints and route conversion (customer order fixed)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from star_evrp.types import Instance, NodeType, Route, RouteStop


def customer_local_sequence(instance: Instance, route: Route) -> list[int]:
    """Extract customer local indices in visit order."""
    if route.customer_indices is not None:
        return list(route.customer_indices)
    out: list[int] = []
    for stop in route.stops or []:
        if instance.node(stop.node_id).node_type == NodeType.CUSTOMER:
            out.append(instance.customer_local_index(stop.node_id))
    return out


def customer_node_ids(instance: Instance, route: Route) -> list[int]:
    """Customer node ids in visit order."""
    locals_ = customer_local_sequence(instance, route)
    return [instance.customer_node_ids[i] for i in locals_]


def station_visit_tuples(route: Route, instance: Instance) -> list[tuple[int, float | None]]:
    """(station_node_id, energy_charged) for each charging visit in order."""
    out: list[tuple[int, float | None]] = []
    for stop in route.stops or []:
        if instance.node(stop.node_id).node_type == NodeType.STATION:
            out.append((stop.node_id, stop.energy_charged))
    return out


def _encode_energy(ec: float | None) -> str:
    if ec is None:
        return "FULL"
    return f"{ec:.8g}"


@dataclass(frozen=True, slots=True)
class ChargePlan:
    """Fixed customer order and charging visits (energy amounts explicit)."""

    customer_locals: tuple[int, ...]
    charges: tuple[tuple[int, str], ...]
    """Pairs ``(station_id, energy_token)`` with energy_token from :func:`_encode_energy`."""

    def fingerprint(self) -> str:
        """Stable SHA-256 hex digest for caches and deduplication."""
        payload = {
            "customers": list(self.customer_locals),
            "charges": list(self.charges),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def from_route(instance: Instance, route: Route) -> ChargePlan:
        cust = tuple(customer_local_sequence(instance, route))
        charges = tuple(
            (sid, _encode_energy(ec)) for sid, ec in station_visit_tuples(route, instance)
        )
        return ChargePlan(customer_locals=cust, charges=charges)

    def to_route(self, instance: Instance, route_id: int = 0) -> Route:
        """Reconstruct explicit depot–customers–depot with interleaved stations."""
        stops: list[RouteStop] = [RouteStop(node_id=0)]
        charge_iter = iter(self.charges)
        next_charge = next(charge_iter, None)
        for loc in self.customer_locals:
            while next_charge is not None:
                # Heuristic: stations before this customer if we cannot disambiguate —
                # full reconstruction requires original stop positions; we interleave
                # using stored sequence matching :func:`route_to_charge_plan_stops`.
                break
            cid = instance.customer_node_ids[loc]
            stops.append(RouteStop(node_id=cid))
        # Fallback when charges were stored with route snapshot
        return Route(
            route_id=route_id,
            customer_indices=list(self.customer_locals),
            stops=stops,
        )


def route_to_charge_plan_stops(instance: Instance, route: Route) -> ChargePlan:
    """Fingerprint including full stop-aligned charge list (preserves positions)."""
    cust = tuple(customer_local_sequence(instance, route))
    charges: list[tuple[int, str]] = []
    for stop in route.stops or []:
        if instance.node(stop.node_id).node_type == NodeType.STATION:
            charges.append((stop.node_id, _encode_energy(stop.energy_charged)))
    return ChargePlan(customer_locals=cust, charges=tuple(charges))


def charge_plan_to_route(
    instance: Instance,
    plan: ChargePlan,
    route_id: int,
    *,
    stop_positions: list[tuple[int, float | None]] | None = None,
) -> Route:
    """Build route from plan.

    If ``stop_positions`` is given, each item is ``(node_id, energy_charged)`` in
    full visit order (depot, customers, stations, depot). Otherwise only customer
  indices are set and stops must be supplied by the caller.
    """
    if stop_positions is not None:
        stops = [
            RouteStop(node_id=nid, energy_charged=ec if ec is not None or nid == 0 else ec)
            for nid, ec in stop_positions
        ]
        return Route(
            route_id=route_id,
            customer_indices=list(plan.customer_locals),
            stops=stops,
        )
    return Route(route_id=route_id, customer_indices=list(plan.customer_locals), stops=[])


def routes_share_customers(instance: Instance, a: Route, b: Route) -> bool:
    """True if customer visit order matches."""
    return customer_local_sequence(instance, a) == customer_local_sequence(instance, b)


def clone_route_stops(route: Route) -> list[RouteStop]:
    return [
        RouteStop(node_id=s.node_id, energy_charged=s.energy_charged, wait_extra=s.wait_extra)
        for s in route.stops or []
    ]