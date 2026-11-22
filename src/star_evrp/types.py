"""Shared typed data structures for STaR-EVRP."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Any, Literal

import numpy as np

NUM_TOL = 1e-9

PartitionName = Literal["development", "holdout", "unknown"]
VariantCode = Literal["A", "B"]


class NodeType(str, Enum):
    """Benchmark node classification."""

    DEPOT = "depot"
    CUSTOMER = "customer"
    STATION = "station"


@dataclass(frozen=True, slots=True)
class Node:
    """A depot, customer, or charging-station node."""

    node_id: int
    node_type: NodeType
    x: float
    y: float
    demand: float
    ready_time: float
    due_date: float
    service_time: float


@dataclass(frozen=True, slots=True)
class StationAttributes:
    """Heterogeneous charging-station parameters (joined by ``station_id``)."""

    station_id: int
    charging_rate: float
    price_mu: float
    price_sigma: float
    wait_mu: float
    wait_sigma: float
    density_score: float


@dataclass(frozen=True, slots=True)
class EVSpecs:
    """Electric-vehicle energy parameters."""

    battery_capacity: float
    energy_consumption_rate: float


@dataclass
class Instance:
    """Parsed EVRPTW benchmark instance with geometry and station metadata."""

    instance_key: str
    family: str
    variant: VariantCode
    parent_key: str
    partition: PartitionName
    instance_path: Path
    stations_path: Path
    instance_file_sha256: str
    stations_file_sha256: str
    fleet_size: int
    load_capacity: float
    depot_closing_time: float
    num_customers: int
    num_stations: int
    nodes: list[Node]
    node_id_to_index: dict[int, int]
    customer_node_ids: list[int]
    station_node_ids: list[int]
    station_attributes: dict[int, StationAttributes]
    coordinates: np.ndarray
    distance_matrix: np.ndarray
    dataset_params: dict[str, Any]
    ev_specs: EVSpecs

    def node(self, node_id: int) -> Node:
        return self.nodes[self.node_id_to_index[node_id]]

    def customer_local_index(self, node_id: int) -> int:
        """Map customer ``node_id`` to local index ``0 .. num_customers-1``."""
        return self.customer_local_indices[node_id]

    @cached_property
    def customer_local_indices(self) -> dict[int, int]:
        return {node_id: index for index, node_id in enumerate(self.customer_node_ids)}

    def index_of(self, node_id: int) -> int:
        return self.node_id_to_index[node_id]

    def charging_rate(self, station_id: int) -> float:
        return self.station_attributes[station_id].charging_rate


@dataclass(frozen=True, slots=True)
class ChargingVisit:
    """Planned or executed charging event at a station."""

    station_id: int
    energy_before: float
    energy_charged: float
    energy_after: float
    charge_duration: float
    wait_before_charge: float


@dataclass
class RouteStop:
    """One visit in an explicit route plan (depot, customer, or station)."""

    node_id: int
    energy_charged: float | None = None
    """Energy added at a station; ``None`` means recharge to full capacity."""

    wait_extra: float = 0.0
    """Exogenous waiting time at this stop (stochastic slot; 0 for deterministic baseline)."""


@dataclass
class Route:
    """A vehicle route.

    Either ``customer_indices`` (baseline CON/HC local indices, charging inserted on the fly)
    or an explicit ``stops`` sequence including station node ids for fixed charging plans.
  """

    route_id: int = 0
    customer_indices: list[int] | None = None
    stops: list[RouteStop] | None = None

    def uses_explicit_stops(self) -> bool:
        return self.stops is not None and len(self.stops) > 0


@dataclass
class RouteTraceStop:
    """Simulation state at one node visit."""

    node_id: int
    node_type: NodeType
    arrival_time: float
    service_start_time: float
    departure_time: float
    wait_time_early: float
    wait_time_extra: float
    service_time: float
    battery_on_arrival: float
    battery_on_departure: float
    energy_charged: float
    load_after_service: float
    tw_slack_remaining: float
    battery_slack_remaining: float
    charging_rate: float | None = None


@dataclass
class RouteTrace:
    """Full deterministic timeline for one route."""

    route_id: int
    feasible: bool
    failure_reason: str | None
    total_distance: float
    num_charging_visits: int
    end_node_id: int
    end_battery: float
    end_clock: float
    end_load: float
    stops: list[RouteTraceStop] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable summary (stops abbreviated when large)."""
        return {
            "route_id": self.route_id,
            "feasible": self.feasible,
            "failure_reason": self.failure_reason,
            "total_distance": self.total_distance,
            "num_charging_visits": self.num_charging_visits,
            "end_node_id": self.end_node_id,
            "end_battery": self.end_battery,
            "end_clock": self.end_clock,
            "end_load": self.end_load,
            "stops": [
                {
                    "node_id": s.node_id,
                    "node_type": s.node_type.value,
                    "arrival_time": s.arrival_time,
                    "departure_time": s.departure_time,
                    "energy_charged": s.energy_charged,
                }
                for s in self.stops
            ],
        }


@dataclass
class Solution:
    """Multi-route solution for one instance."""

    instance_key: str
    variant: VariantCode
    method: str
    battery_capacity: float
    energy_consumption_rate: float
    routes: list[Route]
    total_distance: float | None = None
    feasible: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationMetrics:
    """Aggregated outcomes from one or more route simulations."""

    num_routes: int
    total_distance: float
    total_charging_visits: int
    feasible_routes: int
    infeasible_routes: int


@dataclass
class RouteReliabilityResult:
    """Stochastic route-level reliability estimate (filled by future simulators)."""

    instance_key: str
    route_id: int
    scenarios: int
    successes: int
    reliability: float
    wilson_ci_low: float
    wilson_ci_high: float
    mean_extra_wait: float = 0.0


@dataclass
class FeasibilityIssue:
    """Single validation failure."""

    scope: str
    message: str
    route_id: int | None = None
    node_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeasibilityReport:
    """Solution- or instance-level validation outcome."""

    feasible: bool
    issues: list[FeasibilityIssue] = field(default_factory=list)
    traces: list[RouteTrace] = field(default_factory=list)

    def add_issue(
        self,
        message: str,
        *,
        scope: str = "solution",
        route_id: int | None = None,
        node_id: int | None = None,
        **details: Any,
    ) -> None:
        self.feasible = False
        self.issues.append(
            FeasibilityIssue(
                scope=scope,
                message=message,
                route_id=route_id,
                node_id=node_id,
                details=dict(details),
            )
        )
