"""Euclidean geometry helpers for benchmark instances."""

from __future__ import annotations

import numpy as np

from star_evrp.types import Instance, Node


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Planar Euclidean distance."""
    return float(np.hypot(x2 - x1, y2 - y1))


def distance_between_nodes(a: Node, b: Node) -> float:
    return euclidean_distance(a.x, a.y, b.x, b.y)


def build_coordinate_array(nodes: list[Node]) -> np.ndarray:
    """Stack node coordinates in list order into an ``(n, 2)`` array."""
    return np.asarray([[n.x, n.y] for n in nodes], dtype=np.float64)


def precompute_distance_matrix(coordinates: np.ndarray) -> np.ndarray:
    """All-pairs Euclidean distance matrix (symmetric, zero diagonal)."""
    diff = coordinates[:, np.newaxis, :] - coordinates[np.newaxis, :, :]
    return np.sqrt(np.sum(diff * diff, axis=2, dtype=np.float64))


def attach_distance_matrix(instance: Instance) -> Instance:
    """Return the same instance with ``distance_matrix`` filled (in-place update)."""
    instance.distance_matrix = precompute_distance_matrix(instance.coordinates)
    return instance


def leg_distance(instance: Instance, from_id: int, to_id: int) -> float:
    """Distance between two nodes by global id."""
    i = instance.node_id_to_index[from_id]
    j = instance.node_id_to_index[to_id]
    return float(instance.distance_matrix[i, j])


def leg_energy(instance: Instance, from_id: int, to_id: int, consumption_rate: float) -> float:
    return consumption_rate * leg_distance(instance, from_id, to_id)