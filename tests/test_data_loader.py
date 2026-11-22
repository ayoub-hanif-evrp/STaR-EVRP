"""Tests for dataset parsing and instance materialization."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest

from star_evrp.data_loader import (
    assign_partitions,
    build_instance,
    discover_dataset_root,
    load_single_instance,
    load_station_csv,
    normalize_instance_stem,
    parse_family_and_parent,
)
from star_evrp.types import NodeType

from tests.conftest import PROJECT_ROOT


def test_discover_dataset_root(project_root: Path):
    root = discover_dataset_root(project_root / "dataset")
    assert (root / "ev_specs.json").is_file()
    assert (root / "params.json").is_file()


def test_load_real_instance_c1_10_1(project_root: Path):
    inst = load_single_instance(project_root, "C1_10_1", "A")
    assert inst.instance_key == "C1_10_1"
    assert inst.family == "C1"
    assert inst.fleet_size == 250
    assert inst.load_capacity == 200.0
    assert inst.num_customers == len(inst.customer_node_ids)
    assert inst.num_customers > 0
    assert inst.num_stations > 0
    depot = inst.node(0)
    assert depot.node_type == NodeType.DEPOT
    assert inst.depot_closing_time == depot.due_date
    assert len(inst.customer_node_ids) == inst.num_customers
    for sid in inst.station_node_ids:
        assert sid in inst.station_attributes
        assert inst.station_attributes[sid].charging_rate > 0


def test_station_csv_joined_by_id(project_root: Path):
    inst = load_single_instance(project_root, "C1_10_1", "A")
    csv_ids = set(inst.station_attributes.keys())
    txt_ids = set(inst.station_node_ids)
    assert txt_ids <= csv_ids


def test_normalize_instance_stem():
    assert normalize_instance_stem(Path("c1_10_1.txt")) == "C1_10_1"
    assert normalize_instance_stem(Path("C1_10_1_stations.csv")) == "C1_10_1"


def test_parse_family_and_parent():
    family, parent = parse_family_and_parent("RC2_25_3")
    assert family == "RC2"
    assert parent == "RC2_25_3"


def test_assign_partitions_lexicographic():
    parents = {"C1": ["C1_10_2", "C1_10_1", "C1_10_3"]}
    part = assign_partitions(parents, 2)
    assert part["C1_10_1"] == "development"
    assert part["C1_10_2"] == "development"
    assert part["C1_10_3"] == "holdout"


def test_reject_missing_stations_csv():
    with tempfile.TemporaryDirectory() as tmp:
        inst_txt = Path(tmp) / "C1_10_1.txt"
        inst_txt.write_text(
            "c1_10_1\n\nVEHICLE\nNUMBER     CAPACITY\n 5 50\n\n"
            "CUSTOMER\nCUST NO.  XCOORD.    YCOORD.    DEMAND   READY TIME  DUE DATE   SERVICE TIME\n"
            "    0       0          0          0          0       100          0\n"
            "    1       10         0         10          0       100         10\n"
            " 1001       5          5          0          0       100          0\n",
            encoding="utf-8",
        )
        missing_csv = Path(tmp) / "C1_10_1_stations.csv"
        with pytest.raises(FileNotFoundError):
            build_instance(inst_txt, missing_csv, "A")


def test_reject_invalid_station_csv_columns():
    with tempfile.TemporaryDirectory() as tmp:
        bad_csv = Path(tmp) / "bad_stations.csv"
        with bad_csv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["station_id", "charging_rate"])
            w.writerow(["1001", "1.0"])
        with pytest.raises(ValueError, match="missing columns"):
            load_station_csv(bad_csv)