"""Independent solution feasibility checks (no silent repair)."""

from __future__ import annotations

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
        if route.customer_indices is not None:
            for loc in route.customer_indices:
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
        elif route.stops:
            for stop in route.stops:
                node = instance.node(stop.node_id)
                if node.node_type == NodeType.CUSTOMER:
                    loc = instance.customer_local_index(stop.node_id)
                    if loc in seen:
                        report.add_issue(
                            "Duplicate customer in explicit stops",
                            scope="customer_coverage",
                            route_id=route.route_id,
                            node_id=stop.node_id,
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
    if route.uses_explicit_stops():
        stops = route.stops or []
        if not stops:
            report.add_issue("Explicit route has no stops", route_id=route.route_id, scope="route")
            return
        if stops[0].node_id != 0:
            report.add_issue("Route must start at depot", route_id=route.route_id, scope="route")
        if stops[-1].node_id != 0:
            report.add_issue("Route must end at depot", route_id=route.route_id, scope="route")
        for stop in stops:
            if stop.node_id not in instance.node_id_to_index:
                report.add_issue(
                    "Unknown node in route",
                    route_id=route.route_id,
                    node_id=stop.node_id,
                    scope="route",
                )


def validate_solution(
    instance: Instance,
    solution: Solution,
    *,
    config: SimulatorConfig | None = None,
) -> FeasibilityReport:
    """Validate fleet, coverage, and per-route physics via independent simulation."""
    report = FeasibilityReport(feasible=True)
    routes = [r for r in solution.routes if r.customer_indices or r.stops]

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