"""Read-only study lineage, immutable panel selection and archive joins."""

import csv
import os
import platform
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
import yaml
from scipy.optimize._highspy import _core as highs

from star_evrp.phase3 import versions
from star_evrp.phase4_results import audit, canonical, file_sha, git, read_json, require, require_keys, sha
from star_evrp.phase5_analysis import load_new
from star_evrp.phase5_experiments import case_inputs, check_unchanged, get_protocol

CONFIG = "configs/phase6.yaml"
THREADS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
PUBLIC = {"B0":"CON","B1":"MWR","B2":"QBR","B3":"SLS","B4":"FSPC","STaR":"STaR",
          "STaR_no_partial":"STaR-NPC","STaR_NSP":"STaR-NSP","STaR_NAS":"STaR-NAS","STaR_NPP":"STaR-NPP"}
MARKERS = ("docs/.gitkeep","results/figures/.gitkeep","results/processed/.gitkeep","results/raw/.gitkeep",
           "results/reports/.gitkeep","results/tables/.gitkeep","scripts/.gitkeep")


def now():
    return datetime.now(timezone.utc).isoformat()


def write_bytes(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix=path.name,suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(descriptor,"wb") as handle:
            handle.write(data)
        os.replace(name,path)
    finally:
        Path(name).unlink(missing_ok=True)


def write_json(path, value):
    write_bytes(path,canonical(value)+b"\n")


def csv_rows(path):
    with path.open(encoding="utf-8",newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, records, fields=None):
    from io import StringIO
    fields = fields or list(dict.fromkeys(k for row in records for k in row))
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer,fieldnames=fields,lineterminator="\n")
    writer.writeheader()
    writer.writerows({k:row[k] if row.get(k) is not None else "NA" for k in fields} for row in records)
    write_bytes(path,buffer.getvalue().encode())


def freeze_context(root):
    return read_json(root/"results/phase3/manifests/freeze.json")


def roster(root):
    return sorted(read_json(root/"results/manifests/dataset_inventory.json")["instances"],
                  key=lambda row:(row["parent_key"],row["variant"]))


def key(row):
    return row["partition"],row["parent"],row["variant"],int(row["route"])


def case_key(case):
    return case["partition"],case["parent_key"],case["variant"]


def contexts(root, token):
    config = freeze_context(root)["config"]
    for case in roster(root):
        instance,physics,original,_,source_hash = case_inputs(root,case,config,token)
        yield case,instance,physics,original,source_hash


def protected(root,base):
    allowed = (*MARKERS,"README.md",".gitignore",".gitattributes")
    changed = git(root,"diff","--name-only",base,"--").decode().splitlines()
    existing = git(root,"ls-tree","-r","--name-only",base).decode().splitlines()
    require(not (set(changed)&(set(existing)-set(allowed))),"Historical tracked inputs changed")
    return {name:file_sha(root/name) for name in existing if name not in allowed}


def source_hashes(root):
    paths = [root/CONFIG,root/"docs/PHASE6_ANALYSIS_PROTOCOL.md",root/"scripts/run_phase6.py",
             *(root/"src/star_evrp"/f"phase6_{name}.py" for name in ("archive","diagnostics","fixed","math","run")),
             root/"tests/test_phase6_math.py"]
    return {p.relative_to(root).as_posix():file_sha(p) for p in sorted(paths)}


def environment():
    info = {"python":platform.python_version(),"system":platform.platform(),"processor":platform.processor(),
            "logical_cpus":os.cpu_count(),"deps":versions()|{"scipy":scipy.__version__,"numpy":np.__version__},
            "solver":f"SciPy HiGHS {highs.HIGHS_VERSION_MAJOR}.{highs.HIGHS_VERSION_MINOR}.{highs.HIGHS_VERSION_PATCH}",
            "threads":{k:os.getenv(k) for k in THREADS}}
    try:
        import psutil
        info.update(cpu_affinity=psutil.Process().cpu_affinity(), cpu_load_percent=psutil.cpu_percent(interval=.25))
    except (ImportError,AttributeError,OSError):
        info.update(cpu_affinity=None,cpu_load_percent=None)
    return info


def panels(root, out, cfg, token):
    result = {"as1":[],"comparator":[]}
    for case,instance,_,original,source_hash in contexts(root,token):
        by_visits = {rid:sum(s["node_id"] in instance.station_attributes for s in route["stops"])
                     for rid,route in original.items()}
        one = [rid for rid,n in by_visits.items() if n==1]
        multi = [rid for rid,n in by_visits.items() if n>1]
        partition,parent,variant = case_key(case)
        salt = f'{cfg["panel_salt"]}|{parent}|{variant}'
        preferred = "single" if int(sha((salt+"|category").encode()),16)%2==0 else "multi"
        rank = lambda rid: sha(f"{salt}|{rid}".encode())
        for kind in result:
            subset = one if kind=="as1" else ((one or multi) if preferred=="single" else (multi or one))
            rid = min(subset,key=rank) if subset else None
            result[kind].append(dict(parent=parent,variant=variant,partition=partition,family=case["family"],
                                     route=rid,visits=by_visits[rid] if rid is not None else None,
                                     preferred=preferred if kind=="comparator" else "single",
                                     eligible_single=len(one),eligible_multi=len(multi),source_routes=len(original),
                                     source_sha256=source_hash,reason="selected" if subset else "no_eligible_route"))
    for name,rows in result.items():
        write_csv(out/"manifests"/f"{name}_panel.csv",rows)
    return result


def prior_audit(root):
    ph5 = root/"results/phase5"
    phase5_protocol = get_protocol(root,ph5)
    check_unchanged(root,phase5_protocol)
    gate = read_json(ph5/"audit/final_gate.json")
    require(all(file_sha(ph5/name)==h for name,h in gate["file_sha256"].items()),"Phase 5 release hash mismatch")
    source = read_json(ph5/"manifests/source_map.json")
    fresh,_,_,hashes = load_new(ph5,phase5_protocol)
    require(hashes==source["fresh"],"Phase 5 raw/source map mismatch")
    prior = audit(root)
    paired = next(row for row in prior.summary["paired"] if row["status"]=="confirmatory")
    require(paired["n"]==2321 and all(round(100*paired[k],2)==v for k,v in
            (("estimate",1.24),("lower95",.86),("upper95",1.65))),"Registered primary differs")
    previous = {"phase3_batches":len(prior.lineage["batches"]),"phase3_validation":len(prior.rows),
                "phase5_release_hashes":len(gate["file_sha256"]),"phase5_raw_hashes":len(hashes),
                "phase5_new_records":len(fresh),"primary":paired,"phase3_reconciliation":prior.summary["reconciliation"]}
    return prior,previous


def load_archive(root):
    prior,evidence = prior_audit(root)
    ph5 = root/"results/phase5"
    records,plans,_,_ = load_new(ph5,get_protocol(root,ph5))
    for old_key,record in prior.rows.items():
        if old_key[0]!="c64":
            continue
        current = ("holdout",*old_key[1:])
        require(current not in records,"Holdout overlap")
        records[current] = dict(record,partition="holdout",source=f'results/phase3/{record["source"]}')
        plans[current] = prior.plans[old_key]
    public = {(*k[:4],PUBLIC[k[4]]):dict(v,source=v["source"] if k[0]=="holdout" and not v["source"].startswith(("raw/dev","raw/ablations"))
                                      else f'results/phase5/{v["source"]}') for k,v in records.items()}
    public_plans = {(*k[:4],PUBLIC[k[4]]):v for k,v in plans.items()}
    csv_data = csv_rows(ph5/"data/route_results.csv")
    index = {(*key(r),r["method"]):r for r in csv_data}
    require_keys(public,index,"Phase 5 route CSV")
    require(len(index)==len(csv_data)==len(public)==28910,"Phase 5 exact row count")
    for k,row in public.items():
        saved = index[k]
        v = row["validation"]
        require(int(saved["successes"])==v["successes"] and float(saved["R"])==v["reliability"] and
                abs(float(saved["completion"])-v["completion"]) < 1e-8 and saved["plan_sha256"]==row["plan_sha256"],
                f"Phase 5 flat validation mismatch: {k}")
    require(len(csv_rows(ph5/"data/instance_results.csv"))==1200,"Missing instance-method rows")
    return public,public_plans,evidence


def preflight(root,out):
    existing = out/"manifests/protocol.json"
    if existing.exists():
        return verify(root,out,all_inputs=True)
    cfg = yaml.safe_load((root/CONFIG).read_text(encoding="utf-8"))
    head = git(root,"rev-parse","HEAD").decode().strip()
    git(root,"merge-base","--is-ancestor",cfg["base_commit"],head)
    archive,evidence = prior_audit(root)
    require(all(os.getenv(k)=="1" for k in THREADS),"Use single-thread numerical settings")
    require(cfg["validation_seed"] not in {20261122,20261123,20261124,20261125,20261127},"Validation seed conflict")
    result = panels(root,out,cfg,archive.lineage["freeze_digest"])
    classes = {name:dict(Counter((r["partition"]+"-"+str(r["visits"])) for r in rows if r["route"] is not None))
               for name,rows in result.items()}
    payload = {"schema":1,"pre_execution_utc":now(),"execution_head":head,"configuration":cfg,
               "frozen_commit":archive.freeze["commit"],"freeze_digest":archive.lineage["freeze_digest"],
               "environment":environment(),"protected_sha256":protected(root,cfg["base_commit"]),
               "source_sha256":source_hashes(root),
               "panel_sha256":{name:file_sha(out/"manifests"/f"{name}_panel.csv") for name in result},
               "panel_counts":classes,"archived_reconciliation":evidence,
               "status":"prospective on previously opened benchmark"}
    write_json(existing,payload)
    return payload


def verify(root,out,*,all_inputs=False):
    protocol = read_json(out/"manifests/protocol.json")
    require(protocol["source_sha256"]==source_hashes(root),"Phase 6 execution source differs from prospective freeze")
    require(all(file_sha(out/"manifests"/f"{k}_panel.csv")==h for k,h in protocol["panel_sha256"].items()),"Panel selection changed")
    if all_inputs:
        require(protocol["protected_sha256"]==protected(root,protocol["configuration"]["base_commit"]),"Historical hash mismatch")
        require(git(root,"rev-parse","star-phase3-freeze-v1^{}").decode().strip()==protocol["frozen_commit"],"Frozen tag moved")
    return protocol
