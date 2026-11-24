"""Finalize release only after tests, independent replay, rebuild and visual review."""

import argparse
import re
from pathlib import Path

from star_evrp.phase4_results import file_sha, read_json, require, write_json
from star_evrp.phase5_release import package, validate


def finalize(root,out,repeat):
    entries=validate(root,out)
    tex=read_json(out/"audit/tex_check.json")
    require(tex["status"]=="pass","TeX acceptance failed")
    formats=read_json(out/"audit/formats.json")["figures"]
    visual=read_json(out/"audit/visual.json")
    require(set(formats)==set(visual["figures"]),"Visual evidence incomplete")
    for name,info in visual["figures"].items():
        require(info["sha256"]==formats[name]["sha256"] and info["reviewed"],"Stale visual proof")
    hashes={}
    for scope in ("figures","tables","data"):
        first={p.relative_to(out).as_posix() for p in (out/scope).rglob("*") if p.is_file()}
        second={p.relative_to(repeat).as_posix() for p in (repeat/scope).rglob("*") if p.is_file()}
        require(first==second,"Derived rebuild has different files")
        for name in sorted(first):
            hashes[name]=file_sha(out/name)
            require(hashes[name]==file_sha(repeat/name),f"Rebuild byte mismatch: {name}")
    write_json(out/"audit/repeatability.json",{"status":"PASS","files":hashes})
    observed=read_json(out/"audit/preexecution_test_observation.json")
    require(observed["passed"]>0,"Missing pre-execution component evidence")
    tests={"preexecution_components":observed["passed"]}
    for name in ("phase5_tests","full_tests"):
        raw=(out/"logs"/f"{name}.txt").read_bytes()
        report=raw.decode("utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig")
        matches=re.search(r"(\d+) passed",report)
        require(matches and " failed" not in report and " skipped" not in report,"Failed test report")
        tests[name]=int(matches[1])
    summary=read_json(out/"data/summary.json")
    replay=[read_json(out/"audit"/f"{stage}_replay.json") for stage in ("development","ablations")]
    require(all(not log["errors"] and log["scalar_per_plan"]==5 for log in replay),"Replay evidence incomplete")
    amount=sum(log["records"] for log in replay)
    require(amount==summary["counts"]["new_controls"]+summary["counts"]["new_ablations"],"Replay denominator differs")
    quality={"gates":{f"P5-G{number}":"PASS" for number in range(7)},"tests":tests,"frozen_inputs_unchanged":True,
             "new_replay_records":amount,"reference_scalar_checks":5*amount,"clean_repeat_files":len(hashes),
             "pngs":len(entries["figures"]),"table_bundles":len(entries["tables"]),"tex":tex,
             "interpretation":"Only the original holdout c64 STaR minus FSPC reliability remains confirmatory.",
             "execution_note":"First reporting path raised NameError after replay computations. Additive reporter replayed unchanged batches; no optimization rerun.",
             "release_commit":"Verify GitHub main; the producer base commit and byte-exact new source hashes are in the handoff."}
    path=out/"audit/final_gate.json"
    write_json(path,quality)
    members,digest=package(root,out,summary)
    quality["package"]={"zip_members":members,"sha256":digest}
    quality["file_sha256"]={p.relative_to(out).as_posix():file_sha(p) for p in sorted(out.rglob("*")) if p.is_file() and p!=path}
    write_json(path,quality)
    return quality


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("results/phase5"))
    parser.add_argument("--repeat",type=Path,default=Path("results/phase5_repeat"))
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    print(finalize(root,args.output.resolve(),args.repeat.resolve())["gates"])
