#!/usr/bin/env python3
"""Audit Phase-2 raw result integrity."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from star_evrp.analysis_phase2 import audit_phase2_results
from star_evrp.cli import add_root_argument, ensure_src_path, project_root_from_script


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    report = audit_phase2_results(root)
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())