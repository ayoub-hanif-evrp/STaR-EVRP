"""Partition-preserving reconciliation and parent-paired analysis."""

from collections import Counter
from statistics import fmean

import numpy as np

from star_evrp.phase3 import read_bundle
from star_evrp.phase4_results import (audit as audit_holdout, bootstrap, canonical, failure_reason, file_sha,
                                     grouped, indexed, read_json, require, require_keys, route_key, sha,
                                     stop_proxy, strata, summarize, value, write_json)
from star_evrp.phase4_release import csv_export
from star_evrp.phase5_experiments import STAGES, check_unchanged, get_protocol

COHORTS=("holdout","development","all120")
MAIN=("CON","MWR","QBR","STaR")
ABL=("STaR","STaR-NPC","STaR-NSP","STaR-NAS","STaR-NPP")
METRICS=("reliability","attained","full_completion","search_scenarios","candidate_evaluations","wall_ms","cpu_ms")


def cohort_rows(rows,cohort):
    return [row for row in rows if cohort=="all120" or row["partition"]==cohort]


def quantiles(rows, field):
    array=np.array(rows)
    points=np.quantile(array,[0,.1,.25,.5,.75,.9,1])
    return {f"{field}_{key}":float(val) for key,val in zip(("min","p10","p25","median","p75","p90","max"),points)}


def metric_summary(rows, *, pooled):
    base_keys=("mean_R","point_at_target","lower_bound_attained","two_sided_CI_contains_target","full_completion_time",
               "search_scenarios","search_wall_ms","search_cpu_ms")
    extras=("unique_trials","generated","deterministic_checks","screen_checks","analytical_rejections","prefix_rejections",
            "search_wall_ms","search_cpu_ms","validation_ms","generation_ms","screening_ms","simulation_ms","checking_ms")
    if not rows:
        empty={"n":0,**{key:None for key in base_keys},**{key:None for key in extras}}
        for key in (*extras,"search_scenarios"):
            empty.update({name:None for name in quantiles([0],key)})
        return empty
    result=summarize(rows)
    for field in extras:
        if field=="unique_trials":
            vals=[value(row,"candidate_evaluations") for row in rows]
        elif field in ("wall_ms","cpu_ms","search_wall_ms","search_cpu_ms"):
            vals=[value(row,field.removeprefix("search_")) for row in rows]
        elif field in ("validation_ms","generation_ms","screening_ms","simulation_ms","checking_ms"):
            key={"generation_ms":"generation_seconds","screening_ms":"screening_seconds",
                 "simulation_ms":"simulation_seconds","checking_ms":"deterministic_seconds"}.get(field)
            vals=[1000*(row["validation_seconds"] if key is None else row["work"][key]) for row in rows]
        elif field in ("analytical_rejections","prefix_rejections"):
            vals=[row["screen_rejections" if field=="analytical_rejections" else field] for row in rows]
        else:
            vals=[row["work"][field] for row in rows]
        result[field]=fmean(vals)
        result.update(quantiles(vals,field))
    result.update(quantiles([value(row,"search_scenarios") for row in rows],"search_scenarios"))
    if pooled:
        result.update({key:None for key in result if "_ms" in key})
    return result


def paired(first,second):
    left,right=(indexed(rows,route_key) for rows in (first,second))
    require_keys(left,right,"Original paired route set")
    return [(row,right[key]) for key,row in left.items()]


def effect(samples,metric,parents):
    estimates=[]
    for first,second in samples:
        if metric=="completion_common_attained":
            if not(value(first,"attained") and value(second,"attained")):
                continue
            field="full_completion"
        else:
            field=metric
        estimates.append((first["parent"],value(first,field)-value(second,field)))
    nums=bootstrap(estimates,parents)
    return {"n":len(estimates),"parents":len({key for key,_ in estimates}),
            **dict(zip(("mean","lo95","hi95","parent_mean","parent_lo95","parent_hi95"),nums))}


def public(value_to_relabel,names):
    if isinstance(value_to_relabel,str):
        return names.get(value_to_relabel,value_to_relabel)
    if isinstance(value_to_relabel,list):
        return [public(item,names) for item in value_to_relabel]
    if isinstance(value_to_relabel,dict):
        return {key:public(item,names) for key,item in value_to_relabel.items()}
    return value_to_relabel


def load_new(out,protocol):
    metrics,plans,logs,hashes={}, {}, {}, {}
    token=sha(canonical(protocol))
    for stage in STAGES:
        reports=[read_json(out/"audit"/f"{stage}_{kind}.json") for kind in ("execution","replay")]
        report,replay=reports
        require(all(item["protocol"]==token and not item["errors"] for item in reports)
                and report["cases"]==replay["cases"] and replay["scalar_per_plan"]==5
                and report["records"]==replay["records"],"Incomplete or stale experimental replay")
        logs[stage]=report
        case_map=indexed(report["cases"],lambda row:row["case"])
        expected_batches={}
        for case,details in case_map.items():
            ids=details["eligible"]
            methods=protocol["frozen_profile"]["methods"] if stage=="development" else list(protocol["policy"]["ablations"])
            if stage=="ablations":
                methods=("STaR_NSP","STaR_NAS","STaR_NPP")
            for start in range(0,len(ids),24):
                expected_batches[f"{case}__{start:04d}.json.gz"]=(details,[(rid,m) for rid in ids[start:start+24] for m in methods])
        for area in ("raw","plans"):
            require_keys([path.name for path in (out/area/stage).glob("*.json.gz")],expected_batches,"New batches")
        for name,(details,expected) in expected_batches.items():
            paths=[out/area/stage/name for area in ("raw","plans")]
            raw, saved=(read_bundle(path) for path in paths)
            context=raw["context"]
            require(context==saved["context"] and context["protocol"]==token and context["profile"]=="c64"
                    and context["source_sha256"]==details["source_sha256"] and context["partition"]==details["partition"]
                    and (context["parent"],context["variant"])==(details["parent"],details["variant"])
                    and [tuple(key) for key in context["keys"]]==expected,"Batch identity differs")
            require(all([(row["route_id"],row["method"]) for row in pack["rows"]]==expected for pack in (raw,saved)),
                    "Incomplete new batch")
            for path in paths:
                hashes[path.relative_to(out).as_posix()]=file_sha(path)
            for raw_row,plan in zip(raw["rows"],saved["rows"],strict=True):
                key=details["partition"],details["parent"],details["variant"],raw_row["route_id"],raw_row["method"]
                require(raw_row["plan_sha256"]==sha(canonical(plan)) and key not in metrics,"Duplicate/changed new plan")
                metrics[key]={**raw_row,"partition":key[0],"parent":key[1],"variant":key[2],"route":key[3],
                              "family":details["family"],"profile":"c64","run_cohort":f"Phase5-{stage}",
                              "source":paths[0].relative_to(out).as_posix()}
                plans[key]=plan
    require(len(metrics)==sum(log["records"] for log in logs.values()),"New report count differs")
    return metrics,plans,logs,hashes


def export_records(path,rows):
    fields=list(dict.fromkeys(key for row in rows for key in row))
    csv_export(path,fields,[["NA" if row.get(key) is None else row[key] for key in fields] for row in rows])


def analyze(root,out):
    protocol=get_protocol(root,out)
    check_unchanged(root,protocol)
    archived=audit_holdout(root)
    methods={key:description[0] for key,description in protocol["policy"]["methods"].items()}
    fresh,plans,logs,hashes=load_new(out,protocol)
    records=dict(fresh)
    for key,row in archived.rows.items():
        if key[0]=="c64":
            combined=("holdout",*key[1:])
            require(combined not in records,"Holdout control overwrite attempted")
            records[combined]={**row,"partition":"holdout","run_cohort":"Phase3-archive"}
            plans[combined]=archived.plans[key]
    roster=read_json(root/"results/manifests/dataset_inventory.json")["instances"]
    cases={}
    for case in logs["ablations"]["cases"]:
        cases[case["parent"],case["variant"]]=case
    require_keys(cases,[(case["parent_key"],case["variant"]) for case in roster],"Benchmark coverage")
    for case in archived.cases:
        current=cases[case["parent"],case["variant"]]
        require((current["all_routes"],current["eligible"],current["zero_charge"])==
                (case["routes"],case["eligible_route_ids"],case["zero_charge"]),"Holdout source denominator changed")
    expected={(case["partition"],case["parent"],case["variant"],rid,method)
              for case in cases.values() for rid in case["eligible"] for method in methods}
    require_keys(records,expected,"Benchmark route pairs")
    require_keys(plans,expected,"Benchmark plan pairs")
    parent_info={mode:strata([row for row in roster if mode=="all120" or row["partition"]==mode]) for mode in COHORTS}
    parent_partition={row["parent_key"]:row["partition"] for row in roster}
    instance_rows,population=[],[]
    by_case=grouped(records.values(),lambda row:(row["parent"],row["variant"],row["method"]))
    base_row=lambda row:{field:row[field] for field in ("parent","variant","partition","family","all_routes","exposed","zero_charge")}
    for key,case in sorted(cases.items()):
        con=by_case[*key,"B0"]
        exposed=case["exposed"]
        require(case["all_routes"]==case["zero_charge"]+exposed==case["zero_charge"]+len(con),"Per-instance population mismatch")
        population.append({**base_row(case),"CON_below_point":sum(row["validation"]["successes"]<9500 for row in con),
                           "CON_nonattained":exposed-sum(value(row,"attained") for row in con)})
        for method,label in methods.items():
            subset=by_case[*key,method]
            require(len(subset)==exposed,"Wrong method denominator")
            instance_rows.append({"instance":f"{key[0]}/{key[1]}",**base_row(case),"profile":"c64","method":label,
                                  "runtime_cohort":subset[0]["run_cohort"] if subset else "NA",**metric_summary(subset,pooled=False)})
    pool=[]; family=[]; failures=[]; paired_effects=[]; family_ablation=[]; paired_routes=[]; directions=[]; restore=[]
    full="STaR"
    for cohort in COHORTS:
        categories=cohort_rows(records.values(),cohort)
        by_method=grouped(categories,lambda row:row["method"])
        groups={key:(f"{parent_partition[key]}:{family}" if cohort=="all120" else family)
                for key,family in parent_info[cohort].items()}
        for key,label in methods.items():
            subset=by_method[key]
            pool.append(dict(cohort=cohort,profile="c64",method=label,
                             **metric_summary(subset,pooled=cohort=="all120")))
            for (family_name,variant),items in sorted(grouped(subset,lambda row:(row["family"],row["variant"])).items()):
                family.append(dict(cohort=cohort,profile="c64",family=family_name,variant=variant,method=label,**summarize(items)))
                outcomes=Counter(failure_reason(row["validation"]) for row in items)
                validations=[row["validation"] for row in items]
                failures.append(dict(cohort=cohort,profile="c64",family=family_name,variant=variant,method=label,n=len(items),
                                     **{name:outcomes[name] for name in ("attained","point_only","customer_only","depot_only","joint")},
                                     scenario_customer_only=sum(row["late_customer"]-row["late_both"] for row in validations),
                                     scenario_depot_only=sum(row["late_depot"]-row["late_both"] for row in validations),
                                     scenario_joint=sum(row["late_both"] for row in validations),
                                     scenario_straddle_routes=sum(row["wilson95_two_sided"][0]<=.95<=row["wilson95_two_sided"][1] for row in validations)))
        con_pairs=paired(by_method[full],by_method["B0"])
        con_low={route_key(con) for _,con in con_pairs if con["validation"]["successes"]<9500}
        for key,label in methods.items():
            if label in MAIN:
                candidates=[row for row in by_method[key] if route_key(row) in con_low]
                restore.append(dict(cohort=cohort,profile="c64",method=label,n=len(candidates),
                                    attained=sum(value(row,"attained") for row in candidates)))
            if key==full:
                continue
            pairs=paired(by_method[full],by_method[key])
            for metric in (*METRICS,"completion_common_attained"):
                if cohort=="all120" and metric in ("wall_ms","cpu_ms"):
                    continue
                if metric in ("wall_ms","cpu_ms") and cohort=="holdout" and label in ABL[2:]:
                    continue
                paired_effects.append(dict(cohort=cohort,profile="c64",comparison=label,metric=metric,
                                           status="confirmatory" if (cohort,label,metric)==("holdout","FSPC","reliability") else "exploratory",
                                           **effect(pairs,metric,groups)))
            if label in ABL[1:]:
                for name,pair_group in sorted(grouped(pairs,lambda pair:pair[0]["family"]).items()):
                    relevant={parent:stratum for parent,stratum in groups.items() if parent_info[cohort][parent]==name}
                    for metric in ("reliability","attained","full_completion","search_scenarios","candidate_evaluations"):
                        family_ablation.append(dict(cohort=cohort,profile="c64",family=name,comparison=label,metric=metric,
                                                    **effect(pair_group,metric,relevant)))
            for field in ("reliability","full_completion"):
                bigger=1 if field=="reliability" else -1
                deltas=[bigger*(value(first,field)-value(second,field)) for first,second in pairs]
                tolerance=0 if field=="reliability" else 1e-8
                directions.append(dict(cohort=cohort,profile="c64",comparison=label,metric=field,n=len(pairs),
                                       better=sum(d>tolerance for d in deltas),ties=sum(abs(d)<=tolerance for d in deltas),
                                       worse=sum(d<-tolerance for d in deltas)))
            if cohort!="all120":
                paired_routes.extend(dict(partition=cohort,profile="c64",parent=first["parent"],family=first["family"],
                                          variant=first["variant"],route=first["route"],comparator=label,
                                          STaR_successes=first["validation"]["successes"],comparator_successes=second["validation"]["successes"],
                                          STaR_run=first["run_cohort"],comparator_run=second["run_cohort"],
                                          **{f"delta_{metric}":value(first,metric)-value(second,metric) for metric in METRICS})
                                     for first,second in pairs)
    computed=next(item for item in paired_effects if item["status"]=="confirmatory")
    official=next(item for item in archived.summary["paired"] if item["status"]=="confirmatory")
    for field,source in zip(("mean","lo95","hi95","parent_mean","parent_lo95","parent_hi95"),
                            ("estimate","lower95","upper95","parent_equal_estimate","parent_equal_lower95","parent_equal_upper95")):
        require(abs(computed[field]-official[source])<=2e-14,"Registered interval changed")
    for result in archived.summary["overall"]:
        actual=next(row for row in pool if row["method"]==methods[result["method"]] and row["cohort"]=="holdout")
        require(all(actual[key]==number for key,number in result.items() if key!="method"),"Published holdout mean/count differs")
    run_work=[]
    for (run,partition,method),subset in sorted(grouped(records.values(),lambda row:(row["run_cohort"],row["partition"],row["method"])).items()):
        run_work.append(dict(runtime_cohort=run,partition=partition,profile="c64",method=methods[method],
                             **metric_summary(subset,pooled=False)))
    candidate=[]
    for row in archived.rows.values():
        if row["method"] in ("B3","B4","STaR"):
            candidate.append(dict(profile=row["profile"],method=methods[row["method"]],
                                  trials=value(row,"candidate_evaluations"),draws=value(row,"search_scenarios"),
                                  stop=stop_proxy(row,archived.freeze["config"]["profiles"][row["profile"]]["limits"])))
    runtime_environment={"new":protocol["environment"],"archive":{key:archived.freeze[key] for key in (
        "platform","processor","logical_cpus","dependencies","python","thread_settings")}}
    case_data=public(archived.summary["case_routes"],methods)
    example=archived.summary["example"]
    case_draws={methods[method]:archived.rows["c64",*example,method]["validation"] for method in ("B0","B4","STaR")}
    routes=[]
    for key,row in sorted(records.items()):
        result=row["validation"]; plan=plans[key]
        routes.append(dict(partition=key[0],profile="c64",parent=key[1],variant=key[2],route=key[3],method=methods[key[4]],
                           family=row["family"],runtime_cohort=row["run_cohort"],source=row["source"],plan_sha256=row["plan_sha256"],
                           draws_validation=result["n"],successes=result["successes"],R=result["reliability"],
                           LB=result["wilson95_lower_one_sided"],attained=result["attained"],completion=result["completion"],
                           lower95_two=result["wilson95_two_sided"][0],upper95_two=result["wilson95_two_sided"][1],
                           customer_late=result["late_customer"],depot_late=result["late_depot"],joint_late=result["late_both"],
                           failure_mode=failure_reason(result),station_visits=len(plan["station_positions"]),energy=plan["energy_added"],
                           distance=plan["distance"],wall_ms=value(row,"wall_ms"),cpu_ms=value(row,"cpu_ms"),
                           validation_ms=row["validation_seconds"]*1000,**row["work"],screen_rejections=row["screen_rejections"],
                           prefix_rejections=row["prefix_rejections"]))
    for name,series in (("instance_results",instance_rows),("population_by_instance",population),("paired_routes",paired_routes),
                        ("route_results",routes),("family_ablation",family_ablation),("registered_route_events",case_data)):
        export_records(out/"data"/f"{name}.csv",series)
    results=dict(pool=pool,family=family,population=population,failures=failures,paired=paired_effects,family_ablation=family_ablation,
                 directions=directions,restoration=restore,work=run_work,instance=instance_rows,
                 archived=public({key:archived.summary[key] for key in ("paired","mechanism","parent_effects","robustness","budget",
                                                                      "work","reliability_quality","station_tables")},methods),
                 example=example,case_events=case_data,case_draws=case_draws,archived_candidates=candidate,
                 counts={"archived_controls":len(records)-len(fresh),"new_controls":logs["development"]["records"],
                         "new_ablations":logs["ablations"]["records"],"all":len(records)},
                 methods=list(methods.values()),runtime_environment=runtime_environment)
    write_json(out/"data/summary.json",results)
    write_json(out/"manifests/source_map.json",dict(protocol=sha(canonical(protocol)),fresh=hashes,
                                                   archived_c64={name:info["sha256"] for name,info in archived.lineage["batches"].items()
                                                                if "/c64/" in name},archive_commit=archived.lineage["published_source_commit"]))
    write_json(out/"audit/reconciled.json",dict(status="PASS",registered=computed,counts=results["counts"],instances=len(cases),
                                               phase3_verified_batches=len(archived.lineage["batches"]),frozen_unchanged=True))
    print(f"Reconciled {len(records):,} matched c64 records, {len(cases)} instances",flush=True)
    return results
