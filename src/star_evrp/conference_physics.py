
"""Reconstruct zero-wait traces of saved routes without scoring or optimizing them."""

from collections import Counter
from math import hypot, isclose
from statistics import median_low

from star_evrp.charge_plan import ChargePlan, customer_node_ids
from star_evrp.phase3 import _route
from star_evrp.phase4_results import canonical, plan_link, require, sha
from star_evrp.phase5_experiments import case_inputs
from star_evrp.types import NUM_TOL


def example_candidates(features):
    """Freeze the deterministic, outcome-selected example rules before rendering."""
    holdout = [r for r in features.values() if r["partition"] == "holdout" and r["exposed"] == "True"]
    multi = [r for r in holdout if int(r["source_visits"]) >= 3]
    options = []
    for r in multi:
        gain = int(r["STaR_successes"]) - int(r["CON_successes"])
        changed = r["topology_changed"] == "True"
        preferred = r["family"] in ("R2", "RC2")
        attained = r["STaR_attained"] == "True"
        if gain > 0 and changed and attained:
            tier = 1 if preferred else 2
        elif gain > 0 and changed:
            tier = 3
        elif gain > 0:
            tier = 4
        else:
            tier = 5
        options.append(dict(parent=r["parent"], variant=r["variant"], route=int(r["route"]), family=r["family"],
                            customers=int(r["customers"]), tier=tier, original_visits=int(r["source_visits"]),
                            selected_visits=int(r["selected_visits"]), gain_successes=gain,
                            topology_changed=changed, star_attained=attained))
    require(options, "No complex routes in holdout archive")
    order = lambda r: (r["parent"], r["variant"], r["route"])
    options.sort(key=order)
    tier = min(r["tier"] for r in options)
    pool = [r for r in options if r["tier"] == tier]
    count = median_low([r["customers"] for r in pool])
    choice = next(r for r in pool if r["customers"] == count)
    complex_rule = dict(chosen=choice, candidate_count=len(pool), tier_counts=dict(Counter(r["tier"] for r in options)),
                        rule="First parent, variant and route at lower median customer count in first nonempty tier. "
                             "Tiers: improved + topology changed + attained in R2/RC2; same any family; improved + "
                             "topology changed; improved; any route. All require at least 3 original visits.",
                        example_scope="Outcome-selected, exploratory illustration")
    return complex_rule, options


def deteriorated_candidates(rows, keys):
    options = []
    for k in keys:
        a, b = (rows[*k, m]["validation"] for m in ("FSPC", "STaR"))
        require(a["n"] == b["n"] == 10000, "Unmatched diagnostic denominators")
        if b["successes"] < a["successes"]:
            options.append(dict(parent=k[0], variant=k[1], route=k[2], gain_successes=b["successes"]-a["successes"],
                                control_attained=a["attained"], star_attained=b["attained"]))
    options.sort(key=lambda r: (r["gain_successes"], r["parent"], r["variant"], r["route"]))
    require(options, "No deteriorated holdout comparison")
    return dict(chosen=options[0], candidate_count=len(options),
                rule="Largest observed reliability loss versus fixed-station repair among the negative paired "
                     "holdout contrasts, then parent, variant and route ID.",
                example_scope="Outcome-selected, exploratory adverse example"), options


def assert_close(found, expected, description):
    require(isclose(found, expected, abs_tol=NUM_TOL, rel_tol=0), description)


def physical_events(instance, physics, trace, method):
    """Independently check Euclidean travel, energy, charging duration and clock accounting."""
    events = []
    distance = 0.0
    customers = visits = 0
    for i, event in enumerate(trace.stops):
        node = instance.node(event.node_id)
        kind = node.node_type.value
        leg = 0.0 if i == 0 else hypot(node.x-events[-1]["x"], node.y-events[-1]["y"])
        distance += leg
        prev_energy = physics.battery_capacity if i == 0 else events[-1]["battery_departure"]
        consumed = physics.energy_consumption_rate * leg
        assert_close(event.battery_on_arrival, prev_energy-consumed, "Route leg energy balance")
        assert_close(event.battery_on_departure, event.battery_on_arrival+event.energy_charged, "Stop energy balance")
        require(-NUM_TOL <= min(event.battery_on_arrival, event.battery_on_departure)
                <= max(event.battery_on_arrival, event.battery_on_departure) <= physics.battery_capacity+NUM_TOL,
                "Validated energy outside tolerance")
        assert_close(event.wait_time_extra, 0, "Nonzero station wait in deterministic trace")
        if kind == "customer":
            customers += 1
        if kind == "station":
            visits += 1
        charge_time = (event.energy_charged/event.charging_rate
                       if kind == "station" and event.energy_charged > NUM_TOL else 0.0)
        elapsed = event.wait_time_early + charge_time + event.service_time
        assert_close(event.departure_time-event.arrival_time, elapsed, "Stop clock balance")
        if i:
            assert_close(event.arrival_time-events[-1]["departure"], leg, "Route leg clock balance")
        events.append(dict(plan=method,index=i,node=node.node_id,type=kind,x=node.x,y=node.y,
                           customer_order=customers if kind == "customer" else None,
                           station_order=visits if kind == "station" else None, customers_served=customers,
                           leg_distance=leg,distance=distance,consumed=consumed,charged=event.energy_charged,
                           battery_arrival=event.battery_on_arrival,battery_departure=event.battery_on_departure,
                           arrival=event.arrival_time,service_start=event.service_start_time,departure=event.departure_time,
                           ready=node.ready_time,due=node.due_date,readiness_wait=event.wait_time_early,
                           service_duration=event.service_time,charging_rate=event.charging_rate,
                           charging_duration=charge_time,
                           deadline_slack=node.due_date-event.service_start_time
                           if kind == "customer" or (kind == "depot" and i) else None))
    totals = dict(method=method,capacity=physics.battery_capacity,consumption_rate=physics.energy_consumption_rate,
                  tolerance=NUM_TOL,customers=customers,visits=visits,total_distance=distance,
                  energy_consumed=sum(r["consumed"] for r in events),energy_added=sum(r["charged"] for r in events),
                  initial_battery=events[0]["battery_arrival"],final_battery=events[-1]["battery_departure"],
                  depot_start=events[0]["departure"],zero_wait_return=trace.end_clock,
                  charging_duration=sum(r["charging_duration"] for r in events),
                  readiness_wait=sum(r["readiness_wait"] for r in events[1:]),
                  service_duration=sum(r["service_duration"] for r in events[1:]))
    assert_close(distance, trace.total_distance, "Validator distance")
    require(visits == trace.num_charging_visits, "Validator station count")
    assert_close(totals["final_battery"], trace.end_battery, "Validator final battery")
    assert_close(totals["initial_battery"], physics.battery_capacity, "Start at capacity")
    assert_close(totals["initial_battery"]+totals["energy_added"]-totals["energy_consumed"],
                 totals["final_battery"], "Whole route energy balance")
    assert_close(totals["depot_start"]+distance+totals["charging_duration"]+totals["readiness_wait"]+
                 totals["service_duration"], trace.end_clock, "Whole route clock balance")
    return events, totals


def route_example(root, rows, plans, freeze, selection, methods):
    """Read matching saved plans and validation rows and tie them to original coordinates."""
    from star_evrp.route_validator import validate_repair

    chosen = selection["chosen"]
    k = chosen["parent"], chosen["variant"], chosen["route"]
    case = next(r for r in freeze["holdout"] if (r["parent_key"], r["variant"]) == k[:2])
    instance, physics, original, _, base_hash = case_inputs(root, case, freeze["config"], sha(canonical(freeze)))
    baseline = _route(original[k[2]])
    nodes = [dict(node=n.node_id,type=n.node_type.value,x=n.x,y=n.y) for n in instance.nodes]
    require(sum(n["type"] == "customer" for n in nodes) == 1000, "Example benchmark case size")
    stops, metrics, totals = [], [], []
    sources = [instance.instance_path.relative_to(root).as_posix(), instance.stations_path.relative_to(root).as_posix()]
    for method in methods:
        row, plan = rows[*k,method], plans["holdout",*k,method]
        plan_link(row, plan, original[k[2]])
        sources.extend((row["source"], row["source"].replace("/raw/", "/plans/")))
        route = _route(plan)
        trace = validate_repair(instance, baseline, route, physics)
        customers = customer_node_ids(instance, route)
        require(customers == customer_node_ids(instance, baseline) and route.route_id == k[2], "Changed customers or route")
        fp = ChargePlan.from_route(instance, route).fingerprint()
        require(fp == plan["fingerprint"] and trace.end_clock == plan["zero_wait_completion"], "Replay mismatch")
        events, summary = physical_events(instance, physics, trace, method)
        require([(r["node"], r["type"], r["charged"]) for r in events] ==
                [(e[0], e[1], e[4]) for e in plan["events"]], "Stop order or amount differs from archive")
        stops.extend(events)
        totals.append(summary)
        v = row["validation"]
        both = v["late_both"]
        metrics.append(dict(method=method,successes=v["successes"],scenarios=v["n"],reliability=v["reliability"],
                            completion=v["completion"],wilson_lower=v["wilson95_lower_one_sided"],attained=v["attained"],
                            customer_only=v["late_customer"]-both,depot_only=v["late_depot"]-both,joint=both,
                            tape_seed=v["tape_seed"],fingerprint=fp,plan_digest=row["plan_sha256"],source=row["source"]))
    require(len({m["tape_seed"] for m in metrics}) == 1, "Example validation is not paired")
    for m in metrics:
        require(m["successes"]+m["customer_only"]+m["depot_only"]+m["joint"] == m["scenarios"], "Failure tally")
    return dict(selection=dict(selection, con_bundle_member=f"raw/con/{k[0]}__{k[1]}.json.gz",
                               con_bundle_member_sha256=base_hash, instance_sha256=case["instance_sha256"],
                               stations_sha256=case["stations_sha256"], customer_order=customers),
                nodes=nodes, stops=stops, metrics=metrics, totals=totals, paths=sources)
