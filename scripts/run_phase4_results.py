"""Independent Phase 4 audit and publication package CLI."""

import argparse
from pathlib import Path

from star_evrp.phase4_release import audit_export, build, package, tex_probe, validate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("audit","build","validate","package","all","tex"))
    parser.add_argument("--project-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    root=args.project_root.resolve()
    out=(args.output or root/"results/phase4").resolve()
    if out in root.parents or out in (root, root/"results") or any(out==path or path in out.parents for path in
                 [root/"dataset",root/"docs",root/"src",root/"configs",root/"prompts",root/"scripts",
                  root/"tests",root/".git",*[path for path in (root/"results").iterdir() if path.name!="phase4"
                  and not path.name.startswith("phase4_")]]):
        parser.error("Output must be outside the frozen/historical tree")
    if args.action in ("audit","build","all"):
        study=audit_export(root,out)
        print(f"Independent audit PASS: {len(study.rows):,} records, {len(study.cases)} original cases",flush=True)
        if args.action in ("build","all"):
            items=build(study,out)
            print(f"Built {len(items)} exhibits",flush=True)
    if args.action in ("validate","all"):
        results=validate(out)
        print(f"Format validation: {len(results['png'])} PNGs, {len(results['table_formats'])} table sets",flush=True)
    if args.action in ("tex","all"):
        print(f"TeX evidence: {tex_probe(out)}",flush=True)
    if args.action in ("all","package"):
        print(f"Handoff: {package(root,out)}",flush=True)


if __name__=="__main__":
    main()
