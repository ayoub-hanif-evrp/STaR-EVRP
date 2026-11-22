"""Single entry point for the immutable Phase 3 experiment."""

import argparse
import json
from pathlib import Path

from star_evrp.phase3 import canonical, config, digest, execute, freeze, preflight, smoke, verified_freeze
from star_evrp.phase3_analysis import analyze, audit, paper
from star_evrp.results_io import save_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "freeze", "smoke", "run", "replay", "analyze", "audit", "report"))
    parser.add_argument("--config", default="configs/phase3_frozen.yaml")
    parser.add_argument("--output", type=Path, default=Path("results/phase3"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = args.output.resolve()
    if args.action == "preflight":
        print(json.dumps(preflight(root, args.config, out)["phase25_reconciled"], indent=2))
    elif args.action == "freeze":
        print(freeze(root, args.config, out)["commit"])
    elif args.action == "smoke":
        frozen, _ = verified_freeze(root, out)
        evidence = {"freeze": digest(canonical(frozen)), **smoke(root, frozen["config"])}
        path = out / "manifests/smoke.json"
        if not path.exists():
            save_json(path, evidence)
        print(evidence)
    elif args.action in ("run", "replay"):
        execute(root, out, replay=args.action == "replay")
    elif args.action == "analyze":
        analyze(root, out)
    elif args.action == "audit":
        print(audit(root, out))
    else:
        paper(root, out)


if __name__ == "__main__":
    main()
