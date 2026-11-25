"""Build and verify the conference exhibits from immutable archives."""

import argparse
import os
import sys
from pathlib import Path

for variable in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[variable]="1"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

from star_evrp.conference_audit import audit, package, proofs, verify_input_protection
from star_evrp.conference_exhibits import build
from star_evrp.phase4_results import require


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("build","audit","proofs","package"))
    parser.add_argument("--project-root",type=Path,default=Path("."))
    parser.add_argument("--output",type=Path,default=Path("results/conference"))
    parser.add_argument("--width-mm",type=float,default=178)
    parser.add_argument("--pdf-tools",type=Path,help="Optional locally installed pypdfium2 directory")
    parser.add_argument("--scratch",type=Path,help="Proof or ZIP extraction directory")
    args=parser.parse_args()
    root=args.project_root.resolve()
    out=(root/args.output).resolve()
    require(out!=root and not out.is_relative_to(root/"dataset") and not out.is_relative_to(root/"src"),"Unsafe output")
    frozen_results=root/"results"
    if out.is_relative_to(frozen_results):
        entry=out.relative_to(frozen_results).parts
        require(entry and (entry[0]=="conference" or entry[0].startswith("conference_")),
                "Use a new output outside archived result folders")
    if args.command=="build":
        verify_input_protection(root,out)
        build(root,out,args.width_mm)
        print(f"Built five figures and three tables in {out}")
        return
    if args.command=="package":
        scratch=(root/(args.scratch or Path("results/conference_zip_check"))).resolve()
        require(not scratch.exists() and not scratch.is_relative_to(out),"Use an empty ZIP proof directory outside the release")
        print(package(root,out,scratch))
        return
    if args.pdf_tools:
        sys.path.insert(0,str(args.pdf_tools.resolve()))
    try:
        import pypdfium2
    except ImportError:
        parser.error("audit and proofs need pypdfium2. See the conference exhibit report for the optional tool setup.")
    if args.command=="audit":
        audit(root,out,pypdfium2)
        print(f"Verified archives, figure formats, spatial plan and diagram in {out}")
    else:
        scratch=(root/(args.scratch or Path("results/conference_proofs"))).resolve()
        require(not scratch.is_relative_to(out),"Proofs must be outside the release directory")
        proofs(out,scratch,pypdfium2)
        print(f"Rendered figure proofs and compiled all three tables at {scratch}")


if __name__=="__main__":
    try:
        main()
    except (FileNotFoundError,ValueError) as exc:
        sys.exit(f"Conference build or audit failed: {exc}")
