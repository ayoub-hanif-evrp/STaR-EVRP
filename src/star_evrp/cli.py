"""Shared CLI helpers."""

from __future__ import annotations

import argparse
from pathlib import Path


def project_root_from_script(script_path: Path) -> Path:
    """Assume scripts live in ``<root>/scripts/``."""
    return script_path.resolve().parent.parent


def ensure_src_path(root: Path) -> None:
    import sys

    src = root / "src"
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


def add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/pilot.yaml"),
        help="Experiment YAML configuration",
    )


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (defaults to parent of scripts/)",
    )