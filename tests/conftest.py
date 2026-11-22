"""Shared fixtures: synthetic miniature instances and project root."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from star_evrp.geometry import build_coordinate_array, precompute_distance_matrix
from star_evrp.types import EVSpecs, Instance, Node, NodeType, StationAttributes

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_synthetic_instance(
    *,
    num_customers: int = 2,
    station_ids: list[int] | None = None,
    fleet_size: int = 5,
    load_capacity: float = 100.0,
    depot_closing: float = 500.0,
    ev_specs: EVSpecs | None = None,
    customer_tw: tuple[float, float] | None = None,
    charging_rate: float = 2.0,
    wait_mu: float = -1.0,
    wait_sigma: float = 0.3,
) -> Instance:
    """Build a tiny Euclidean instance for unit tests (not benchmark results)."""
    if station_ids is None:
        station_ids = [1001]
    if ev_specs is None:
        ev_specs = EVSpecs(battery_capacity=50.0, energy_consumption_rate=1.0)

    nodes: list[Node] = [
        Node(
            node_id=0,
            node_type=NodeType.DEPOT,
            x=0.0,
            y=0.0,
            demand=0.0,
            ready_time=0.0,
            due_date=depot_closing,
            service_time=0.0,
        ),
    ]
    for i in range(1, num_customers + 1):
        ready, due = customer_tw if customer_tw else (0.0, depot_closing - 10.0)
        nodes.append(
            Node(
                node_id=i,
                node_type=NodeType.CUSTOMER,
                x=float(i * 5),
                y=0.0,
                demand=1.0,
                ready_time=ready,
                due_date=due,
                service_time=1.0,
            )
        )
    for j, sid in enumerate(station_ids):
        nodes.append(
            Node(
                node_id=sid,
                node_type=NodeType.STATION,
                x=float(2 + j * 3),
                y=5.0,
                demand=0.0,
                ready_time=0.0,
                due_date=depot_closing,
                service_time=0.0,
            )
        )

    station_attributes = {
        sid: StationAttributes(
            station_id=sid,
            charging_rate=charging_rate,
            price_mu=0.0,
            price_sigma=0.1,
            wait_mu=wait_mu,
            wait_sigma=wait_sigma,
            density_score=0.5,
        )
        for sid in station_ids
    }

    node_id_to_index = {n.node_id: i for i, n in enumerate(nodes)}
    customer_node_ids = [n.node_id for n in nodes if n.node_type == NodeType.CUSTOMER]
    station_node_ids = [n.node_id for n in nodes if n.node_type == NodeType.STATION]
    coords = build_coordinate_array(nodes)
    dist = precompute_distance_matrix(coords)

    return Instance(
        instance_key="SYNTH_MINI",
        family="SYNTH",
        variant="A",
        parent_key="SYNTH_MINI",
        partition="unknown",
        instance_path=PROJECT_ROOT / "tests" / "_synthetic.txt",
        stations_path=PROJECT_ROOT / "tests" / "_synthetic_stations.csv",
        instance_file_sha256="synthetic",
        stations_file_sha256="synthetic",
        fleet_size=fleet_size,
        load_capacity=load_capacity,
        depot_closing_time=depot_closing,
        num_customers=len(customer_node_ids),
        num_stations=len(station_node_ids),
        nodes=nodes,
        node_id_to_index=node_id_to_index,
        customer_node_ids=customer_node_ids,
        station_node_ids=station_node_ids,
        station_attributes=station_attributes,
        coordinates=coords,
        distance_matrix=dist,
        dataset_params={},
        ev_specs=ev_specs,
    )


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def synth_instance() -> Instance:
    return make_synthetic_instance()


@pytest.fixture
def simulator_config(synth_instance: Instance):
    from star_evrp.deterministic_simulator import SimulatorConfig

    Q = synth_instance.ev_specs.battery_capacity
    h = synth_instance.ev_specs.energy_consumption_rate
    return SimulatorConfig(battery_capacity=Q, energy_consumption_rate=h)