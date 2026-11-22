"""Seed stability, partitions, and resume helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from star_evrp.data_loader import build_partition_manifest, load_single_instance
from star_evrp.results_io import merge_resume
from star_evrp.statistics import make_rng, stable_seed
from star_evrp.stochastic_simulator import simulate_route_stochastic
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.types import Route, RouteStop

from tests.conftest import PROJECT_ROOT, make_synthetic_instance


def test_stable_seed_reproducible():
    assert stable_seed(1, "C1_10_1", "A") == stable_seed(1, "C1_10_1", "A")
    assert stable_seed(1, "C1_10_1", "A") != stable_seed(1, "C1_10_2", "A")


def test_rng_streams_independent_of_processing_order():
    keys = ["route_b", "route_a", "route_c"]
    streams = {k: make_rng(42, "sim", k, 0) for k in keys}
    samples_a = {k: streams[k].standard_normal(3) for k in sorted(keys)}
    streams2 = {k: make_rng(42, "sim", k, 0) for k in reversed(keys)}
    samples_b = {k: streams2[k].standard_normal(3) for k in sorted(keys)}
    for k in keys:
        assert (samples_a[k] == samples_b[k]).all()


def test_simulation_order_independent():
    inst = make_synthetic_instance(wait_mu=-1.0, wait_sigma=0.2)
    cfg = SimulatorConfig(
        battery_capacity=inst.ev_specs.battery_capacity,
        energy_consumption_rate=0.2,
    )
    sid = inst.station_node_ids[0]

    def make_route(rid):
        return Route(
            route_id=rid,
            stops=[
                RouteStop(node_id=0),
                RouteStop(node_id=sid),
                RouteStop(node_id=1),
                RouteStop(node_id=0),
            ],
        )

    r0, r1 = make_route(0), make_route(1)
    m_first = [
        simulate_route_stochastic(inst, r0, cfg, num_scenarios=200, master_seed=5).reliability,
        simulate_route_stochastic(inst, r1, cfg, num_scenarios=200, master_seed=5).reliability,
    ]
    m_rev = [
        simulate_route_stochastic(inst, r1, cfg, num_scenarios=200, master_seed=5).reliability,
        simulate_route_stochastic(inst, r0, cfg, num_scenarios=200, master_seed=5).reliability,
    ]
    assert m_first[0] == m_rev[1]
    assert m_first[1] == m_rev[0]


def test_variant_a_b_same_partition():
    a = load_single_instance(PROJECT_ROOT, "C1_10_1", "A")
    b = load_single_instance(PROJECT_ROOT, "C1_10_1", "B")
    manifest = build_partition_manifest(PROJECT_ROOT, development_parents_per_family=2)
    by_key = {(e["instance_key"], e["variant"]): e["partition"] for e in manifest["instances"]}
    assert a.parent_key == b.parent_key
    assert by_key[("C1_10_1", "A")] == by_key[("C1_10_1", "B")]
    assert a.partition == "unknown" or b.partition == "unknown" or a.partition == b.partition


def test_merge_resume_does_not_duplicate_keys():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "batch.json"
        merge_resume(path, {"run_1": {"x": 1}}, skip_existing=True)
        merge_resume(path, {"run_1": {"x": 999}, "run_2": {"y": 2}}, skip_existing=True)
        data = __import__("star_evrp.results_io", fromlist=["load_json"]).load_json(path)
        assert data["entries"]["run_1"]["x"] == 1
        assert data["entries"]["run_2"]["y"] == 2