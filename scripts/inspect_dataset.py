#!/usr/bin/env python3
"""Print dataset inventory summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from star_evrp.cli import add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.data_loader import load_all_instances, inventory_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect EVRPTW dataset inventory")
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)

    instances = load_all_instances(root)
    summary = inventory_summary(instances)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())