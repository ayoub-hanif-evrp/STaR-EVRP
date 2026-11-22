"""Independent solution feasibility checks (no silent repair)."""

from __future__ import annotations

from star_evrp.charge_plan import customer_local_sequence, route_structure_error
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route
from star_evrp.types import (
    FeasibilityReport,
    Instance,
    NodeType,
    NUM_TOL,
    Route,
    Solution,
)


def _validate_customer_coverage(
    instance: Instance,
    routes: list[Route],
    report: FeasibilityReport,
) -> set[int]:
    seen: set[int] = set()
    expected = set(range(instance.num_customers))

    for route in routes:
        if route.stops is not None:
            indices = [
                instance.customer_local_index(stop.node_id) for stop in route.stops
                if stop.node_id in instance.customer_local_indices
            ]
        else:
            indices = route.customer_indices or []
        for loc in indices:
                if loc in seen:
                    report.add_issue(
                        "Duplicate customer local index",
                        scope="customer_coverage",
                        route_id=route.route_id,
                        customer_local=loc,
                    )
                if loc < 0 or loc >= instance.num_customers:
                    report.add_issue(
                        "Customer index out of range",
                        scope="customer_coverage",
                        route_id=route.route_id,
                        customer_local=loc,
                    )
                seen.add(loc)

    missing = expected - seen
    extra = seen - expected
    if missing:
        report.add_issue(
            f"Missing customers: {sorted(missing)[:10]}{'...' if len(missing) > 10 else ''}",
            scope="customer_coverage",
        )
    if extra:
        report.add_issue("Unknown customer indices served", scope="customer_coverage")
    return seen


def validate_route_structure(route: Route, instance: Instance, report: FeasibilityReport) -> None:
    if route.stops is not None:
        error = route_structure_error(instance, route)
        if error:
            report.add_issue(error, route_id=route.route_id, scope="route")


def validate_solution(
    instance: Instance,
    solution: Solution,
    *,
    config: SimulatorConfig | None = None,
) -> FeasibilityReport:
    """Validate fleet, coverage, and per-route physics via independent simulation."""
    report = FeasibilityReport(feasible=True)
    routes = solution.routes

    if len(routes) > instance.fleet_size:
        report.add_issue(
            f"Fleet exceeded: {len(routes)} > {instance.fleet_size}",
            scope="fleet",
        )

    _validate_customer_coverage(instance, routes, report)

    for route in routes:
        validate_route_structure(route, instance, report)

    if config is None:
        config = SimulatorConfig(
            battery_capacity=solution.battery_capacity,
            energy_consumption_rate=solution.energy_consumption_rate,
        )

    total_distance = 0.0
    for route in routes:
        if route.stops is None and any(
            not 0 <= index < instance.num_customers for index in route.customer_indices or []
        ):
            continue
        trace = simulate_route(instance, route, config)
        report.traces.append(trace)
        if not trace.feasible:
            report.add_issue(
                trace.failure_reason or "route_infeasible",
                scope="simulation",
                route_id=route.route_id,
            )
        else:
            total_distance += trace.total_distance

        for stop in trace.stops:
            if stop.battery_on_arrival < -NUM_TOL or stop.battery_on_departure < -NUM_TOL:
                report.add_issue(
                    "Negative battery in trace",
                    scope="battery",
                    route_id=route.route_id,
                    node_id=stop.node_id,
                )
            if stop.battery_on_departure > config.battery_capacity + NUM_TOL:
                report.add_issue(
                    "Battery exceeds capacity",
                    scope="battery",
                    route_id=route.route_id,
                    node_id=stop.node_id,
                )

    if solution.total_distance is not None and report.feasible:
        if abs(solution.total_distance - total_distance) > 1e-2:
            report.add_issue(
                "Recorded total_distance disagrees with simulation",
                scope="solution",
                recorded=solution.total_distance,
                simulated=total_distance,
            )

    return report


def validate_repair(instance: Instance, original: Route, selected: Route, config: SimulatorConfig):
    """Check actual visits and replay the selected plan with the reference simulator."""
    if original.route_id != selected.route_id or route_structure_error(instance, selected):
        raise ValueError("Invalid repaired route structure or route ID")
    if customer_local_sequence(instance, original) != customer_local_sequence(instance, selected):
        raise ValueError("Repair changed customer sequence")
    trace = simulate_route(instance, selected, config)
    if not trace.feasible:
        raise ValueError(f"Invalid repaired route: {trace.failure_reason}")
    return trace
