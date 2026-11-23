"""Record independently observed test, visual and repeatability evidence."""

import argparse
import re
from pathlib import Path

from star_evrp.phase4_release import package, validate
from star_evrp.phase4_results import file_sha, read_json, require, unchanged_scope, write_json


def finalize(root, out, repeat):
    lineage=read_json(out/"audit/lineage.json")
    audit=read_json(out/"audit/audit_summary.json")
    require(audit["status"]=="pass","Cannot release unreconciled outcomes")
    unchanged_scope(root,lineage)
    formats=validate(out)
    tex=read_json(out/"audit/tex_check.json")
    require(tex["status"] in ("pass","unavailable"),"LaTeX compilation failed")
    visual=read_json(out/"audit/visual_inspection.json")
    require(set(visual["figures"])==set(formats["png"]),"Not all figures were inspected")
    for name, checked in visual["figures"].items():
        require(checked["sha256"]==file_sha(out/name) and checked["status"]=="pass","Visual review is stale or failed")
    matches={}
    for head in ("data","figures","tables"):
        paths={path.relative_to(out).as_posix() for path in (out/head).rglob("*") if path.is_file()}
        second={path.relative_to(repeat).as_posix() for path in (repeat/head).rglob("*") if path.is_file()}
        require(paths==second,f"Clean repeat differs in {head} membership")
        for name in sorted(paths):
            matches[name]=file_sha(out/name)
            require(matches[name]==file_sha(repeat/name),f"Clean repeat mismatch: {name}")
    write_json(out/"audit/repeatability.json",{"status":"pass","canonical_files":len(matches),"sha256":matches})
    tests={}
    for key in ("phase4_tests","full_tests"):
        path=out/"logs"/f"{key}.txt"
        raw=path.read_bytes()
        result=raw.decode("utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig")
        count=re.search(r"(\d+) passed",result)
        require(count is not None and " failed" not in result and " skipped" not in result,"Test gate requires passing, non-skipped tests")
        tests[key]={"passed":int(count[1]),"sha256":file_sha(path)}
    gates={f"P4-G{index}":"PASS" for index in range(7)}
    quality={
        "gates":gates,"tests":tests,"tex":tex,"repeatability_files":len(matches),
        "png_counts":{"main":sum("/main/" in name for name in formats["png"]),
                      "supplementary":sum("/supplementary/" in name for name in formats["png"])},
        "table_bundles":len(formats["table_formats"]),"immutable_inputs_unchanged":True,
        "validated_records":audit["plans"],"stochastic_validation_not_rerun":True,
        "visual_evidence":"audit/visual_inspection.json",
        "method":"Independent hashes, reconstructions, counts and bootstrap; three table formats; 400-DPI PNG header and visual audits; clean repeat; archive byte round trip.",
        "limitations":["One confirmatory reliability contrast; no new confirmatory trial",
                       "No explicit archived stop reason; c64 exhaustion inferred under unhit caps",
                       "Synthetic waits, four shared station attribute tables, measured archived wall time not a speedup",
                       "This quality envelope excludes its own checksum"],
        "unavailable":[] if tex["status"]=="pass" else ["Full TeX compile unavailable; table syntax and value checks passed"],
    }
    path=out/"audit/final_quality_gate.json"
    write_json(path,quality)
    archive=package(root,out)
    quality["handoff"]=archive
    quality["files"]={name.relative_to(out).as_posix():file_sha(name) for name in sorted(out.rglob("*"))
                      if name.is_file() and name!=path}
    write_json(path,quality)
    return quality


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("results/phase4"))
    parser.add_argument("--repeat",type=Path,default=Path("results/phase4_repeat"))
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    report=finalize(root,args.output.resolve(),args.repeat.resolve())
    print(report["gates"],report["tests"])
