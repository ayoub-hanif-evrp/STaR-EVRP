"""Read-only, exact-key inputs for the conference exhibits."""

from collections import Counter
from math import isclose
from statistics import fmean, median

from star_evrp.conference_physics import deteriorated_candidates, example_candidates, route_example
from star_evrp.phase4_results import (bootstrap, canonical, file_sha, git, grouped, indexed, plan_link, read_json,
                                     require, require_keys, strata)
from star_evrp.phase6_archive import csv_rows, freeze_context, key, load_archive, roster, write_csv, write_json
from star_evrp.phase6_run import _loads, _payloads

METHODS = {
    "CON": "Original route", "MWR": "Mean-wait repair", "QBR": "Quantile repair",
    "FSPC": "Fixed-station repair", "SLS": "Scenario search", "STaR": "STaR",
}
ABLATIONS = {
    "STaR": "None (full STaR)", "STaR-NPC": "Partial charging", "STaR-NSP": "Slack prioritization",
    "STaR-NAS": "Analytical screening", "STaR-NPP": "Progressive evaluation",
}
FROZEN = "c657aa69d55178c85b4759475933b36d1bcc2181"
HISTORICAL_BASE = "d17616177b61cb98e11c1cd5408d7c981fae2b21"
BASE = "f243297cd60206b7ab75dcd52d38faf8bee73d5e"
AUDIT = "audit/phase8"
IGNORE_ADDITION = b"\n# Local conference proof, renderer and rebuild scratch\n/results/conference_p8_work/\n"
PRIMARY = (0.012420292977165015, 0.008630955453232267, 0.016503459913289817)
SOURCE_5 = "results/phase5/data/"
SOURCE_6 = "results/phase6/data/"
FROZEN_SEARCH = (
    "competitive_search.py", "route_evaluator.py", "timing.py", "budget.py", "search_common.py",
    "charge_plan.py", "deterministic_simulator.py", "scenario_tapes.py",
)
SOURCES = {
    "Fig01": (SOURCE_6+"route_features.csv", "results/phase3/con_bundles.zip",
              "results/phase3/processed/provenance.json", SOURCE_5+"route_results.csv"),
    "Fig02": tuple(f"src/star_evrp/{name}" for name in FROZEN_SEARCH)
             + ("configs/phase3_frozen.yaml", "docs/PHASE6_MATHEMATICAL_AUDIT.md","src/star_evrp/phase3.py"),
    "Fig03": (SOURCE_5+"paired_effects.csv", SOURCE_5+"route_results.csv",
              "results/phase3/tables/parent_effects.csv", SOURCE_6+"paired_directions.csv"),
    "Fig04": (SOURCE_6+"mechanism_strata.csv", SOURCE_6+"route_features.csv", SOURCE_6+"paired_routes.csv",
              SOURCE_6+"attainment_transitions.csv", SOURCE_6+"parent_influence.csv", SOURCE_5+"route_results.csv"),
    "Fig05": tuple(SOURCE_6+f"timing_{name}.csv" for name in
                   ("route_results","route_aggregates","summary","paired_routes","paired_effects"))
             + ("results/phase6/manifests/comparator_panel.csv","results/phase6/manifests/protocol.json",
                "results/phase6/tables/T06-05_controlled_runtime.csv"),
    "Tab01": ("configs/phase3_frozen.yaml","results/phase3/manifests/freeze.json",
              "results/manifests/dataset_inventory.json",SOURCE_5+"population_by_instance.csv"),
    "Tab02": (SOURCE_5+"route_results.csv",SOURCE_5+"summary.json",
              "results/phase5/tables/supplementary/S01_complete_benchmark.csv"),
    "Tab03": (SOURCE_5+"route_results.csv",SOURCE_5+"paired_effects.csv",
              "results/phase5/tables/main/T04_ablation_quality.csv","results/phase5/tables/main/T05_ablation_work.csv"),
}


def near(value, expected, label, atol=2e-10):
    require(isclose(float(value),float(expected),rel_tol=0,abs_tol=atol),
            f"{label}: {value!r} differs from {expected!r}")


def selected_paths(root, *names):
    return {name:file_sha(root/name) for name in dict.fromkeys(names)}


def protected_hashes(root):
    tag=git(root,"rev-parse","star-phase3-freeze-v1^{}").decode().strip()
    require(tag==FROZEN,"Changed optimizer tag")
    git(root,"merge-base","--is-ancestor",BASE,"HEAD")
    base=git(root,"ls-tree","-r","--name-only",HISTORICAL_BASE).decode().splitlines()
    protected=set(base)-{"README.md",".gitattributes",".gitignore"}
    changed=set(git(root,"diff","--name-only",HISTORICAL_BASE).decode().splitlines())
    require(not changed & protected,"Protected archive changed")
    return selected_paths(root,*sorted(protected))


def census(root,cfg):
    roster_rows = roster(root)
    case_ids={(x["parent_key"],x["variant"]):x for x in roster_rows}
    population=indexed(csv_rows(root/(SOURCE_5+"population_by_instance.csv")),lambda r:(r["parent"],r["variant"]))
    require_keys(population,case_ids,"Instance census")
    breakdown=[]
    for partition in ("development","holdout"):
        relevant=[r for r in population.values() if r["partition"]==partition]
        selected=[r for r in roster_rows if r["partition"]==partition]
        require({(r["parent"],r["variant"]) for r in relevant}=={(r["parent_key"],r["variant"]) for r in selected}
                and all(r["family"]==case_ids[r["parent"],r["variant"]]["family"] for r in relevant),"Census split mismatch")
        require(all(int(r["all_routes"])==int(r["exposed"])+int(r["zero_charge"]) for r in relevant),"Invalid route census")
        breakdown.append(dict(partition=partition,instances=len(relevant),parents=len(strata(selected)),
                              **{k:sum(int(r[k]) for r in relevant) for k in ("all_routes","exposed","zero_charge")}))
    require([(r["instances"],r["parents"],r["all_routes"],r["exposed"]) for r in breakdown]==
            [(24,12,1742,570),(96,48,6864,2321)],"Unexpected frozen split or denominators")
    hashes={r["stations_sha256"] for r in roster_rows}
    require(len(hashes)==4 and all({r["partition"] for r in roster_rows if r["stations_sha256"]==item}==
                                   {"development","holdout"} for item in hashes),"Station table reuse mismatch")
    counts={field:sum(r[field] for r in breakdown) for field in ("instances","parents","all_routes","exposed","zero_charge")}
    frozen=cfg["profiles"]["c64"]
    spec=counts|{"partitions":breakdown,"distinct_station_tables":len(hashes),"customers_per_instance":1000,
                 "target":cfg["target"],"battery_capacity":cfg["battery_capacity"],
                 "energy_consumption":cfg["energy_consumption_rate"],"station_windows":cfg["station_windows"],
                 "work_limits":frozen["limits"],"search_draws":cfg["opt_samples"],"prefix_draws":cfg["opt_samples"]//4,
                 "nearby_count":cfg["nearby_stations"],"validation_draws":cfg["validation_samples"],
                 "search_seed":frozen["seed"],"validation_seed":cfg["validation_seed"],
                 "bootstrap_seed":cfg["statistical_seed"],"bootstrap_replicates":cfg["bootstrap_draws"],
                 "archive_workers":cfg["workers"]}
    require(spec["search_draws"]*frozen["limits"]["max_candidate_evals"]<frozen["limits"]["max_scenario_evals"],
            "Scenario cap statement no longer applies")
    return spec


def holdout_records(root, records, cfg):
    selected={k[1:]:v for k,v in records.items() if k[0]=="holdout"}
    parents=strata([r for r in roster(root) if r["partition"]=="holdout"])
    groups=grouped(selected,lambda k:k[-1])
    keys={k[:3] for k in groups["STaR"]}
    require(len(keys)==2321 and len(parents)==48 and {k[0] for k in keys}==set(parents),"Bad primary matched sample")
    require_keys(groups,set(METHODS)|set(ABLATIONS),"Expected frozen c64 methods")
    for method,ks in groups.items():
        require_keys((k[:3] for k in ks),keys,method)
    for balance in keys:
        vals=[selected[*balance,m]["validation"] for m in groups]
        require({v["n"] for v in vals}=={cfg["validation_samples"]} and len({v["tape_seed"] for v in vals})==1,
                "Validation count, seed or key mismatch")
        require(all(v["successes"]/v["n"]==v["reliability"] for v in vals),"Success proportion mismatch")
    return selected,parents,sorted(keys)


def signed_pairs(rows,keys,comparator):
    result=[]
    for p,v,r in keys:
        one,two=(rows[p,v,r,m]["validation"] for m in ("STaR",comparator))
        result.append(dict(parent=p,variant=v,route=r,family=rows[p,v,r,"STaR"]["family"],comparator=comparator,
                           star_successes=one["successes"],control_successes=two["successes"],scenarios=one["n"],
                           delta_pp=100*(one["successes"]-two["successes"])/one["n"]))
    return result


def boot(values, parents, cfg):
    return bootstrap(values,parents,seed=cfg["statistical_seed"],replicates=cfg["bootstrap_draws"])


def paired(root,rows,keys,parents,cfg):
    archive=indexed([r for r in csv_rows(root/(SOURCE_5+"paired_effects.csv"))
                      if (r["cohort"],r["metric"],r["profile"])==("holdout","reliability","c64")],lambda r:r["comparison"])
    dirs=indexed([r for r in csv_rows(root/(SOURCE_6+"paired_directions.csv"))
                   if (r["cohort"],r["metric"])==("holdout","R_pp")],lambda r:r["comparison"])
    archive_parent=indexed([r for r in csv_rows(root/"results/phase3/tables/parent_effects.csv") if r["metric"]=="reliability"],
                           lambda r:(r["competitor"],r["parent"]))
    summaries, raw, blocks = [], [], []
    for method in ("FSPC","SLS",*list(ABLATIONS)[1:]):
        saved=archive[method]
        pairs=signed_pairs(rows,keys,method)
        result=boot([(r["parent"],r["star_successes"]/r["scenarios"]-r["control_successes"]/r["scenarios"])
                     for r in pairs],parents,cfg)
        for label,numeric in zip(("mean","lo95","hi95","parent_mean","parent_lo95","parent_hi95"),result,strict=True):
            near(numeric,saved[label],f"{method} archived {label}")
        require(int(saved["n"])==len(pairs) and int(saved["parents"])==len(parents),"Paired archive denominator differs")
        counts=Counter("higher" if r["delta_pp"]>0 else "lower" if r["delta_pp"]<0 else "equal" for r in pairs)
        summaries.append(dict(comparator=method,n=len(pairs),parents=len(parents),status=saved["status"],
                              **dict(zip(("mean_pp","lo95_pp","hi95_pp","parent_mean_pp","parent_lo95_pp","parent_hi95_pp"),
                                         (100*x for x in result),strict=True)),
                              **{name:counts[name] for name in ("higher","equal","lower")}))
        if method in ("FSPC","SLS"):
            raw.extend(pairs)
            for count,archived in zip(("higher","equal","lower"),("gains","ties","losses"),strict=True):
                require(counts[count]==int(dirs[method][archived]),"Archived direction counts differ")
            frozen_code="B4" if method=="FSPC" else "B3"
            for p,group in sorted(grouped(pairs,lambda r:r["parent"]).items()):
                historic=archive_parent[frozen_code,p]
                mean=fmean(r["delta_pp"] for r in group)
                require(len(group)==int(historic["paired_routes"]),"Wrong parent route count")
                near(mean,100*float(historic["mean_difference"]),"Historic parent effect",atol=5.1e-6)
                blocks.append(dict(comparator=method,parent=p,family=parents[p],n=len(group),mean_pp=mean))
        if method=="FSPC":
            for got,expected in zip(result[:3],PRIMARY,strict=True):
                near(got,expected,"Registered Phase 3 primary",atol=1e-14)
    require(sum(r["status"]=="confirmatory" for r in summaries)==1 and summaries[0]["status"]=="confirmatory",
            "Wrong confirmatory comparison status")
    return summaries,raw,blocks


def table_values(root,rows,keys,effects):
    source5=root/"results/phase5"
    s1=indexed([r for r in csv_rows(source5/"tables/supplementary/S01_complete_benchmark.csv") if r["Cohort"]=="96 holdout"],
               lambda r:r["Method"])
    t4=indexed([r for r in csv_rows(source5/"tables/main/T04_ablation_quality.csv") if r["Cohort"]=="96 holdout"],
               lambda r:r["Method"])
    t5=indexed([r for r in csv_rows(source5/"tables/main/T05_ablation_work.csv") if r["Partition"]=="holdout"],
               lambda r:r["Method"])
    summary=indexed([r for r in read_json(source5/"data/summary.json")["pool"] if r["cohort"]=="holdout"],lambda r:r["method"])
    comparison,ablation=[],[]
    pairs={r["comparator"]:r for r in effects}
    for method in dict.fromkeys((*METHODS,*ABLATIONS)):
        subset=[rows[*k,method] for k in keys]
        vals=[r["validation"] for r in subset]
        agg=dict(method=method,n=len(vals),reliability_pct=100*fmean(v["reliability"] for v in vals),
                 attained=sum(v["attained"] for v in vals),completion=fmean(v["completion"] for v in vals),
                 draws=fmean(r["work"]["scenarios_evaluated"] for r in subset),
                 trials=fmean(r["work"]["candidates_evaluated"] for r in subset),
                 wall_ms=1000*fmean(r["work"]["elapsed_seconds"] for r in subset))
        archived=summary[method]
        require(agg["attained"]==archived["lower_bound_attained"],"Summary Wilson count mismatch")
        for col,raw,scale in (("reliability_pct","mean_R",100),("completion","full_completion_time",1),
                              ("draws","search_scenarios",1),("wall_ms","search_wall_ms",1)):
            near(agg[col],scale*archived[raw],f"Phase 5 pooled {method} {col}",atol=1e-8)
        if method in METHODS:
            legacy=s1[method]
            require([f'{agg["reliability_pct"]:.2f}',f'{agg["attained"]}/{len(vals)}',f'{agg["completion"]:.2f}',
                     f'{agg["trials"]:.2f}',f'{agg["draws"]:.0f}',f'{agg["wall_ms"]:.2f}']==
                    [legacy[k] for k in ("R (%)","LB / n","Completion","Trials","Draws","Wall ms")],f"Comparison table mismatch {method}")
            comparison.append(dict(label=METHODS[method],**agg))
        if method in ABLATIONS:
            require([f'{agg["reliability_pct"]:.2f}',f'{agg["attained"]}/{len(vals)}',f'{agg["draws"]:.0f}']==
                    [t4[method]["R (%)"],t4[method]["LB / n"],t5[method]["Draws"]],f"Ablation table mismatch {method}")
            effect=pairs.get(method,{})
            ablation.append(dict(component=ABLATIONS[method],**agg,loss_pp=effect.get("mean_pp"),
                                 lo95_pp=effect.get("lo95_pp"),hi95_pp=effect.get("hi95_pp")))
    require(all(all(rows[*k,"STaR"]["validation"][metric]==rows[*k,"STaR-NPP"]["validation"][metric]
                    for metric in ("reliability","successes","completion","attained")) for k in keys),"NPP exact route outcomes differ")
    return comparison,ablation


def complexity(root,rows,keys,parents,cfg,pairs,primary,features):
    part={k:r for k,r in features.items() if k[0]=="holdout" and r["exposed"]=="True"}
    require_keys((k[1:] for k in part),keys,"Holdout feature match")
    old=csv_rows(root/(SOURCE_6+"paired_routes.csv"))
    legacy=indexed([r for r in old if (r["partition"],r["comparison"])==("holdout","FSPC")],lambda r:key(r)[1:])
    require_keys(legacy,keys,"FSPC mechanism matched keys")
    route_rows=[]
    for r in pairs:
        k=r["parent"],r["variant"],r["route"]
        facts=part["holdout",*k]
        source,selected=(int(facts[x]) for x in ("source_visits","selected_visits"))
        nonattain=not rows[*k,"STaR"]["validation"]["attained"]
        require(source>0 and int(legacy[k]["star_successes"])==r["star_successes"]
                and int(legacy[k]["control_successes"])==r["control_successes"]
                and (facts["STaR_attained"]=="False")==nonattain,"Mechanism source mismatch")
        near(r["delta_pp"],legacy[k]["R_pp"],"Mechanism units")
        route_rows.append(dict(**r,source_visits=source,selected_visits=selected,nonattained=nonattain,
                               bin="3+" if source>=3 else str(source)))
    ref=indexed([r for r in csv_rows(root/(SOURCE_6+"mechanism_strata.csv"))
                 if (r["cohort"],r["comparison"],r["dimension"])==("holdout","FSPC","source_visit_bin")],lambda r:r["group"])
    bins=[]
    for level in ("1","2","3+"):
        part=[r for r in route_rows if r["bin"]==level]
        n=len(part)
        effect=boot([(r["parent"],r["delta_pp"]) for r in part],parents,cfg)
        p=len({r["parent"] for r in part})
        failure=sum(r["nonattained"] for r in part)
        contribute=sum(r["delta_pp"] for r in part)/len(keys)
        for field,observed in (("mean",effect[0]),("lo95",effect[1]),("hi95",effect[2]),("contribution",contribute)):
            near(observed,ref[level][field],f"{level}-visit {field}")
        require((n,p,failure)==tuple(int(ref[level][z]) for z in ("n","parents","nonattained")),"Visit-bin denominator mismatch")
        bins.append(dict(bin=level,n=n,parents=p,mean_pp=effect[0],lo95_pp=effect[1],hi95_pp=effect[2],
                         contribution_pp=contribute,nonattained=failure,nonattainment_pct=100*failure/n))
    near(sum(r["contribution_pp"] for r in bins),primary["mean_pp"],"Summed mechanism signed effect")
    count=Counter(r["family"] for r in route_rows if r["nonattained"])
    require(sum(count.values())==110 and count["R2"]+count["RC2"]==109,"Holdout nonattainment mismatch")
    return bins,route_rows,dict(by_family=dict(count),three_share=100*bins[-1]["n"]/len(keys),
                                  net_share=100*bins[-1]["contribution_pp"]/primary["mean_pp"])


def map_candidates(rows,keys,plans,features):
    all_options=[]
    for k in keys:
        parent,variant,rid=k
        source,selected=plans["holdout",*k,"CON"],plans["holdout",*k,"STaR"]
        v0,v1=(rows[*k,m]["validation"] for m in ("CON","STaR"))
        original=features["holdout",*k]
        original_topology,final_topology=(p["station_positions"] for p in (source,selected))
        require(canonical(original_topology).decode()==original["source_topology"] and
                canonical(final_topology).decode()==original["selected_topology"],"Topology does not match archive")
        require(source["customer_sha256"]==selected["customer_sha256"],"Customer order changed")
        customers=sum(event[1]=="customer" for event in source["events"])
        require(customers==int(original["customers"]),"Source customer count mismatch")
        changed=original_topology!=final_topology
        gain=v1["successes"]-v0["successes"]
        tier = 1 if changed and not v0["attained"] and v1["attained"] and gain>0 else (
            2 if changed and gain>0 else 3 if changed else None)
        all_options.append(dict(parent=parent,variant=variant,route=rid,customers=customers,tier=tier,
                                topology_changed=changed,con_attained=v0["attained"],star_attained=v1["attained"],gain_successes=gain,
                                con_topology=canonical(original_topology).decode(),star_topology=canonical(final_topology).decode()))
    all_options.sort(key=lambda r:(r["customers"],r["parent"],r["variant"],r["route"]))
    eligible=[r for r in all_options if r["tier"] is not None]
    require(bool(eligible),"No physical topology change in archive")
    chosen=min(eligible,key=lambda r:r["tier"])
    require((chosen["parent"],chosen["variant"],chosen["route"])==("C1_10_3","A",106),
            "The Phase 7 main example must remain fixed")
    return dict(chosen=chosen,eligible_tier_counts=dict(Counter(str(r["tier"]) for r in all_options)),
                rule="First by original customer count, parent, variant, route ID within first nonempty tier",
                fallback=chosen["tier"]!=1,example_scope="Outcome-selected holdout illustration"), all_options


def timing_panel(root,cfg):
    phase6=root/"results/phase6"
    protocol=read_json(phase6/"manifests/protocol.json")
    policy=protocol["configuration"]
    panel=indexed([r for r in csv_rows(phase6/"manifests/comparator_panel.csv") if r["route"]!="NA"],key)
    guards=sorted(policy["timing_guards_ms"])
    repeats=policy["timing_repeats"]
    methods=("STaR","SLS")
    require(guards==[20,50,100] and repeats==3 and len(panel)==118,"Wrong timing panel design")
    require(Counter(k[0] for k in panel)=={"development":23,"holdout":95} and len({k[1] for k in panel})==60,
            "Timing panel partitions differ")
    raw=csv_rows(phase6/"data/timing_route_results.csv")
    by_repeat=indexed(raw,lambda r:(*key(r),r["method"],int(r["nominal_ms"]),int(r["repeat"])))
    require_keys(by_repeat,((*k,m,g,i) for k in panel for m in methods for g in guards for i in range(1,repeats+1)),
                 "Timing repeat sample")
    for k,row in panel.items():
        context,metrics,plan_file=_payloads(phase6,"timing",protocol,row)
        raw_items,_=_loads(metrics,plan_file,context)
        for r in raw_items:
            point=by_repeat[*k,r["method"],r["nominal_ms"],r["repeat"]]
            val=r["validation"]["phase6"]
            require(point["plan_sha256"]==r["plan_sha256"] and int(point["phase6_successes"])==val["successes"]
                    and val["n"]==10000 and int(point["phase6_tape_seed"])==val["tape_seed"]
                    and int(point["search_scenarios_evaluated"])==r["work"]["scenarios_evaluated"]
                    and float(point["elapsed_s"])==r["elapsed_s"] and point["status"]==r["status"],"Timing archive repeat mismatch")
    aggregates=indexed(csv_rows(phase6/"data/timing_route_aggregates.csv"),lambda r:(*key(r),r["method"],int(r["guard_ms"])))
    require_keys(aggregates,((*k,m,g) for k in panel for m in methods for g in guards),"Timing route-method mean")
    paired_archive=indexed(csv_rows(phase6/"data/timing_paired_routes.csv"),lambda r:(*key(r),int(r["guard_ms"])))
    require_keys(paired_archive,((*k,g) for k in panel for g in guards),"Timing paired routes")
    summary=indexed([r for r in csv_rows(phase6/"data/timing_summary.csv") if r["cohort"]=="all120"],
                    lambda r:(r["method"],int(r["guard_ms"])))
    effects=indexed([r for r in csv_rows(phase6/"data/timing_paired_effects.csv") if r["cohort"]=="all120"],
                    lambda r:(r["metric"],int(r["guard_ms"])))
    timed_table=indexed(csv_rows(phase6/"tables/T06-05_controlled_runtime.csv"),lambda r:(r["Method"],int(r["Guard ms"])))
    blocks={r["parent_key"]:f'{r["family"]}:{r["partition"]}' for r in roster(root)}
    route_rows,comparisons,points,effects_pp=[],[],[],[]
    for guard in guards:
        raw_note={}
        for method in methods:
            observations=[]
            repeat_rows=[]
            for k,identity in panel.items():
                items=[by_repeat[*k,method,guard,i] for i in range(1,repeats+1)]
                repeat_rows.extend(items)
                expected=aggregates[*k,method,guard]
                take=lambda field:[float(item[field]) for item in items]
                new=dict(partition=k[0],parent=k[1],variant=k[2],route=k[3],family=identity["family"],method=method,
                         guard_ms=guard,reliability=fmean(take("phase6_reliability")),
                         draws=fmean(take("search_scenarios_evaluated")),wall_ms=1000*median(take("elapsed_s")),
                         overshoots=sum(x>0 for x in take("overshoot_ms")))
                for field in ("reliability","draws","wall_ms"):
                    near(new[field],expected[field],f"Timing route-level {field}")
                require(new["overshoots"]==int(expected["wall_exceedances"]),"Timing actual exceedance count differs")
                observations.append(new)
                route_rows.append(new)
            ref=summary[method,guard]
            point=dict(method=method,guard_ms=guard,n=len(observations),repeats=len(repeat_rows),
                       reliability_pct=100*fmean(r["reliability"] for r in observations),draws=fmean(r["draws"] for r in observations),
                       median_wall_ms=median(r["wall_ms"] for r in observations),
                       overshoots=sum(r["overshoots"] for r in observations),
                       max_overshoot_ms=max(float(r["overshoot_ms"]) for r in repeat_rows))
            for col,hist,scale in (("reliability_pct","reliability",100),("draws","draws",1),("median_wall_ms","wall_ms_median",1),
                                   ("max_overshoot_ms","overshoot_max_ms",1)):
                near(point[col],scale*float(ref[hist]),f"Timing summary {guard} {method} {col}",atol=1e-8)
            require((point["n"],point["repeats"],point["overshoots"])==
                    tuple(int(ref[k]) for k in ("n","repeats","over_guard")),"Timing summary denominator mismatch")
            require(timed_table[method,guard]["R (%)"]==f'{point["reliability_pct"]:.2f}',"Archived timing presentation mismatch")
            points.append(point)
            raw_note[method]=observations
        by_route={key(r):r for r in raw_note["SLS"]}
        one_guard=[]
        for candidate in raw_note["STaR"]:
            k=key(candidate)
            control=by_route[k]
            result={f:candidate[f] for f in ("partition","parent","variant","family","route")}
            result.update(guard_ms=guard,R_pp=100*(candidate["reliability"]-control["reliability"]),
                          draws=candidate["draws"]-control["draws"],wall_ms=candidate["wall_ms"]-control["wall_ms"])
            for metric in ("R_pp","draws","wall_ms"):
                near(result[metric],paired_archive[*k,guard][metric],"Archived route-level timing difference",atol=1e-8)
            one_guard.append(result)
        comparisons.extend(one_guard)
        for metric in ("R_pp","draws","wall_ms"):
            value=boot([(r["parent"],r[metric]) for r in one_guard],blocks,cfg)
            archived=effects[metric,guard]
            for got,name in zip(value,("mean","lo95","hi95","parent_mean","parent_lo95","parent_hi95"),strict=True):
                near(got,archived[name],f"Timing interval {metric} {guard} ms {name}",atol=1e-8)
            require((int(archived["n"]),int(archived["parents"]))==(118,60),"Wrong timing inference denominator")
            effects_pp.append(dict(guard_ms=guard,metric=metric,n=118,parents=60,mean=value[0],lo95=value[1],hi95=value[2]))
    primary={r["method"]:r for r in points if r["guard_ms"]==50}
    rely=[r for r in effects_pp if r["metric"]=="R_pp"]
    require(len(raw)==2124 and all(r["lo95"]<0<r["hi95"] for r in rely),"Timing conclusions are inconsistent")
    saves = 100*(1-primary["STaR"]["draws"]/primary["SLS"]["draws"])
    return points,effects_pp,route_rows,comparisons,dict(n=118,parents=60,guards_ms=guards,repeats_each=repeats,
            measurements=len(raw),development=23,holdout=95,relative_reduction_pct=saves,
            primary_stops={m:{k:primary[m][k] for k in ("overshoots","max_overshoot_ms","repeats")} for m in methods})


def gather(root,out):
    records,plans,prior=load_archive(root)
    freeze=freeze_context(root)
    cfg=freeze["config"]
    rows,parents,ks=holdout_records(root,records,cfg)
    source=census(root,cfg)
    phase6_features=indexed(csv_rows(root/(SOURCE_6+"route_features.csv")),key)
    require(len(phase6_features)==source["all_routes"],"Missing source routes")
    effects,matched,blocks=paired(root,rows,ks,parents,cfg)
    comparison,ablation=table_values(root,rows,ks,effects)
    bins,complex_routes,stats=complexity(root,rows,ks,parents,cfg,[r for r in matched if r["comparator"]=="FSPC"],
                                       effects[0],phase6_features)
    # Check original visit counts directly from source archive, not from selected STaR topology.
    for r in complex_routes:
        k=r["parent"],r["variant"],r["route"]
        source_count=len(plans["holdout",*k,"CON"]["station_positions"])
        chosen_count=len(plans["holdout",*k,"STaR"]["station_positions"])
        require((r["source_visits"],r["selected_visits"])==(source_count,chosen_count),"Charging-visit counts differ from plans")
    main,main_options=map_candidates(rows,ks,plans,phase6_features)
    complex_case,complex_options=example_candidates(phase6_features)
    adverse,adverse_options=deteriorated_candidates(rows,ks)
    examples={name:route_example(root,rows,plans,freeze,selection,methods)
              for name,selection,methods in (("Fig01",main,("CON","STaR")),
                    ("Sup01",complex_case,("CON","STaR")),("Sup02",adverse,("FSPC","STaR")))}
    for name,options in (("Fig01",main_options),("Sup01",complex_options),("Sup02",adverse_options)):
        example=examples[name]
        for suffix,items in (("route_selection",options),("instance_nodes",example["nodes"]),
                             ("route_stops",example["stops"]),("metrics",example["metrics"]),
                             ("physical_summary",example["totals"])):
            write_csv(out/"data"/f"{name}_{suffix}.csv",items)
        write_csv(out/"data"/f"{name}_charging_events.csv",
                  [r for r in example["stops"] if r["type"]=="station"])
        write_json(out/"data"/f"{name}_route_selection.json",example["selection"])
    timing,ti_effects,ti_routes,ti_pairs,ti_notes=timing_panel(root,cfg)
    flat=(("Fig03_paired_routes",matched),("Fig03_parent_effects",blocks),
          ("Fig03_contrast_summary",effects[:2]),("Fig04_source_visit_bins",bins),("Fig04_route_inputs",complex_routes),
          ("Fig05_guard_summary",timing),("Fig05_paired_intervals",ti_effects),("Fig05_route_aggregates",ti_routes),
          ("Fig05_paired_routes",ti_pairs),("Tab01_population",source["partitions"]),("Tab02_exact",comparison),("Tab03_exact",ablation))
    for name,data in flat:
        write_csv(out/"data"/f"{name}.csv",data)
    write_json(out/"data/Tab01_configuration.json",source)
    references={name:selected_paths(root,*paths) for name,paths in SOURCES.items()}
    for name,example in examples.items():
        diagnostic=("results/phase6/data/paired_routes.csv",) if name=="Sup02" else ()
        references[name]=selected_paths(root,*SOURCES["Fig01"],*example["paths"],*diagnostic,
                                        "src/star_evrp/route_validator.py","src/star_evrp/deterministic_simulator.py",
                                        "configs/phase3_frozen.yaml")
    result=dict(config=source,examples=examples,
                paired=effects[:2],complexity=bins,complexity_notes=stats,timing=timing,timing_effects=ti_effects,timing_notes=ti_notes,
                comparison=comparison,ablation=ablation,prior_archive=prior,sources=references)
    write_json(out/AUDIT/"numerical.json",dict(status="pass",phase3_bundles=prior["phase3_batches"],phase5_routes=len(records),
                holdout_exposed=len(ks),holdout_parents=len(parents),primary_fraction=PRIMARY,route_selection={n:r["selection"] for n,r in examples.items()},
                signed_direction_counts={r["comparator"]:[r["higher"],r["equal"],r["lower"]] for r in effects[:2]},
                complexity_counts={r["bin"]:[r["n"],r["nonattained"]] for r in bins},
                timing_repeats=ti_notes["measurements"],all_tables_crosschecked=True,replayed_optimizers=0,
                exact_routewise_npp_equality=True))
    return result
