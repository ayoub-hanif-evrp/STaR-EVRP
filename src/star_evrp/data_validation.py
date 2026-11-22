"""Structural validation of parsed benchmark instances."""

from __future__ import annotations

import math

from star_evrp.types import FeasibilityReport, Instance, NodeType, NUM_TOL


def validate_instance(instance: Instance) -> list[str]:
    """Return a list of human-readable integrity issues (empty if ok)."""
    issues: list[str] = []
    seen_ids: set[int] = set()

    for node in instance.nodes:
        if node.node_id in seen_ids:
            issues.append(f"Duplicate node id {node.node_id}")
        seen_ids.add(node.node_id)

    depots = [n for n in instance.nodes if n.node_type == NodeType.DEPOT]
    if len(depots) != 1 or depots[0].node_id != 0:
        issues.append("Expected exactly one depot with id 0")

    customers = [n for n in instance.nodes if n.node_type == NodeType.CUSTOMER]
    stations = [n for n in instance.nodes if n.node_type == NodeType.STATION]

    if len(customers) != instance.num_customers:
        issues.append(
            f"Customer count mismatch: header {instance.num_customers} vs parsed {len(customers)}"
        )

    if len(stations) != instance.num_stations:
        issues.append(
            f"Station count mismatch: header {instance.num_stations} vs parsed {len(stations)}"
        )

    for cid in instance.customer_node_ids:
        if cid <= 0 or cid > 1000:
            issues.append(f"Customer id {cid} outside published range 1..1000")

    for sid in instance.station_node_ids:
        if sid <= 1000:
            issues.append(f"Station id {sid} must be > 1000")

    csv_ids = set(instance.station_attributes)
    txt_station_ids = set(instance.station_node_ids)
    missing_csv = txt_station_ids - csv_ids
    extra_csv = csv_ids - txt_station_ids
    if missing_csv:
        issues.append(f"Stations in .txt without CSV rows: {sorted(missing_csv)[:5]}...")
    if extra_csv:
        issues.append(f"CSV station ids not in .txt: {sorted(extra_csv)[:5]}...")

    for sid, attr in instance.station_attributes.items():
        if not math.isfinite(attr.charging_rate) or attr.charging_rate <= 0:
            issues.append(f"Invalid charging_rate at station {sid}")
        if not math.isfinite(attr.wait_mu) or not math.isfinite(attr.wait_sigma):
            issues.append(f"Non-finite wait lognormal parameters at station {sid}")
        if attr.wait_sigma < -NUM_TOL:
            issues.append(f"Negative wait_sigma at station {sid}")

    for node in customers:
        if node.demand < -NUM_TOL:
            issues.append(f"Negative demand at customer {node.node_id}")
        if node.service_time < -NUM_TOL:
            issues.append(f"Negative service_time at customer {node.node_id}")
        if node.ready_time > node.due_date + NUM_TOL:
            issues.append(
                f"Customer {node.node_id} ready_time > due_date "
                f"({node.ready_time} > {node.due_date})"
            )

    if instance.fleet_size <= 0:
        issues.append(f"Nonpositive fleet_size {instance.fleet_size}")
    if instance.load_capacity <= 0:
        issues.append(f"Nonpositive load_capacity {instance.load_capacity}")

    if instance.ev_specs.battery_capacity <= 0:
        issues.append("Nonpositive battery_capacity in EV specs")
    if instance.ev_specs.energy_consumption_rate < 0:
        issues.append("Negative energy_consumption_rate in EV specs")

    n = len(instance.nodes)
    if instance.distance_matrix.shape != (n, n):
        issues.append("Distance matrix shape does not match node count")

    return issues


def validate_instance_report(instance: Instance) -> FeasibilityReport:
    """Wrap :func:`validate_instance` as a :class:`FeasibilityReport`."""
    raw = validate_instance(instance)
    report = FeasibilityReport(feasible=len(raw) == 0)
    for msg in raw:
        report.add_issue(msg, scope="instance", details={"instance_key": instance.instance_key})
    return report