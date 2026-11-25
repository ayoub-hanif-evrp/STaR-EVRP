"""All-route archived mechanism features and paired descriptive evidence."""

from collections import Counter
from statistics import fmean

import numpy as np

from star_evrp.charge_plan import ChargePlan, customer_node_ids
from star_evrp.competitive_search import Neighborhood
from star_evrp.deterministic_simulator import simulate_route_fixed
from star_evrp.phase3 import _route
from star_evrp.phase4_results import bootstrap, canonical, failure_reason, grouped, plan_link, require, require_keys, sha
from star_evrp.phase6_archive import case_key, contexts, csv_rows, key, load_archive, write_csv, write_json
from star_evrp.route_validator import validate_repair
from star_evrp.timing import RouteTiming
from star_evrp.types import NUM_TOL, NodeType, Route, RouteStop

COMPARATORS = ("CON","QBR","FSPC","SLS")
COHORTS = ("all120","development","holdout")


def plan_features(instance, route, trace, physics):
    timing = RouteTiming.from_trace(instance,trace,physics)
    customers, stops, events = customer_node_ids(instance,route),[],[]
    gap = 0
    for index,event in enumerate(trace.stops):
        if event.node_type==NodeType.CUSTOMER:
            gap += 1
        if event.node_type==NodeType.STATION:
            stops.append((gap,event.node_id))
            events.append((index,event))
    amounts = [float(event.energy_charged) for _,event in events]
    return timing,customers,stops,amounts,events


def _plan_fields(prefix, stations, amounts):
    n = len(stations)
    positive = sum(q > NUM_TOL for q in amounts)
    return {prefix+"visits":n,prefix+"distinct_stations":len({s for _,s in stations}),
            prefix+"positive_charge_visits":positive,prefix+"zero_quantity_visits":sum(q==0 for q in amounts),
            prefix+"small_positive_visits":sum(0 < q <= NUM_TOL for q in amounts),
            prefix+"energy":sum(amounts), prefix+"topology":canonical(stations).decode()}


def features(instance, physics, original, archived_plan, base, star):
    source = _route(original)
    trace = simulate_route_fixed(instance,source,physics)
    require(trace.feasible,"Source route failed replay")
    timing,customers,stations,amounts,events = plan_features(instance,source,trace,physics)
    n = len(stations)
    indices = [instance.index_of(i) for i in (0,*customers,0)]
    customer_distance = float(instance.distance_matrix[indices[:-1],indices[1:]].sum())
    plain = Route(source.route_id,source.customer_indices,[RouteStop(i) for i in (0,*customers,0)])
    stripped = simulate_route_fixed(instance,plain,physics)
    ready = [instance.node(node).ready_time for node in customers]
    due = [instance.node(node).due_date for node in customers]
    customer_events = [e for e in trace.stops if e.node_type==NodeType.CUSTOMER]
    caps = timing.isolated_caps(trace)
    source_fp = ChargePlan.from_route(instance,source).fingerprint()
    require(abs(timing.evaluate(np.zeros((1,n)))[1][0]-trace.end_clock)<=1e-8,"Feature clock drift")
    row = {"source_fingerprint":source_fp,"customers":len(customers),"customer_distance":customer_distance,
           "source_distance":trace.total_distance,"detour_distance":trace.total_distance-customer_distance,
           "total_service":sum(e.service_time for e in customer_events),"depot_deadline":instance.depot_closing_time,
           "customer_horizon":max(due)-min(ready) if customers else None,
           "source_zero_wait_return":trace.end_clock,"depot_slack":instance.depot_closing_time-trace.end_clock,
           "min_customer_slack":min((d-e.service_start_time for d,e in zip(due,customer_events,strict=True)),default=None),
           "min_isolated_wait_cap":float(caps.min()) if n else None,
           "isolated_wait_caps":canonical(caps.tolist()).decode(),
           "source_charging_time":sum(s.duration for s in timing.steps if s.slot is not None),
           "mean_visit_wait":float(np.exp(timing.mus+timing.sigmas**2/2).mean()) if n else None,
           "mean_visit_log_sigma":float(timing.sigmas.mean()) if n else None,
           "stripped_energy_feasible":bool(customer_distance*physics.energy_consumption_rate<=physics.battery_capacity+NUM_TOL),
           "stripped_full_feasible":stripped.feasible,
           "min_visits_energy_lower_bound":max(0,int(np.ceil((customer_distance*physics.energy_consumption_rate)/
                                           (physics.battery_capacity+NUM_TOL)))-1),
           **_plan_fields("source_",stations,amounts)}
    if n==0:
        return row
    require(base is not None and star is not None,"Exposed route missing Phase 5 comparisons")
    row["local_two_leg_nearby"] = sum(len(Neighborhood(instance,physics,3).alternatives(
        source.stops[i-1].node_id,source.stops[i+1].node_id,
        {source.stops[j].node_id for j in (i-1,i,i+1)})) for i,_ in events)
    selected = _route(archived_plan)
    selected_trace = validate_repair(instance,source,selected,physics)
    _,after_customers,new,new_amounts,_ = plan_features(instance,selected,selected_trace,physics)
    require(customers==after_customers and archived_plan["fingerprint"]==ChargePlan.from_route(instance,selected).fingerprint(),
            "Selected planned fingerprint or customer sequence mismatch")
    row.update(_plan_fields("selected_",new,new_amounts))
    row.update(selected_fingerprint=archived_plan["fingerprint"],exact_plan_equal=archived_plan["fingerprint"]==source_fp,
               gap_sequence_changed=[g for g,_ in stations]!=[g for g,_ in new],
               station_id_sequence_changed=[s for _,s in stations]!=[s for _,s in new],
               topology_changed=stations!=new,
               matched_quantity_changed=any(abs(a-b)>NUM_TOL for a,b in zip(amounts,new_amounts,strict=True)) if stations==new else None,
               delta_charge_energy=sum(new_amounts)-sum(amounts),delta_distance=selected_trace.total_distance-trace.total_distance,
               selected_zero_wait_return=selected_trace.end_clock)
    for label,record in (("CON",base),("STaR",star)):
        metrics=record["validation"]
        row.update({f"{label}_R":metrics["reliability"],f"{label}_successes":metrics["successes"],
                    f"{label}_completion":metrics["completion"], f"{label}_LB":metrics["wilson95_lower_one_sided"],
                    f"{label}_attained":metrics["attained"], f"{label}_failure":failure_reason(metrics),
                    f"{label}_customer_only":metrics["late_customer"]-metrics["late_both"],
                    f"{label}_depot_only":metrics["late_depot"]-metrics["late_both"],
                    f"{label}_joint":metrics["late_both"],
                    f"{label}_straddles":metrics["wilson95_two_sided"][0]<=.95<=metrics["wilson95_two_sided"][1]})
    return row


def summarize_direction(values,tolerance):
    signs = [1 if d>tolerance else -1 if d<-tolerance else 0 for d in values]
    gains,losses = ([d for d,s in zip(values,signs,strict=True) if s==sign] for sign in (1,-1))
    a = np.quantile(values,(0,.05,.25,.5,.75,.95,1)) if values else [None]*7
    n = len(values)
    return {"n":n,"gains":len(gains),"ties":signs.count(0),"losses":len(losses),
            "mean_signed":fmean(values) if values else None,
            "gain_mean":fmean(gains) if gains else None,"loss_mean":fmean(losses) if losses else None,
            "gain_contribution":sum(gains)/n if n else None,"loss_contribution":sum(losses)/n if n else None,
            **dict(zip(("min","p05","p25","median","p75","p95","max"),map(lambda v:None if v is None else float(v),a)))}


def ia_estimate(rows, metric, parents, policy):
    blocks = {r["parent"] for r in rows}
    n = len(rows)
    pairs = [(r["parent"],r[metric]) for r in rows]
    if len(blocks)<policy["min_interval_parents"]:
        vals = grouped(pairs,lambda r:r[0])
        return dict(n=n,parents=len(blocks),mean=fmean(r[1] for r in pairs) if n else None,
                    lo95=None,hi95=None,parent_mean=fmean(fmean(v for _,v in rr) for rr in vals.values()) if n else None,
                    parent_lo95=None,parent_hi95=None)
    result = bootstrap(pairs,parents,seed=policy["bootstrap_seed"],replicates=policy["bootstrap_draws"])
    return dict(n=n,parents=len(blocks),**dict(zip(("mean","lo95","hi95","parent_mean","parent_lo95","parent_hi95"),result)))


def diagnose(root,out,protocol):
    records,plans,evidence = load_archive(root)
    policy=protocol["configuration"]
    all_features,paired,population = [],[],[]
    methods = (*COMPARATORS,"MWR","STaR","STaR-NPC","STaR-NSP","STaR-NAS","STaR-NPP")
    for case,instance,physics,original,source_hash in contexts(root,protocol["freeze_digest"]):
        part,parent,variant = case_key(case)
        pop = Counter()
        for rid,route in sorted(original.items()):
            k = part,parent,variant,rid
            exposed = any(s["node_id"] in instance.station_attributes for s in route["stops"])
            base,star = [records.get((*k,m)) for m in ("CON","STaR")]
            row = dict(partition=part,parent=parent,variant=variant,route=rid,family=case["family"],instance=f"{parent}/{variant}",
                       source_archive="Phase2.5 CON" if part=="development" else "Phase3 con_bundles.zip",
                       archive_sha256=source_hash, source_route_sha256=sha(canonical(route)),exposed=exposed,
                       selected_archive=star["source"] if star else None,selected_plan_sha256=star["plan_sha256"] if star else None,
                       **features(instance,physics,route,plans.get((*k,"STaR")),base,star))
            pop.update(all_routes=1,exposed=int(exposed),zero_charge=int(not exposed))
            all_features.append(row)
            if not exposed:
                continue
            for method in methods:
                plan_link(records[*k,method],plans[*k,method],route)
            for method in COMPARATORS:
                a,b = (records[*k,m]["validation"] for m in ("STaR",method))
                require(a["n"]==b["n"]==10000,"Matched validation tape size changed")
                paired.append(dict(partition=part,parent=parent,variant=variant,family=case["family"],route=rid,comparison=method,
                                   R_pp=(a["successes"]-b["successes"])/100,
                                   attainment_pp=100*(a["attained"]-b["attained"]),
                                   completion_saved=b["completion"]-a["completion"],star_attained=a["attained"],control_attained=b["attained"],
                                   star_successes=a["successes"],control_successes=b["successes"],star_failure=row["STaR_failure"]))
        population.append(dict(partition=part,parent=parent,variant=variant,family=case["family"],**pop))
    archived_pop = csv_rows(root/"results/phase5/data/population_by_instance.csv")
    require([{**r,**{k:int(r[k]) for k in ("all_routes","exposed","zero_charge")}} for r in [
        {k:x[k] for k in population[0]} for x in archived_pop]]==population,"Phase5 population mismatch")
    require(len(all_features)==8606 and len(paired)==2891*len(COMPARATORS),"Unexpected source or exposure counts")
    require_keys({(*key(row),method) for row in all_features if row["exposed"] for method in methods},records,"All phases route keys")
    facts = [r for r in all_features if r["exposed"]]
    cuts = {field:np.quantile([r[field] for r in facts if r["partition"]=="development"],[.25,.5,.75]).tolist()
            for field in ("customer_distance","min_customer_slack")}
    for row in facts:
        row.update(source_visit_bin=str(min(3,row["source_visits"]))+("+" if row["source_visits"]>=3 else ""),
                   source_R_bin="<0.80" if row["CON_R"]<.8 else ("0.80-<0.95" if row["CON_R"]<.95 else ">=0.95"),
                   **{f"{f}_quartile":int(np.searchsorted(cuts[f],row[f],side="right"))+1 for f in cuts})
    factmap = {key(r):r for r in facts}
    complexity,transitions,directions,strata,influence,visit_transitions,cases = [],[],[],[],[],[],[]
    for cohort in COHORTS:
        subset = [r for r in all_features if cohort=="all120" or r["partition"]==cohort]
        parents = {r["parent"]:(r["partition"]+":"+r["family"] if cohort=="all120" else r["family"]) for r in subset}
        for group,items in [("all",subset),*((f"{k[0]}-{k[1]}",rr) for k,rr in sorted(grouped(subset,lambda r:(r["family"],r["variant"])).items()))]:
            for plan,people,field in (("CON all",items,"source_"),("CON exposed",[r for r in items if r["exposed"]],"source_"),
                                      ("STaR exposed",[r for r in items if r["exposed"]],"selected_"),
                                      ("STaR nonattained",[r for r in items if r["exposed"] and not r["STaR_attained"]],"selected_"),
                                      ("CON, STaR nonattained",[r for r in items if r["exposed"] and not r["STaR_attained"]],"source_")):
                for measure in ("visits","distinct_stations","positive_charge_visits","zero_quantity_visits","small_positive_visits"):
                    counts = Counter(r[field+measure] for r in people)
                    for level in range(max(4,max(counts,default=0))+1):
                        complexity.append(dict(cohort=cohort,group=group,plan=plan,measure=measure,level=level,
                                               count=counts[level],n=len(people),share=counts[level]/len(people) if people else None))
            charges=Counter((r["source_visits"],r["selected_visits"]) for r in items if r["exposed"])
            visit_transitions.extend(dict(cohort=cohort,group=group,source=a,selected=b,n=n) for (a,b),n in sorted(charges.items()))
        for comparison in COMPARATORS:
            rr = [r for r in paired if r["comparison"]==comparison and (cohort=="all120" or r["partition"]==cohort)]
            for metric in ("R_pp","completion_saved"):
                summary=summarize_direction([r[metric] for r in rr],0.0 if metric=="R_pp" else policy["completion_tolerance"])
                directions.append(dict(cohort=cohort,comparison=comparison,metric=metric,**summary))
            transition=Counter((r["control_attained"],r["star_attained"]) for r in rr)
            transitions.append(dict(cohort=cohort,comparison=comparison,n=len(rr),gained=transition[False,True],
                                    lost=transition[True,False],retained=transition[True,True],neither=transition[False,False],
                                    net=transition[False,True]-transition[True,False]))
            groups = [("all","all",rr)]
            for dimension in ("source_visit_bin","source_R_bin","customer_distance_quartile","min_customer_slack_quartile",
                              "family","variant","topology_changed","gap_sequence_changed","station_id_sequence_changed","matched_quantity_changed"):
                groups.extend((dimension,value,part) for value,part in sorted(grouped(
                    rr,lambda row:str(factmap[key(row)].get(dimension))).items()))
            for dimension,value,part in groups:
                reason = Counter(r["star_failure"] for r in part)
                strata.append(dict(cohort=cohort,comparison=comparison,dimension=dimension,group=value,
                                   **ia_estimate(part,"R_pp",parents,policy),nonattained=len(part)-reason["attained"],
                                   point_only=reason["point_only"],customer_only=reason["customer_only"],depot_only=reason["depot_only"],
                                   joint=reason["joint"],contribution=sum(r["R_pp"] for r in part)/len(rr)))
            total = sum(r["R_pp"] for r in rr)
            for parent,part in sorted(grouped(rr,lambda r:r["parent"]).items()):
                partial=sum(r["R_pp"] for r in part)
                influence.append(dict(cohort=cohort,comparison=comparison,parent=parent,n=len(part),mean_pp=partial/len(part),
                                      contribution_pp=partial/len(rr),without_parent_pp=(total-partial)/(len(rr)-len(part))))
    registered = factmap["holdout","R2_10_2","A",0]
    cases.append(dict(selection="registered R2-A",**registered))
    for failure in ("point_only","customer_only","depot_only","joint"):
        candidates=[r for r in facts if r["STaR_failure"]==failure]
        if candidates:
            cases.append(dict(selection="lexicographic observed "+failure,**min(candidates,key=key)))
    for comparison in ("FSPC","SLS"):
        rr = [r for r in paired if r["comparison"]==comparison]
        for direction,sign in (("gain",1),("loss",-1)):
            chosen = [r for r in rr if r["R_pp"]*sign>0]
            if chosen:
                cases.append(dict(selection=f"lexicographic observed {comparison} {direction}",**factmap[key(min(chosen,key=key))]))
    for name,rows in (("route_features",all_features),("charging_complexity",complexity),("paired_routes",paired),
                      ("paired_directions",directions),("attainment_transitions",transitions),("mechanism_strata",strata),
                      ("parent_influence",influence),("diagnostic_cases",cases),("visit_transitions",visit_transitions)):
        write_csv(out/"data"/f"{name}.csv",rows)
    summary = dict(status="pass",instances=len(population),parents=len({r["parent"] for r in population}),routes=len(all_features),
                   exposed=len(facts),no_charge=len(all_features)-len(facts),by_partition=population,quartile_values=cuts,
                   single=sum(r["source_visits"]==1 for r in facts),
                   single_development=sum(r["source_visits"]==1 and r["partition"]=="development" for r in facts),
                   nonattained=sum(not r["STaR_attained"] for r in facts),archive=evidence)
    write_json(out/"audit/diagnostics.json",summary)
    return summary
