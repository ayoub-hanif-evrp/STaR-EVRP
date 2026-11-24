"""Resumable c64 extension; never runs a frozen holdout control again."""

from __future__ import annotations

import gzip
import json
import os
import platform
import tempfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter, process_time
from zipfile import ZipFile

import yaml

from star_evrp.budget import BudgetConfig
from star_evrp.charge_plan import ChargePlan
from star_evrp.competitive_search import optimize
from star_evrp.data_loader import load_instance
from star_evrp.experiment_phase2 import load_baseline_solution
from star_evrp.phase3 import _route, physics_for, plan_details, read_bundle, validation, versions
from star_evrp.phase4_results import (FREEZE, audit as audit_holdout, audit_validation, canonical, file_sha, git, indexed,
                                     observed_counts, plan_link, read_json, require, require_keys, sha, strata, write_json)
from star_evrp.phase5_ablations import optimize_component
from star_evrp.route_validator import validate_repair, validate_solution
from star_evrp.timing import RouteTiming
from star_evrp.types import Solution

CONFIG = "configs/phase5.yaml"
NEW = ("STaR_NSP", "STaR_NAS", "STaR_NPP")
STAGES = ("development", "ablations")
HISTORICAL = ("dataset", "configs/phase3_frozen.yaml", "results/baselines", "results/manifests",
              "results/phase2", "results/phase25", "results/phase3", "results/phase4", "docs/PHASE3_MANUSCRIPT_DRAFT.md")


def clock():
    return datetime.now(timezone.utc).isoformat()


def settings(root):
    policy = yaml.safe_load((root / CONFIG).read_text(encoding="utf-8"))
    frozen = read_json(root / "results/phase3/manifests/freeze.json")
    cfg = frozen["config"]
    require(frozen["commit"] == FREEZE and policy["profile"] == cfg["primary"] == "c64"
            and policy["bootstrap_seed"] == cfg["statistical_seed"] == 312406
            and policy["bootstrap_replicates"] == cfg["bootstrap_draws"] == 9999
            and policy["frozen_config"] == frozen["config_path"], "Phase 5 differs from frozen profile")
    require(policy["ablations"] == {"STaR_NSP":{"prioritize":False},"STaR_NAS":{"analytical":False},
                                    "STaR_NPP":{"prefix":False}}, "Incorrect component toggles")
    require_keys(policy["methods"], (*cfg["profiles"]["c64"]["methods"], *NEW), "Acronym map")
    require(len({row[0] for row in policy["methods"].values()})==10,"Acronyms must be unique")
    return policy, frozen


def frozen_hashes(root):
    head = git(root,"rev-parse","HEAD").decode().strip()
    tracked = git(root, "ls-tree", "-r", "--name-only", head, "--", *HISTORICAL).decode().splitlines()
    changed = git(root, "diff", "--name-only", "4ab2e32", "--", *HISTORICAL).decode().splitlines()
    require(not changed, f"Previous inputs modified: {changed[:5]}")
    return {name:file_sha(root/name) for name in sorted(tracked)}


def check_unchanged(root, protocol):
    require(frozen_hashes(root)==protocol["protected_sha256"],"Protected input bytes changed")
    freeze=read_json(root/"results/phase3/manifests/freeze.json")
    require(git(root,"rev-list","-n1",freeze["tag"]).decode().strip()==FREEZE,"Frozen tag moved")
    for name,expected in freeze["git_blob_sha256"].items():
        data=(root/name).read_bytes()
        require(expected in (sha(data),sha(data.replace(b"\r\n",b"\n"))),f"Frozen source changed: {name}")


def route_arguments(cfg):
    rule = cfg["profiles"]["c64"]
    return dict(seed=rule["seed"], samples=cfg["opt_samples"], target=cfg["target"], nearby=cfg["nearby_stations"])


def case_inputs(root, case, cfg, token):
    parent, variant = case["parent_key"], case["variant"]
    stem = f"{parent}__{variant}"
    instance=load_instance(root,parent,variant)
    physics=physics_for(cfg)
    require((instance.instance_file_sha256,instance.stations_file_sha256)==
            (case["instance_sha256"],case["stations_sha256"]),f"Source data hash mismatch: {stem}")
    if case["partition"]=="development":
        path=root/"results/baselines"/f"{stem}.json"
        solution=load_baseline_solution(path)
        historical=read_json(root/"results/phase25/manifest.json")["file_sha256"]
        data=path.read_bytes()
        require(historical[path.relative_to(root).as_posix()] in
                (sha(data),sha(data.replace(b"\r\n",b"\n")),sha(data.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n"))),
                f"Phase 2.5 development route source differs: {stem}")
        require(solution.method=="CON" and solution.battery_capacity==cfg["battery_capacity"]
                and solution.energy_consumption_rate==cfg["energy_consumption_rate"]
                and solution.metadata["instance_file_sha256"]==case["instance_sha256"]
                and solution.metadata["stations_file_sha256"]==case["stations_sha256"],f"Invalid CON context: {stem}")
    else:
        name=f"raw/con/{stem}.json.gz"
        with ZipFile(root/"results/phase3/con_bundles.zip") as archive:
            data=archive.read(name)
        expected=read_json(root/"results/phase3/processed/provenance.json")["raw"][name]
        require(sha(data)==expected,f"Holdout CON changed: {stem}")
        entry=json.loads(gzip.decompress(data))
        require(entry["context"]=={"schema":1,"freeze":token,"case":stem,"instance_sha256":case["instance_sha256"],
                                   "stations_sha256":case["stations_sha256"]} and
                entry["digest"]==sha(canonical(entry["rows"])),f"CON context differs: {stem}")
        con=entry["rows"]
        solution=Solution(parent,variant,"CON",physics.battery_capacity,physics.energy_consumption_rate,
                          [_route(row) for row in con["routes"]],total_distance=con["distance"])
    require((solution.instance_key, solution.variant)==(parent,variant) and validate_solution(instance,solution,config=physics).feasible,
            f"Invalid original fleet: {stem}")
    original=indexed((asdict(route) for route in solution.routes),lambda row:row["route_id"])
    keys=sorted(rid for rid,route in original.items() if observed_counts(route)[1])
    return instance,physics,original,keys,sha(data)


def signature(result, instance):
    return {"fingerprint":ChargePlan.from_route(instance,result.route).fingerprint(),"score":list(result.score),
            "counts":{field:result.budget[field] for field in ("generated","candidates_evaluated","deterministic_checks",
                                                              "screen_checks","scenarios_evaluated","cache_hits")},
            "screen":result.screen_rejections,"prefix":result.prefix_rejections,"moves":result.moves,
            "target_found":result.target_time is not None}


def preflight(root, out, workers):
    policy, freeze=settings(root)
    existing=out/"manifests/protocol.json"
    if existing.exists():
        return get_protocol(root,out)
    reference=audit_holdout(root)
    frozen=reference.freeze
    cfg=frozen["config"]
    roster=read_json(root/"results/manifests/dataset_inventory.json")["instances"]
    by_partition={mode:strata([c for c in roster if c["partition"]==mode]) for mode in ("development","holdout")}
    require(len(roster)==120 and len(by_partition["development"])==12 and len(by_partition["holdout"])==48 and
            not set(by_partition["development"]).intersection(by_partition["holdout"]),"Bad benchmark partitions")
    panel=[]
    token=reference.lineage["freeze_digest"]
    for case in sorted((row for row in roster if row["partition"]=="development"),
                       key=lambda row:(row["parent_key"],row["variant"])):
        instance,physics,original,eligible,_=case_inputs(root,case,cfg,token)
        path=root/"results/phase25/raw/candidates64"/f'{case["instance_key"]}__{case["variant"]}.json'
        old=read_json(path)
        require(old["rows_sha256"]==sha(json.dumps(old["rows"],sort_keys=True,allow_nan=False).encode())
                and {row["route_id"] for row in old["rows"]}==set(eligible) and len(old["rows"])==7*len(eligible)
                and all(row["stops"]==original[row["route_id"]]["stops"] for row in old["rows"] if row["method"]=="B0"),
                f"Development/source B0 mismatch: {path.name}")
        unexposed=sorted(set(original)-set(eligible))
        selected=set(eligible[:1]+eligible[-1:]+unexposed[:1])
        for rid in sorted(selected):
            route=_route(original[rid])
            budget=BudgetConfig(**cfg["profiles"]["c64"]["limits"])
            args=route_arguments(cfg)
            frozen_run=optimize(instance,physics,route,"STaR",budget,**args)
            wrapper=optimize_component(instance,physics,route,budget,**args)
            require(max(frozen_run.budget["elapsed_seconds"],wrapper.budget["elapsed_seconds"])<budget.wall_seconds,
                    "Wall guard bound in equivalence fixture")
            exact=signature(frozen_run,instance)
            require(exact==signature(wrapper,instance),f"All-on wrapper mismatch: {case['instance_key']}/{case['variant']}/{rid}")
            panel.append({"parent":case["parent_key"],"variant":case["variant"],"route":rid,
                          "visits":len(observed_counts(original[rid])[1]),**exact})
    require(any(row["screen"]>0 for row in panel) and any(row["prefix"]>0 for row in panel)
            and any(row["visits"]>1 for row in panel) and any(row["visits"]==0 for row in panel),"Insufficient equivalence path coverage")
    source_names=[CONFIG,"docs/PHASE5_ANALYSIS_PROTOCOL.md","src/star_evrp/phase5_ablations.py",
                  "src/star_evrp/phase5_experiments.py"]
    protocol={"schema":1,"start_utc":clock(),"head":git(root,"rev-parse","HEAD").decode().strip(),"frozen_commit":FREEZE,
              "freeze_digest":token,"workers":workers,"policy":policy,"frozen_profile":cfg["profiles"]["c64"],
              "source_sha256":{name:file_sha(root/name) for name in source_names},
              "protected_sha256":frozen_hashes(root),"environment":{
                  "python":platform.python_version(),"platform":platform.platform(),"processor":platform.processor(),
                  "logical_cpus":os.cpu_count(),"dependencies":versions(),
                  "threads":{name:os.environ.get(name) for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS")}},
              "holdout_controls_reused":True,"inference":"existing holdout primary only; all Phase 5 extensions exploratory"}
    write_json(out/"audit/equivalence.json",{"status":"pass","n":len(panel),"panels":panel,
                                          "coverage":{"analytical":sum(row["screen"] for row in panel),
                                                      "prefix":sum(row["prefix"] for row in panel),
                                                      "duplicates":sum(row["counts"]["cache_hits"] for row in panel)}})
    write_json(existing,protocol)
    return protocol


def get_protocol(root,out):
    value=read_json(out/"manifests/protocol.json")
    policy,freeze=settings(root)
    require(value["policy"]==policy and value["freeze_digest"]==sha(canonical(freeze))
            and value["frozen_commit"]==FREEZE,"Stale Phase 5 protocol")
    require(all(file_sha(root/name)==expected for name,expected in value["source_sha256"].items()),
            "Executed inputs differ from pre-execution protocol")
    require(read_json(out/"audit/equivalence.json")["status"]=="pass","Missing equivalence gate")
    return value


def write_batch(path,context,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix=path.name,suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(descriptor,"wb") as handle,gzip.GzipFile(fileobj=handle,mode="wb",filename="",mtime=0,compresslevel=4) as compressed:
            compressed.write(canonical({"context":context,"digest":sha(canonical(rows)),"rows":rows}))
        os.replace(name,path)
    finally:
        Path(name).unlink(missing_ok=True)


def methods_for(stage,case,cfg):
    require(stage in STAGES,"Unknown experiment stage")
    return NEW if stage=="ablations" else tuple(cfg["profiles"]["c64"]["methods"]) if case["partition"]=="development" else ()


def validate_work(method, record, cfg):
    limits=cfg["profiles"]["c64"]["limits"]
    work=record["work"]
    step=512 if method in ("B0","B1","B2","B3","B4","STaR_NPP") else 128
    require(1<=work["candidates_evaluated"]==work["deterministic_checks"]<=limits["max_candidate_evals"]
            and work["generated"]<=10*limits["max_candidate_evals"]
            and 0<=work["scenarios_evaluated"]<=min(limits["max_scenario_evals"],512*work["candidates_evaluated"])
            and work["scenarios_evaluated"]%step==0,"Hard work caps/increments violated")
    require(method!="STaR_NAS" or work["screen_checks"]==record["screen_rejections"]==0,"NAS performed analytical rejection")
    require(method!="STaR_NPP" or record["prefix_rejections"]==0,"NPP used prefix pruning")


def case_worker(root,out,case,stage,protocol,replay):
    label=f'{case["parent_key"]}__{case["variant"]}'
    _,freeze=settings(root)
    cfg=freeze["config"]
    methods=methods_for(stage,case,cfg)
    try:
        instance,physics,original,keys,source_hash=case_inputs(root,case,cfg,protocol["freeze_digest"])
        n_records=0
        token=sha(canonical(protocol))
        for start in range(0,len(keys),cfg["batch_routes"]):
            expected=[(rid,method) for rid in keys[start:start+cfg["batch_routes"]] for method in methods]
            context={"schema":1,"protocol":token,"partition":case["partition"],"profile":"c64",
                     "parent":case["parent_key"],"variant":case["variant"],"source_sha256":source_hash,
                     "instance_sha256":case["instance_sha256"],"stations_sha256":case["stations_sha256"],
                     "keys":[list(key) for key in expected]}
            name=f"{label}__{start:04d}.json.gz"
            raw_path,plan_path=(out/area/stage/name for area in ("raw","plans"))
            if raw_path.exists() or replay:
                raw=read_bundle(raw_path,context)["rows"]
                plans=read_bundle(plan_path,context)["rows"]
            else:
                raw,plans=[],[]
                for rid,method in expected:
                    source=_route(original[rid])
                    begin=process_time()
                    args=route_arguments(cfg)
                    budget=BudgetConfig(**cfg["profiles"]["c64"]["limits"])
                    if stage=="development":
                        result=optimize(instance,physics,source,method,budget,**args)
                    else:
                        result=optimize_component(instance,physics,source,budget,**args,**protocol["policy"]["ablations"][method])
                    cpu=process_time()-begin
                    begin=perf_counter()
                    trace=validate_repair(instance,source,result.route,physics)
                    plan={"route_id":rid,"method":method,"original_route_sha256":sha(canonical(original[rid])),**plan_details(
                        instance,source,result.route,trace,RouteTiming.from_trace(instance,trace,physics))}
                    final=validation(instance,result.route,trace,physics,cfg)
                    plans.append(plan)
                    raw.append({"route_id":rid,"method":method,"plan_sha256":sha(canonical(plan)),"work":result.budget,
                                "cpu_seconds":cpu,"validation_seconds":perf_counter()-begin,"validation":final,
                                "search_score":list(result.score),"accepted_moves":result.moves,"time_to_opt_target":result.target_time,
                                "screen_rejections":result.screen_rejections,"prefix_rejections":result.prefix_rejections})
                write_batch(plan_path,context,plans)
                write_batch(raw_path,context,raw)
            for records in (raw,plans):
                require([(row["route_id"],row["method"]) for row in records]==expected,"Incomplete or reordered work unit")
            for (rid,method),record,plan in zip(expected,raw,plans,strict=True):
                plan_link(record,plan,original[rid])
                require(plan["original_route_sha256"]==sha(canonical(original[rid])),"Original source route changed")
                validate_work(method,record,cfg)
                audit_validation(record["validation"],cfg["validation_seed"],(case["parent_key"],case["variant"],rid),cfg,
                                 plan["zero_wait_completion"])
                if replay:
                    selected,source=_route(plan),_route(original[rid])
                    trace=validate_repair(instance,source,selected,physics)
                    rebuilt=plan_details(instance,source,selected,trace,RouteTiming.from_trace(instance,trace,physics))
                    require(all(plan[key]==val for key,val in rebuilt.items()),"Replayed plan identity/timing mismatch")
                    require(validation(instance,selected,trace,physics,cfg,scalar=True)==record["validation"],"Final tape replay mismatch")
                n_records+=1
        return dict(case=label,partition=case["partition"],family=case["family"],parent=case["parent_key"],variant=case["variant"],
                    all_routes=len(original),exposed=len(keys),zero_charge=len(original)-len(keys),eligible=keys,records=n_records,
                    source_sha256=source_hash)
    except Exception as exception:
        return {"case":label,"partition":case["partition"],"error":f"{type(exception).__name__}: {exception}"}


def execute(root,out,stage,*,replay=False):
    protocol=get_protocol(root,out)
    require(versions()==protocol["environment"]["dependencies"] and platform.python_version()==protocol["environment"]["python"]
            and {name:os.environ.get(name) for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS")}==protocol["environment"]["threads"],
            "Use the recorded Python/package/thread setup")
    roster=read_json(root/"results/manifests/dataset_inventory.json")["instances"]
    cases=sorted((row for row in roster if stage=="ablations" or row["partition"]=="development"),
                 key=lambda row:(row["parent_key"],row["variant"]))
    start,elapsed=clock(),perf_counter()
    reports=[]
    with ProcessPoolExecutor(max_workers=protocol["workers"]) as pool:
        jobs=[pool.submit(case_worker,root,out,case,stage,protocol,replay) for case in cases]
        for index,job in enumerate(jobs,1):
            result=job.result()
            if "error" in result:
                print(result,flush=True)
            reports.append(result)
            if index%12==0 or index==len(jobs):
                print(f"{stage} {'replay' if replay else 'run'}: {index}/{len(jobs)} instances",flush=True)
    errors=[row for row in reports if "error" in row]
    kind="replay" if replay else "execution"
    path=out/"audit"/f"{stage}_{kind}.json"
    if path.exists():
        previous=read_json(path)
        if not previous["errors"]:
            require(previous["cases"]==reports and not errors,"A completed run audit no longer matches")
            return previous
        history=out/"logs"/f"{stage}_{kind}_{sha(canonical(previous))[:12]}.json"
        write_json(history,previous)
    result={"start_utc":start,"end_utc":clock(),"elapsed_seconds":perf_counter()-elapsed,"stage":stage,
            "protocol":sha(canonical(protocol)),"cases":reports,"errors":errors,"records":sum(row.get("records",0) for row in reports),
            "scalar_per_plan":cfg["validation_scalar_checks"] if replay else 0}
    write_json(path,result)
    require(not errors,f"Phase 5 {stage} {kind} incomplete; see {path.name}")
    return result
