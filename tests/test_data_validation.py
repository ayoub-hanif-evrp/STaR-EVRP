"""Structural validation on synthetic malformed instances."""

from __future__ import annotations

import copy

from star_evrp.data_validation import validate_instance, validate_instance_report
from star_evrp.types import Node, NodeType, StationAttributes

from tests.conftest import make_synthetic_instance


def test_valid_synthetic_instance_has_no_issues():
    inst = make_synthetic_instance()
    assert validate_instance(inst) == []
    report = validate_instance_report(inst)
    assert report.feasible


def test_duplicate_node_id_detected():
    inst = make_synthetic_instance()
    inst.nodes.append(copy.deepcopy(inst.nodes[1]))
    issues = validate_instance(inst)
    assert any("Duplicate" in m for m in issues)


def test_missing_depot_detected():
    inst = make_synthetic_instance()
    inst.nodes = [n for n in inst.nodes if n.node_type != NodeType.DEPOT]
    issues = validate_instance(inst)
    assert any("depot" in m.lower() for m in issues)


def test_station_csv_mismatch_detected():
    inst = make_synthetic_instance(station_ids=[1001, 1002])
    inst.station_attributes = {
        1001: inst.station_attributes[1001],
    }
    issues = validate_instance(inst)
    assert any("without CSV" in m or "not in .txt" in m for m in issues)


def test_invalid_customer_time_window():
    inst = make_synthetic_instance()
    bad = Node(
        node_id=99,
        node_type=NodeType.CUSTOMER,
        x=1.0,
        y=1.0,
        demand=1.0,
        ready_time=50.0,
        due_date=10.0,
        service_time=1.0,
    )
    inst.nodes.append(bad)
    inst.customer_node_ids.append(99)
    inst.num_customers += 1
    issues = validate_instance(inst)
    assert any("ready_time > due_date" in m for m in issues)


def test_negative_charging_rate():
    inst = make_synthetic_instance()
    sid = inst.station_node_ids[0]
    att = inst.station_attributes[sid]
    inst.station_attributes[sid] = StationAttributes(
        station_id=sid,
        charging_rate=-1.0,
        price_mu=att.price_mu,
        price_sigma=att.price_sigma,
        wait_mu=att.wait_mu,
        wait_sigma=att.wait_sigma,
        density_score=att.density_score,
    )
    issues = validate_instance(inst)
    assert any("charging_rate" in m for m in issues)