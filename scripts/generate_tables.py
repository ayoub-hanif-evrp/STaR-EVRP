#!/usr/bin/env python3
"""Generate Tables 1–6 (csv, md, tex)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from star_evrp.cli import add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.experiment_runner import generate_all_tables


def main() -> int:
    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    out = generate_all_tables(root)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())