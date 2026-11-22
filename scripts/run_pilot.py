#!/usr/bin/env python3
"""Run development pilot (inventory + baselines + stochastic audit)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from star_evrp.cli import add_config_argument, add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.experiment_runner import run_pilot


def main() -> int:
    parser = argparse.ArgumentParser()
    add_config_argument(parser)
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    summary = run_pilot(root, args.config)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())