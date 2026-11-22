#!/usr/bin/env python3
"""Regenerate all PNG figures from saved results."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from star_evrp.cli import add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.plotting import regenerate_all_figures


def main() -> int:
    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    results = root / "results"
    figures = root / "results" / "figures"
    paths = regenerate_all_figures(results, figures)
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())