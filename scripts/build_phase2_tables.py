#!/usr/bin/env python3
"""Build Phase-2 tables 07–14."""

from __future__ import annotations

import sys
from pathlib import Path

from star_evrp.analysis_phase2 import aggregate_results_to_csv, build_phase2_tables
from star_evrp.cli import add_root_argument, ensure_src_path, project_root_from_script


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    aggregate_results_to_csv(root)
    out = build_phase2_tables(root)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())