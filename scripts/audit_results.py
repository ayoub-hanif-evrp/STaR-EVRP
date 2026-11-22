#!/usr/bin/env python3
"""Audit completeness of baselines and raw audit JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from star_evrp.cli import add_config_argument, add_root_argument, ensure_src_path, project_root_from_script
from star_evrp.data_loader import iter_instances
from star_evrp.experiment_runner import load_experiment_config
from star_evrp.results_io import list_completed_keys, result_key


def main() -> int:
    parser = argparse.ArgumentParser()
    add_config_argument(parser)
    add_root_argument(parser)
    args = parser.parse_args()
    root = args.root or project_root_from_script(Path(__file__))
    ensure_src_path(root)
    config = load_experiment_config(args.config)
    ds = config.get("dataset", {})
    expected = [
        result_key(i.instance_key, i.variant)
        for i in iter_instances(
            root,
            families=ds.get("families"),
            variants=ds.get("variants"),
            development_parents_per_family=int(ds.get("development_parents_per_family", 2)),
            partition="development",
        )
    ]
    baselines = list_completed_keys(root / "results" / "baselines")
    audits = {k.replace("__audit", "") for k in list_completed_keys(root / "results" / "raw", "*__audit.json")}
    report = {
        "expected_development": len(expected),
        "baselines_present": len([k for k in expected if k in baselines]),
        "audits_present": len([k for k in expected if k in audits]),
        "missing_baselines": [k for k in expected if k not in baselines],
        "missing_audits": [k for k in expected if k not in audits],
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())