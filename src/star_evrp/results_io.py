"""JSON persistence with atomic writes and resume helpers."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

from star_evrp.types import FeasibilityReport, RouteTrace, Solution


class ResultsEncoder(json.JSONEncoder):
    """Encode dataclasses and numpy scalars for JSON."""

    def default(self, o: Any) -> Any:
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        if hasattr(o, "item"):
            try:
                return o.item()
            except Exception:
                pass
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def _serialize(obj: Any) -> Any:
    if isinstance(obj, Solution):
        return {
            "instance_key": obj.instance_key,
            "variant": obj.variant,
            "method": obj.method,
            "battery_capacity": obj.battery_capacity,
            "energy_consumption_rate": obj.energy_consumption_rate,
            "routes": [
                {
                    "route_id": r.route_id,
                    "customer_indices": r.customer_indices,
                    "stops": [
                        {
                            "node_id": s.node_id,
                            "energy_charged": s.energy_charged,
                            "wait_extra": s.wait_extra,
                        }
                        for s in (r.stops or [])
                    ],
                }
                for r in obj.routes
            ],
            "total_distance": obj.total_distance,
            "feasible": obj.feasible,
            "metadata": obj.metadata,
        }
    if isinstance(obj, RouteTrace):
        return obj.to_dict()
    if isinstance(obj, FeasibilityReport):
        return {
            "feasible": obj.feasible,
            "issues": [asdict(i) for i in obj.issues],
            "traces": [t.to_dict() for t in obj.traces],
        }
    if is_dataclass(obj):
        return asdict(obj)
    return obj


def save_json(path: Path | str, data: Any, *, indent: int = 2) -> None:
    """Atomically write JSON to ``path``."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _serialize(data)
    fd, tmp_name = tempfile.mkstemp(
        prefix=target.name,
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=indent, cls=ResultsEncoder)
            fh.write("\n")
        os.replace(tmp_name, target)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def load_json(path: Path | str) -> Any:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def result_key(instance_key: str, variant: str, suffix: str = "") -> str:
    base = f"{instance_key}__{variant}"
    return f"{base}__{suffix}" if suffix else base


def list_completed_keys(results_dir: Path | str, pattern: str = "*.json") -> set[str]:
    root = Path(results_dir)
    if not root.is_dir():
        return set()
    keys: set[str] = set()
    for path in root.glob(pattern):
        keys.add(path.stem)
    return keys


def filter_pending(keys: Iterable[str], completed: set[str]) -> list[str]:
    """Return keys that are not yet present in ``completed``."""
    return [k for k in keys if k not in completed]


def merge_resume(
    path: Path | str,
    updates: dict[str, Any],
    *,
    skip_existing: bool = True,
) -> dict[str, Any]:
    """Merge ``updates`` into an on-disk JSON dict, respecting resume semantics."""
    target = Path(path)
    if target.is_file():
        current = load_json(target)
        if not isinstance(current, dict):
            current = {"entries": current}
    else:
        current = {}

    entries = current.setdefault("entries", {})
    for key, value in updates.items():
        if skip_existing and key in entries:
            continue
        entries[key] = _serialize(value)
    save_json(target, current)
    return current