"""Phase 6 scientific supplement. Run from the repository root."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[name] = "1"

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

from star_evrp.phase4_results import read_json, require
from star_evrp.phase6_archive import now, preflight, verify, write_bytes, write_json
from star_evrp.phase6_diagnostics import diagnose
from star_evrp.phase6_run import run_stage


STAGES = ("as1","fixed-topology","timing")


def math_check(root,out):
    path = out/"audit/math_check.json"
    if path.exists():
        result = read_json(path)
        require(result["status"]=="pass","Mathematical tests did not pass")
        return result
    command = [sys.executable,"-B","-m","pytest","-p","no:cacheprovider","-q","tests/test_phase6_math.py"]
    result = subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    write_bytes(out/"logs/math_tests.txt",result.stdout)
    write_json(path,dict(status="pass" if result.returncode==0 else "fail",command=command[1:],exit=result.returncode,utc=now()))
    print(result.stdout.decode(errors="replace"),flush=True)
    require(result.returncode==0,"Phase 6 mathematical tests failed")
    return read_json(path)


def diagnostics(root,out,protocol):
    path = out/"audit/diagnostics.json"
    return read_json(path) if path.exists() else diagnose(root,out,protocol)


def as1_gate(root,out,protocol):
    math_check(root,out)
    result=diagnostics(root,out,protocol)
    policy=protocol["configuration"]
    eligible=result["single"]/result["exposed"]>=policy["as1_min_share"] and result["single_development"]>=policy["as1_min_development_routes"]
    write_json(out/"audit/as1_gate.json",dict(eligible=eligible,single=result["single"],exposed=result["exposed"],
        development_single=result["single_development"],hybrid=False,hybrid_reason="Excluded prospectively",
        reason="Share and development count meet frozen thresholds" if eligible else "Frozen eligibility threshold not met"))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("preflight","diagnose","math-check",*STAGES,"replay",
                                           "analyze","build-exhibits","audit","package","all","production"))
    parser.add_argument("--project-root",type=Path,default=Path("."))
    parser.add_argument("--output",type=Path,default=Path("results/phase6"))
    args=parser.parse_args()
    root=args.project_root.resolve()
    out=(root/args.output).resolve()
    task=args.command
    if task=="preflight":
        result = preflight(root,out)
        print(result["panel_counts"],flush=True)
        return
    if task=="math-check":
        math_check(root,out)
        return
    protocol=preflight(root,out) if task in ("all","production") else verify(root,out)
    if task=="diagnose":
        diagnostics(root,out,protocol)
    elif task in STAGES:
        math_check(root,out)
        if task=="as1":
            as1_gate(root,out,protocol)
        run_stage(root,out,protocol,task)
    elif task in ("production","all","replay"):
        if task!="replay":
            as1_gate(root,out,protocol)
            for stage in STAGES:
                run_stage(root,out,protocol,stage)
        for stage in STAGES:
            run_stage(root,out,protocol,stage,replay=True)
        if task=="all":
            from star_evrp.phase6_release import action
            for item in ("analyze","build-exhibits","audit","package"):
                action(root,out,protocol,item)
    else:
        from star_evrp.phase6_release import action
        action(root,out,protocol,task)


if __name__=="__main__":
    main()
