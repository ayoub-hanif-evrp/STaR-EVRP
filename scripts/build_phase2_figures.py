#!/usr/bin/env python3
"""Regenerate Phase-2 figures (fig07–fig16)."""

from __future__ import annotations

import sys
from pathlib import Path

from star_evrp.cli import add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.analysis_phase2 import regenerate_phase2_figures


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    paths = regenerate_phase2_figures(root)
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())