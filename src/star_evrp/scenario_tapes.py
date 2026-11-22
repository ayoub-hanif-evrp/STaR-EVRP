"""Reproducible scenario tapes: shared standard-normal Z, transformed waits W."""

from __future__ import annotations

from typing import Literal

import numpy as np

from star_evrp.statistics import make_rng, stable_seed
from star_evrp.types import Instance, NodeType, Route

ScenarioSplit = Literal["opt", "val", "holdout"]


def tape_rng_seed(
    master_seed: int,
    parent_key: str,
    variant: str,
    route_id: int,
    split: ScenarioSplit,
) -> int:
    return stable_seed(master_seed, parent_key, variant, route_id, split, "scenario_z")


def num_charging_slots(route: Route, instance: Instance) -> int:
    return sum(
        1 for s in route.stops or [] if instance.node(s.node_id).node_type == NodeType.STATION
    )


def station_slot_indices(route: Route, instance: Instance) -> list[int]:
    """Stop indices of station visits in order (for slot-aligned Z columns)."""
    return [
        i
        for i, s in enumerate(route.stops or [])
        if instance.node(s.node_id).node_type == NodeType.STATION
    ]


def generate_z_tape(
    master_seed: int,
    parent_key: str,
    variant: str,
    route_id: int,
    split: ScenarioSplit,
    num_scenarios: int,
    num_slots: int,
) -> np.ndarray:
    """Standard-normal tape ``Z`` shape ``(num_scenarios, num_slots)``."""
    if num_scenarios <= 0:
        return np.zeros((0, max(0, num_slots)))
    if num_slots <= 0:
        return np.zeros((num_scenarios, 0))
    seed = tape_rng_seed(master_seed, parent_key, variant, route_id, split)
    rng = make_rng(seed, "tape")
    return rng.standard_normal((num_scenarios, num_slots))


def z_tape_for_route(
    master_seed: int,
    instance: Instance,
    route: Route,
    split: ScenarioSplit,
    num_scenarios: int,
    *,
    max_slots: int | None = None,
) -> np.ndarray:
    n = num_charging_slots(route, instance)
    cap = max_slots if max_slots is not None else max(n, 1)
    return generate_z_tape(
        master_seed,
        instance.parent_key,
        instance.variant,
        route.route_id,
        split,
        num_scenarios,
        cap,
    )


def _station_mus_sigmas(route: Route, instance: Instance) -> tuple[np.ndarray, np.ndarray]:
    mus: list[float] = []
    sigmas: list[float] = []
    for stop in route.stops or []:
        if instance.node(stop.node_id).node_type != NodeType.STATION:
            continue
        att = instance.station_attributes[stop.node_id]
        mus.append(float(att.wait_mu))
        sigmas.append(float(att.wait_sigma))
    return np.asarray(mus, dtype=np.float64), np.asarray(sigmas, dtype=np.float64)


def waits_from_z(
    instance: Instance,
    route: Route,
    z_matrix: np.ndarray,
) -> np.ndarray:
    """Transform shared Z to physical waits ``W = exp(mu + sigma * Z)``.

    Uses the first ``n_charges`` columns of ``z_matrix``. CRN policy: share Z across
    compared candidates on the same route/split; do **not** reuse W when ``mu/sigma``
    differ (e.g. after station replacement).
    """
    n_charges = num_charging_slots(route, instance)
    if n_charges == 0:
        return np.zeros((z_matrix.shape[0], 0))
    if z_matrix.shape[1] < n_charges:
        raise ValueError(
            f"z_matrix has {z_matrix.shape[1]} columns but route needs {n_charges}"
        )
    mus, sigmas = _station_mus_sigmas(route, instance)
    z = z_matrix[:, :n_charges]
    return np.exp(mus + sigmas * z)


def slice_z_for_slots(z_tape: np.ndarray, slot_columns: list[int]) -> np.ndarray:
    """Select columns by slot id (visit ordinal among stations)."""
    if not slot_columns:
        return np.zeros((z_tape.shape[0], 0))
    return z_tape[:, slot_columns]