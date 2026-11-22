#!/usr/bin/env python3
"""Phase-2 STaR ablation grid on dev panel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from star_evrp.cli import add_config_argument, add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.experiment_phase2 import run_ablations


def main() -> int:
    parser = argparse.ArgumentParser()
    add_config_argument(parser)
    parser.set_defaults(config=Path("configs/phase2_ablation.yaml"))
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    summary = run_ablations(root, args.config)
    print(json.dumps(summary, indent=2))
    return 0 if not summary.get("errors") else 1


if __name__ == "__main__":
    sys.exit(main())