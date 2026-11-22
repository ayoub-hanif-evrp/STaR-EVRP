#!/usr/bin/env python3
"""Generate CON baselines for development instances."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from star_evrp.cli import add_config_argument, add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.experiment_runner import load_experiment_config, run_baseline_generation, write_dataset_inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    add_config_argument(parser)
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    config = load_experiment_config(args.config)
    write_dataset_inventory(root, config)
    saved = run_baseline_generation(root, config)
    print(f"Generated {len(saved)} baselines: {saved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())