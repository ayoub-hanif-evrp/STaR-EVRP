#!/usr/bin/env python3
"""D1 crosswalk: Phase-1 audit vs fixed simulator on dev panel."""

from __future__ import annotations

import sys
from pathlib import Path

from star_evrp.cli import add_config_argument, add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.experiment_phase2 import run_d1_crosswalk


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    add_config_argument(parser)
    parser.set_defaults(config=Path("configs/phase2_dev.yaml"))
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    out = run_d1_crosswalk(root, args.config)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())