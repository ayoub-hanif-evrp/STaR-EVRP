"""Phase 5 results only: frozen controls, component ablations, replay and release."""

import argparse
from pathlib import Path

from star_evrp.phase5_experiments import execute, preflight, settings


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("preflight","run-development","run-ablations","replay","analyze",
                                          "build-exhibits","audit","package","all"))
    parser.add_argument("--project-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path)
    parser.add_argument("--workers",type=int)
    args=parser.parse_args()
    root=args.project_root.resolve()
    out=(args.output or root/"results/phase5").resolve()
    if out in root.parents or out in (root,root/"results") or any(
        out==path or path in out.parents for path in (*[root/name for name in ("src","docs","dataset","configs",
                                                "scripts","tests","prompts",".git")],
          *[path for path in (root/"results").iterdir() if not path.name.startswith("phase5")])
    ):
        parser.error("Output must be separate from source and historical results")
    workers=args.workers or settings(root)[0]["workers"]
    if workers<1:
        parser.error("Worker count must be positive")
    if args.action in ("preflight","all"):
        protocol=preflight(root,out,workers)
        print(f"Pre-execution protocol and equivalence verified; workers: {protocol['workers']}",flush=True)
    for stage in ("development","ablations"):
        if args.action in (f"run-{stage}","all"):
            print(f"{stage}: {execute(root,out,stage)['records']:,} new records",flush=True)
        if args.action in ("replay","all"):
            from star_evrp.phase5_replay import replay_stage

            print(f"{stage} replay: {replay_stage(root,out,stage)['records']:,} records",flush=True)
    if args.action in ("analyze","build-exhibits","audit","package","all"):
        from star_evrp.phase5_release import action

        action(root,out,args.action)


if __name__=="__main__":
    main()
