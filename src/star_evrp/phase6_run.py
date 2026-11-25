"""Targeted experiments and saved-plan replay."""

from dataclasses import asdict
from math import isfinite
from time import perf_counter, process_time

import numpy as np

from star_evrp.budget import BudgetConfig
from star_evrp.charge_plan import ChargePlan
from star_evrp.competitive_search import optimize
from star_evrp.phase3 import _route, plan_details, read_bundle, validation
from star_evrp.phase4_results import audit_validation, canonical, require, sha
from star_evrp.phase5_experiments import route_arguments, write_batch
from star_evrp.phase6_archive import (case_key, contexts, csv_rows, environment, freeze_context, key, load_archive,
                                    now, write_json)
from star_evrp.phase6_fixed import fixed_topology
from star_evrp.phase6_math import analytic, backward_cap, exhaustive, one_visit_clock
from star_evrp.route_validator import validate_repair
from star_evrp.scenario_tapes import generate_z_tape
from star_evrp.timing import RouteTiming

ARCHIVED = ("CON","FSPC","SLS","STaR")
METHODS = {"SLS":"B3","STaR":"STaR"}


def validation_pair(instance,source,plan,physics,cfg,policy,scalar):
    trace = validate_repair(instance,source,plan,physics)
    timing = RouteTiming.from_trace(instance,trace,physics)
    vals = {label:validation(instance,plan,trace,physics,{**cfg,"validation_seed":seed},scalar=scalar)
            for label,seed in (("archive",cfg["validation_seed"]),("phase6",policy["validation_seed"]))}
    details = plan_details(instance,source,plan,trace,timing)
    exact = analytic(timing) if len(timing.mus)<=1 else None
    if len(timing.mus)==1:
        forward = one_visit_clock(timing)[0]
        backward = backward_cap(timing)
        require((forward is None and backward is None) or (forward is not None and backward is not None
                and (forward==backward or abs(forward-backward)<=1e-8)),"Independent one-visit cap disagrees")
        z = generate_z_tape(policy["validation_seed"],instance.parent_key,instance.variant,plan.route_id,"holdout",
                            cfg["validation_samples"],1)
        _,end = timing.evaluate(timing.waits(z))
        exact.update(phase6_completion_mc_se=float(end.std(ddof=1)/np.sqrt(len(end))))
    return details,vals,exact


def measured(instance,physics,source,method,milliseconds,cfg,policy):
    search = BudgetConfig(wall_seconds=milliseconds/1000,max_candidate_evals=policy["timing_max_trials"],
                          max_scenario_evals=policy["timing_max_draws"])
    start,cpu = perf_counter(),process_time()
    value = None
    error = None
    try:
        value = optimize(instance,physics,source,METHODS[method],search,**route_arguments(cfg))
    except ValueError as exc:
        if str(exc) not in ("Infeasible CON starting plan or insufficient starting budget","Budget too small to score source plan"):
            raise
        error = str(exc)
    elapsed,cpu_used = perf_counter()-start,process_time()-cpu
    work = value.budget if value else None
    if value:
        require(1<=work["candidates_evaluated"]<=search.max_candidate_evals and
                512<=work["scenarios_evaluated"]<=min(search.max_scenario_evals,work["candidates_evaluated"]*512)
                and work["scenarios_evaluated"] % (128 if method=="STaR" else 512)==0,"Timed counters inconsistent")
        status = ("wall_observed" if work["elapsed_seconds"]>=search.wall_seconds else
                  "plan_cap_observed" if work["candidates_evaluated"]>=search.max_candidate_evals else
                  "scenario_cap_observed" if work["scenarios_evaluated"]>=search.max_scenario_evals else
                  "generation_cap_observed" if work["generated"]>=10*search.max_candidate_evals else "no_cap_observed")
    else:
        status = "initialization_fallback"
    return value.route if value else source, dict(status=status,error=error,elapsed_s=elapsed,cpu_s=cpu_used,
        overshoot_ms=max(0,1000*elapsed-milliseconds),nominal_ms=milliseconds,work=work,
        score=list(value.score) if value else None,screen_rejections=value.screen_rejections if value else None,
        prefix_rejections=value.prefix_rejections if value else None)


def timing_jobs(instance,physics,source,cfg,policy,random):
    guard_order = random.permutation(policy["timing_guards_ms"]).tolist()
    for guard in guard_order:
        first_order = list(random.permutation(tuple(METHODS)))
        for repeat in range(1,policy["timing_repeats"]+1):
            order = first_order if repeat==1 else first_order[::-1] if repeat==2 else list(random.permutation(tuple(METHODS)))
            for order_index,method in enumerate(order,1):
                selected,details = measured(instance,physics,source,str(method),int(guard),cfg,policy)
                yield f"{method}-{guard}-{repeat}",selected,{**details,"method":str(method),"repeat":repeat,"order":order_index,
                                                             "guard_order":guard_order.index(guard)+1}


def _payloads(out,kind,protocol,panel_row):
    c = key(panel_row)
    name = f"{c[1]}__{c[2]}__{c[3]}.json.gz"
    out_context = {"schema":1,"analysis_protocol":sha(canonical(protocol)),"stage":kind,"key":list(c),
                   "source_archive_sha256":panel_row["source_sha256"]}
    return out_context,out/"raw"/kind/name,out/"plans"/kind/name


def _loads(raw,plans,context):
    experiments,selected = (read_bundle(f,context)["rows"] for f in (raw,plans))
    require(len(experiments)==len(selected) and len({r["id"] for r in experiments})==len(experiments),"Incomplete or duplicate batch")
    for row,plan in zip(experiments,selected,strict=True):
        require(row["id"]==plan["id"] and row["plan_sha256"]==sha(canonical(plan)),"Phase 6 plan link broken")
    return experiments,selected


def allowed_ids(kind,policy):
    if kind=="timing":
        return {f"{m}-{g}-{i}" for m in METHODS for g in policy["timing_guards_ms"] for i in range(1,policy["timing_repeats"]+1)}
    return {*ARCHIVED,"AS1" if kind=="as1" else "FT-SAA"}


def run_stage(root,out,protocol,kind,*,replay=False):
    cfg = freeze_context(root)["config"]
    policy = protocol["configuration"]
    gate = out/"audit/as1_gate.json"
    if kind=="as1":
        from star_evrp.phase4_results import read_json
        eligibility = read_json(gate)
        if not eligibility["eligible"]:
            return {"stage":"as1","status":"skipped","reason":eligibility["reason"],"plans":0,"rows":0}
    panel_name = "as1" if kind=="as1" else "comparator"
    panel = {key(r)[:3]:r for r in csv_rows(out/"manifests"/f"{panel_name}_panel.csv") if r["route"]!="NA"}
    token = protocol["freeze_digest"]
    initial = now()
    warm = []
    records,plans = ({},{}) if kind=="timing" else load_archive(root)[:2]
    rng = np.random.default_rng(policy["timing_order_seed"])
    current_keys,selected_checks,cache_hits = [],0,0
    expected_ids = allowed_ids(kind,policy)
    if kind=="timing" and not replay and not (out/"audit/timing_execution.json").exists():
        for case,instance,physics,original,_ in contexts(root,token):
            label = case_key(case)
            if label in panel and label[0]=="development":
                source = _route(original[int(panel[label]["route"])])
                for method in METHODS:
                    _,details=measured(instance,physics,source,method,50,cfg,policy)
                    warm.append({"key":[*label,source.route_id],"method":method,"status":details["status"]})
                if len(warm)==8:
                    break
        write_json(out/"logs/timing_context.json",{"started":initial,"environment":environment(),"warm_up":warm})
    for case,instance,physics,original,source_hash in contexts(root,token):
        label = case_key(case)
        if label not in panel:
            continue
        row = panel[label]
        k = key(row)
        context,raw,plan_path = _payloads(out,kind,protocol,row)
        require(source_hash==row["source_sha256"],"Panel source archive changed")
        source = _route(original[k[-1]])
        if raw.exists() or replay:
            raw_rows,plan_rows = _loads(raw,plan_path,context)
            if kind=="timing" and not replay:
                # Reproduce the order RNG state on resumption without invoking optimization.
                for _ in rng.permutation(policy["timing_guards_ms"]):
                    rng.permutation(tuple(METHODS))
                    rng.permutation(tuple(METHODS))
        else:
            if kind=="timing":
                candidates = list(timing_jobs(instance,physics,source,cfg,policy,rng))
            else:
                archived = [(method,_route(plans[*k,method]),{"method":method,"status":"archived"}) for method in ARCHIVED]
                if kind=="as1":
                    selected,work = exhaustive(instance,source,physics,target=cfg["target"],
                                               probability_tol=policy["analytic_tie_probability"],clock_tol=policy["completion_tolerance"])
                    candidates = [*archived,("AS1",selected,{"method":"AS1",**work})]
                else:
                    fspc = _route(plans[*k,"FSPC"])
                    tape = generate_z_tape(cfg["profiles"]["c64"]["seed"],k[1],k[2],k[3],"opt",cfg["opt_samples"],int(row["visits"]))
                    selected,work = fixed_topology(instance,source,fspc,physics,tape,policy,cfg["target"])
                    candidates = [*archived,("FT-SAA",selected,{"method":"FT-SAA",**work})]
            raw_rows,plan_rows,cached = [],[],{}
            for name,selected,meta in candidates:
                if selected is None:
                    details,vals,exact,fp = None,None,None,None
                    hit = False
                else:
                    fp = ChargePlan.from_route(instance,selected).fingerprint()
                    hit = fp in cached
                    if not hit:
                        cached[fp] = validation_pair(instance,source,selected,physics,cfg,policy,False)
                    details,vals,exact = cached[fp]
                    if meta["method"] in ARCHIVED and kind!="timing":
                        require(vals["archive"]==records[*k,meta["method"]]["validation"],"Phase 5 validation failed reconciliation")
                plan = {"id":name,"route_id":k[-1],"details":details,"source_route_sha256":sha(canonical(original[k[-1]]))}
                plan_rows.append(plan)
                raw_rows.append(dict(id=name,**meta,validation=vals,analytic=exact,
                                     plan_sha256=sha(canonical(plan)),validation_cache_hit=hit,fingerprint=fp))
            require({r["id"] for r in raw_rows}==expected_ids,"Missing new method")
            write_batch(plan_path,context,plan_rows)
            write_batch(raw,context,raw_rows)
        require({r["id"] for r in raw_rows}==expected_ids,"Wrong saved method or repeat identities")
        if replay:
            checked = {}
            for row,plan in zip(raw_rows,plan_rows,strict=True):
                fp = row["fingerprint"]
                details = plan["details"]
                require(plan["source_route_sha256"]==sha(canonical(original[k[-1]])),"CON route hash mismatch on replay")
                if details is None:
                    require(row["id"]=="AS1" and row["status"]=="no_feasible_restricted_plan","Missing plan without valid reason")
                    continue
                if fp not in checked:
                    checked[fp] = validation_pair(instance,source,_route({"route_id":k[-1],**details}),physics,cfg,policy,True)
                    selected_checks += 1
                else:
                    cache_hits += 1
                built,vals,an = checked[fp]
                require(built==details and vals==row["validation"] and an==row["analytic"],"Saved plan or final tape disagrees")
                if row["id"]=="AS1":
                    require(len(details["station_positions"])<=1 and row["total"]==row["evaluated"]+row["energy_rejected"]+row["timing_rejected"],
                            "AS1 domain or candidate accounting invalid")
                if row["id"]=="FT-SAA":
                    require(details["station_positions"]==plan_rows[0]["details"]["station_positions"],"Fixed station topology changed")
                for tape_name,seed in (("archive",cfg["validation_seed"]),("phase6",policy["validation_seed"])):
                    audit_validation(vals[tape_name],seed,k[1:],cfg,details["zero_wait_completion"])
        current_keys.append(list(k))
        if len(current_keys)%12==0 or len(current_keys)==len(panel):
            print(f"{kind} {'replay' if replay else 'execution'} {len(current_keys)}/{len(panel)}",flush=True)
    require(len(current_keys)==len(panel),"Panel did not execute every fixed key")
    kind_label = "replay" if replay else "execution"
    report = dict(status="pass",stage=kind,kind=kind_label,start_utc=initial,end_utc=now(),routes=current_keys,
                  rows=len(panel)*len(expected_ids),unique_plan_checks=selected_checks,duplicate_plan_checks_reused=cache_hits,
                  scalar_checks=10*selected_checks)
    report_path = out/"audit"/f"{kind}_{kind_label}.json"
    if not report_path.exists():
        write_json(report_path,report)
    return report
