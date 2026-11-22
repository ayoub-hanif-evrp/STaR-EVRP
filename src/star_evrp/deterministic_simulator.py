"""Deterministic route simulation (fixed plans and baseline nearest-station expansion)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from star_evrp.charge_plan import route_structure_error
from star_evrp.geometry import leg_distance
from star_evrp.types import (
    Instance,
    NodeType,
    NUM_TOL,
    Route,
    RouteTrace,
    RouteTraceStop,
)

# Deposited ``evrptw_solvers._simulate_route`` does **not** enforce station time windows
# during charging; we match that default for baseline expansion and optional explicit mode.
DEFAULT_ENFORCE_STATION_TIME_WINDOWS = False


@dataclass
class SimulatorConfig:
    battery_capacity: float
    energy_consumption_rate: float
    enforce_station_time_windows: bool = DEFAULT_ENFORCE_STATION_TIME_WINDOWS
    max_recharge_legs: int = 500


def _tw_slack(node_due: float, service_start: float) -> float:
    return max(0.0, node_due - service_start)


def _append_trace_stop(
    trace: list[RouteTraceStop],
    *,
    instance: Instance,
    node_id: int,
    arrival: float,
    service_start: float,
    departure: float,
    wait_early: float,
    wait_extra: float,
    service_time: float,
    batt_arr: float,
    batt_dep: float,
    energy_charged: float,
    load: float,
    Q: float,
) -> None:
    node = instance.node(node_id)
    trace.append(
        RouteTraceStop(
            node_id=node_id,
            node_type=node.node_type,
            arrival_time=arrival,
            service_start_time=service_start,
            departure_time=departure,
            wait_time_early=wait_early,
            wait_time_extra=wait_extra,
            service_time=service_time,
            battery_on_arrival=batt_arr,
            battery_on_departure=batt_dep,
            energy_charged=energy_charged,
            load_after_service=load,
            tw_slack_remaining=_tw_slack(node.due_date, service_start),
            battery_slack_remaining=max(0.0, Q - batt_dep),
            charging_rate=(
                instance.charging_rate(node_id)
                if node.node_type == NodeType.STATION
                else None
            ),
        )
    )


def _travel_leg(
    instance: Instance,
    current_id: int,
    target_id: int,
    battery: float,
    clock: float,
    h: float,
) -> tuple[float, float, float, bool]:
    """Returns (new_battery, new_clock, leg_distance, ok)."""
    d = leg_distance(instance, current_id, target_id)
    need = h * d
    if need > battery + NUM_TOL:
        return battery, clock, d, False
    return battery - need, clock + d, d, True


def _charge_at_station(
    instance: Instance,
    station_id: int,
    arrival: float,
    battery: float,
    Q: float,
    energy_charged: float | None,
    wait_extra: float,
    enforce_station_tw: bool,
) -> tuple[float, float, float, float, float, float, float, str | None]:
    """Returns clock, battery, wait_early, wait_extra, charge_dur, energy_added, service_start, err."""
    node = instance.node(station_id)
    rate = instance.charging_rate(station_id)
    wait_early = 0.0
    service_start = arrival
    if enforce_station_tw and arrival < node.ready_time:
        wait_early = node.ready_time - arrival
        service_start = node.ready_time

    clock = service_start + max(0.0, wait_extra)
    if energy_charged is None:
        # Full recharge to capacity (explicit None convention).
        energy_added = max(0.0, Q - battery)
        battery_after = Q
    else:
        # Explicit amount must be physically exact — never clamp.
        if not np.isfinite(energy_charged):
            return clock, battery, wait_early, wait_extra, 0.0, 0.0, service_start, "invalid_charge_amount"
        if energy_charged < -NUM_TOL:
            return clock, battery, wait_early, wait_extra, 0.0, 0.0, service_start, "negative_charge"
        energy_added = float(energy_charged)
        if energy_added < 0.0:
            energy_added = 0.0
        battery_after = battery + energy_added
        if battery_after > Q + NUM_TOL:
            return clock, battery, wait_early, wait_extra, 0.0, 0.0, service_start, "overcharge"

    if energy_added > NUM_TOL and (not np.isfinite(rate) or rate <= 0):
        return clock, battery, wait_early, wait_extra, 0.0, 0.0, service_start, "invalid_rate"

    charge_dur = energy_added / rate if energy_added > NUM_TOL else 0.0
    clock += charge_dur
    if enforce_station_tw and clock > node.due_date + NUM_TOL:
        return clock, battery, wait_early, wait_extra, charge_dur, energy_added, service_start, "station_closing"
    return clock, battery_after, wait_early, wait_extra, charge_dur, energy_added, service_start, None


def _serve_customer(
    instance: Instance,
    customer_id: int,
    arrival: float,
    battery: float,
    load: float,
    load_cap: float,
    t_close: float,
) -> tuple[float, float, float, float, float, float, float, str | None]:
    node = instance.node(customer_id)
    if load + node.demand > load_cap + NUM_TOL:
        return arrival, battery, load, 0.0, 0.0, 0.0, 0.0, "load_capacity"
    service_start = max(arrival, node.ready_time)
    if service_start > node.due_date + NUM_TOL:
        return arrival, battery, load, 0.0, 0.0, 0.0, 0.0, "customer_time_window"
    depart = service_start + node.service_time
    if depart > t_close + NUM_TOL:
        return arrival, battery, load, 0.0, 0.0, 0.0, 0.0, "depot_closing"
    load2 = load + node.demand
    wait_early = max(0.0, node.ready_time - arrival)
    return depart, battery, load2, wait_early, 0.0, node.service_time, service_start, None


def simulate_route_fixed(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
) -> RouteTrace:
    """Simulate an explicit node sequence including charging stations.

    Visit order: travel -> arrival -> (optional station ready wait) -> ``wait_extra`` ->
    charging (``energy_charged`` on stop, or full recharge if ``None``) -> departure.
    """
    Q = float(config.battery_capacity)
    h = float(config.energy_consumption_rate)
    stops = route.stops or []
    route_id = route.route_id

    structural_error = route_structure_error(instance, route)
    if structural_error:
        return RouteTrace(
            route_id=route_id,
            feasible=False,
            failure_reason=structural_error,
            total_distance=0.0,
            num_charging_visits=0,
            end_node_id=0,
            end_battery=Q,
            end_clock=0.0,
            end_load=0.0,
            stops=[],
        )

    current = stops[0].node_id
    if instance.node(current).node_type != NodeType.DEPOT:
        return RouteTrace(
            route_id=route_id,
            feasible=False,
            failure_reason="route_must_start_at_depot",
            total_distance=0.0,
            num_charging_visits=0,
            end_node_id=current,
            end_battery=0.0,
            end_clock=0.0,
            end_load=0.0,
        )

    battery = Q
    clock = 0.0
    load = 0.0
    total_dist = 0.0
    charges = 0
    trace_stops: list[RouteTraceStop] = []

    for idx, stop in enumerate(stops):
        if idx == 0:
            _append_trace_stop(
                trace_stops,
                instance=instance,
                node_id=stop.node_id,
                arrival=0.0,
                service_start=0.0,
                departure=0.0,
                wait_early=0.0,
                wait_extra=0.0,
                service_time=0.0,
                batt_arr=Q,
                batt_dep=Q,
                energy_charged=0.0,
                load=0.0,
                Q=Q,
            )
            continue

        target = stop.node_id
        battery, clock, leg_d, ok = _travel_leg(instance, current, target, battery, clock, h)
        if not ok:
            return RouteTrace(
                route_id=route_id,
                feasible=False,
                failure_reason="battery_infeasible_leg",
                total_distance=total_dist,
                num_charging_visits=charges,
                end_node_id=current,
                end_battery=battery,
                end_clock=clock,
                end_load=load,
                stops=trace_stops,
            )
        total_dist += leg_d
        arrival = clock
        ntype = instance.node(target).node_type

        if ntype == NodeType.STATION:
            clock, battery, wait_early, wait_extra, _cd, energy_added, svc_start, err = (
                _charge_at_station(
                    instance,
                    target,
                    arrival,
                    battery,
                    Q,
                    stop.energy_charged,
                    stop.wait_extra,
                    config.enforce_station_time_windows,
                )
            )
            if err:
                return RouteTrace(
                    route_id=route_id,
                    feasible=False,
                    failure_reason=err,
                    total_distance=total_dist,
                    num_charging_visits=charges,
                    end_node_id=target,
                    end_battery=battery,
                    end_clock=clock,
                    end_load=load,
                    stops=trace_stops,
                )
            if energy_added > NUM_TOL:
                charges += 1
            _append_trace_stop(
                trace_stops,
                instance=instance,
                node_id=target,
                arrival=arrival,
                service_start=svc_start,
                departure=clock,
                wait_early=wait_early,
                wait_extra=wait_extra,
                service_time=0.0,
                batt_arr=battery - energy_added if energy_added else battery,
                batt_dep=battery,
                energy_charged=energy_added,
                load=load,
                Q=Q,
            )
        elif ntype == NodeType.CUSTOMER:
            batt_arr = battery
            depart, battery, load, wait_early, wait_extra, svc_t, svc_start, err = (
                _serve_customer(
                    instance, target, arrival, battery, load, instance.load_capacity, instance.depot_closing_time
                )
            )
            if err:
                return RouteTrace(
                    route_id=route_id,
                    feasible=False,
                    failure_reason=err,
                    total_distance=total_dist,
                    num_charging_visits=charges,
                    end_node_id=target,
                    end_battery=battery,
                    end_clock=clock,
                    end_load=load,
                    stops=trace_stops,
                )
            clock = depart
            _append_trace_stop(
                trace_stops,
                instance=instance,
                node_id=target,
                arrival=arrival,
                service_start=svc_start,
                departure=clock,
                wait_early=wait_early,
                wait_extra=wait_extra,
                service_time=svc_t,
                batt_arr=batt_arr,
                batt_dep=battery,
                energy_charged=0.0,
                load=load,
                Q=Q,
            )
        elif ntype == NodeType.DEPOT:
            _append_trace_stop(
                trace_stops,
                instance=instance,
                node_id=target,
                arrival=arrival,
                service_start=arrival,
                departure=arrival,
                wait_early=0.0,
                wait_extra=0.0,
                service_time=0.0,
                batt_arr=battery,
                batt_dep=battery,
                energy_charged=0.0,
                load=load,
                Q=Q,
            )
            if arrival > instance.depot_closing_time + NUM_TOL:
                return RouteTrace(
                    route_id=route_id,
                    feasible=False,
                    failure_reason="depot_closing",
                    total_distance=total_dist,
                    num_charging_visits=charges,
                    end_node_id=target,
                    end_battery=battery,
                    end_clock=clock,
                    end_load=load,
                    stops=trace_stops,
                )
        else:
            return RouteTrace(
                route_id=route_id,
                feasible=False,
                failure_reason="unknown_node_type",
                total_distance=total_dist,
                num_charging_visits=charges,
                end_node_id=target,
                end_battery=battery,
                end_clock=clock,
                end_load=load,
                stops=trace_stops,
            )
        current = target

    if battery < -NUM_TOL:
        feasible = False
        reason: str | None = "battery_negative"
    else:
        feasible = True
        reason = None

    return RouteTrace(
        route_id=route_id,
        feasible=feasible,
        failure_reason=reason,
        total_distance=total_dist,
        num_charging_visits=charges,
        end_node_id=current,
        end_battery=battery,
        end_clock=clock,
        end_load=load,
        stops=trace_stops,
    )


def simulate_route_baseline_expansion(
    instance: Instance,
    customer_locals: list[int],
    config: SimulatorConfig,
    *,
    route_id: int = 0,
) -> RouteTrace:
    """Match deposited ``_simulate_route``: nearest reachable station, full recharge, no station TW.

    ``customer_locals`` are indices into ``instance.customer_node_ids``.
    """
    Q = float(config.battery_capacity)
    h = float(config.energy_consumption_rate)
    dist = instance.distance_matrix
    station_ids = instance.station_node_ids
    station_indices = [instance.node_id_to_index[s] for s in station_ids]
    charging_rate = np.asarray(
        [instance.charging_rate(s) for s in station_ids], dtype=np.float64
    )
    current = 0
    battery = Q
    clock = 0.0
    load = 0.0
    total_dist = 0.0
    charges = 0
    recharge_legs = 0
    trace_stops: list[RouteTraceStop] = []

    _append_trace_stop(
        trace_stops,
        instance=instance,
        node_id=0,
        arrival=0.0,
        service_start=0.0,
        departure=0.0,
        wait_early=0.0,
        wait_extra=0.0,
        service_time=0.0,
        batt_arr=Q,
        batt_dep=Q,
        energy_charged=0.0,
        load=0.0,
        Q=Q,
    )

    def go_to_station_for_energy(target_index: int) -> bool:
        nonlocal current, battery, clock, total_dist, charges, recharge_legs
        while h * dist[current, target_index] > battery + NUM_TOL:
            d_to_s = dist[current, station_indices]
            ok = h * d_to_s <= battery
            if not np.any(ok):
                return False
            si = int(np.argmin(np.where(ok, d_to_s, np.inf)))
            leg = float(d_to_s[si])
            station_index = station_indices[si]
            station_id = station_ids[si]
            total_dist += leg
            batt_before = battery
            battery -= h * leg
            need = Q - battery
            travel_end = clock + leg
            arrival = travel_end
            clock = travel_end
            if need > NUM_TOL:
                clock += need / float(charging_rate[si])
            battery = Q
            charges += 1
            recharge_legs += 1
            _append_trace_stop(
                trace_stops,
                instance=instance,
                node_id=station_id,
                arrival=arrival,
                service_start=arrival,
                departure=clock,
                wait_early=0.0,
                wait_extra=0.0,
                service_time=0.0,
                batt_arr=batt_before - h * leg,
                batt_dep=Q,
                energy_charged=need,
                load=load,
                Q=Q,
            )
            current = station_index
            if recharge_legs > config.max_recharge_legs:
                return False
        return True

    if not customer_locals:
        return RouteTrace(
            route_id=route_id,
            feasible=True,
            failure_reason=None,
            total_distance=0.0,
            num_charging_visits=0,
            end_node_id=0,
            end_battery=Q,
            end_clock=0.0,
            end_load=0.0,
            stops=trace_stops,
        )

    ready = np.asarray(
        [instance.node(cid).ready_time for cid in instance.customer_node_ids],
        dtype=np.float64,
    )
    due = np.asarray(
        [instance.node(cid).due_date for cid in instance.customer_node_ids],
        dtype=np.float64,
    )
    dem = np.asarray(
        [instance.node(cid).demand for cid in instance.customer_node_ids], dtype=np.float64
    )
    svc = np.asarray(
        [instance.node(cid).service_time for cid in instance.customer_node_ids],
        dtype=np.float64,
    )
    t_close = instance.depot_closing_time
    load_cap = instance.load_capacity

    for loc in customer_locals:
        if loc < 0 or loc >= instance.num_customers:
            return RouteTrace(
                route_id=route_id,
                feasible=False,
                failure_reason="invalid_customer_index",
                total_distance=0.0,
                num_charging_visits=charges,
                end_node_id=instance.nodes[current].node_id,
                end_battery=battery,
                end_clock=clock,
                end_load=load,
                stops=trace_stops,
            )
        target_index = instance.node_id_to_index[instance.customer_node_ids[loc]]
        target_id = instance.customer_node_ids[loc]

        if load + dem[loc] > load_cap + NUM_TOL:
            return RouteTrace(
                route_id=route_id,
                feasible=False,
                failure_reason="load_capacity",
                total_distance=total_dist,
                num_charging_visits=charges,
                end_node_id=instance.nodes[current].node_id,
                end_battery=battery,
                end_clock=clock,
                end_load=load,
                stops=trace_stops,
            )

        if not go_to_station_for_energy(target_index):
            return RouteTrace(
                route_id=route_id,
                feasible=False,
                failure_reason="battery_infeasible_recharge",
                total_distance=total_dist,
                num_charging_visits=charges,
                end_node_id=instance.nodes[current].node_id,
                end_battery=battery,
                end_clock=clock,
                end_load=load,
                stops=trace_stops,
            )

        leg = float(dist[current, target_index])
        total_dist += leg
        batt_arr = battery
        battery -= h * leg
        arrival = clock + leg
        start = max(arrival, ready[loc])
        if start > due[loc] + NUM_TOL:
            return RouteTrace(
                route_id=route_id,
                feasible=False,
                failure_reason="customer_time_window",
                total_distance=total_dist,
                num_charging_visits=charges,
                end_node_id=target_id,
                end_battery=battery,
                end_clock=clock,
                end_load=load,
                stops=trace_stops,
            )
        if start + svc[loc] > t_close + NUM_TOL:
            return RouteTrace(
                route_id=route_id,
                feasible=False,
                failure_reason="depot_closing",
                total_distance=total_dist,
                num_charging_visits=charges,
                end_node_id=target_id,
                end_battery=battery,
                end_clock=clock,
                end_load=load,
                stops=trace_stops,
            )
        clock = start + svc[loc]
        load += dem[loc]
        current = target_index
        _append_trace_stop(
            trace_stops,
            instance=instance,
            node_id=target_id,
            arrival=arrival,
            service_start=start,
            departure=clock,
            wait_early=max(0.0, ready[loc] - arrival),
            wait_extra=0.0,
            service_time=float(svc[loc]),
            batt_arr=batt_arr,
            batt_dep=battery,
            energy_charged=0.0,
            load=load,
            Q=Q,
        )

    if not go_to_station_for_energy(0):
        return RouteTrace(
            route_id=route_id,
            feasible=False,
            failure_reason="cannot_return_depot",
            total_distance=total_dist,
            num_charging_visits=charges,
            end_node_id=instance.nodes[current].node_id,
            end_battery=battery,
            end_clock=clock,
            end_load=load,
            stops=trace_stops,
        )

    leg_back = float(dist[current, 0])
    total_dist += leg_back
    battery -= h * leg_back
    clock += leg_back
    if clock > t_close + NUM_TOL:
        return RouteTrace(
            route_id=route_id,
            feasible=False,
            failure_reason="depot_closing",
            total_distance=total_dist,
            num_charging_visits=charges,
            end_node_id=0,
            end_battery=battery,
            end_clock=clock,
            end_load=load,
            stops=trace_stops,
        )

    _append_trace_stop(
        trace_stops,
        instance=instance,
        node_id=0,
        arrival=clock,
        service_start=clock,
        departure=clock,
        wait_early=0.0,
        wait_extra=0.0,
        service_time=0.0,
        batt_arr=battery + h * leg_back,
        batt_dep=battery,
        energy_charged=0.0,
        load=load,
        Q=Q,
    )

    return RouteTrace(
        route_id=route_id,
        feasible=True,
        failure_reason=None,
        total_distance=total_dist,
        num_charging_visits=charges,
        end_node_id=0,
        end_battery=battery,
        end_clock=clock,
        end_load=load,
        stops=trace_stops,
    )


def simulate_route(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
) -> RouteTrace:
    """Dispatch to explicit-stop or baseline-expansion semantics."""
    if route.stops is not None:
        return simulate_route_fixed(instance, route, config)
    if route.customer_indices is not None:
        return simulate_route_baseline_expansion(
            instance, list(route.customer_indices), config, route_id=route.route_id
        )
    return RouteTrace(
        route_id=route.route_id,
        feasible=False,
        failure_reason="empty_route_definition",
        total_distance=0.0,
        num_charging_visits=0,
        end_node_id=0,
        end_battery=0.0,
        end_clock=0.0,
        end_load=0.0,
    )
