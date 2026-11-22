"""Dataset discovery, parsing, and instance materialization."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml

from star_evrp.geometry import build_coordinate_array, precompute_distance_matrix
from star_evrp.types import (
    EVSpecs,
    Instance,
    Node,
    NodeType,
    PartitionName,
    StationAttributes,
    VariantCode,
)

FAMILY_PATTERN = re.compile(
    r"^(?P<family>RC2|RC1|C2|C1|R2|R1)_(?P<suffix>.+)$",
    re.IGNORECASE,
)
VARIANT_DIRS = {
    "A": "variant_A_original_TW",
    "B": "variant_B_relaxed_TW",
}
DATASET_DIR_NAMES = (
    "EVRPTW_ChargingStations_Dataset",
    "evrptw_charging_stations_dataset",
)


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def discover_dataset_root(dataset_root: Path | str) -> Path:
    """Locate ``EVRPTW_ChargingStations_Dataset`` under ``dataset_root``.

    Supports an extra nesting level (e.g. ``dataset/foo/EVRPTW_...``).
    """
    root = Path(dataset_root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Dataset root does not exist: {root}")

    for name in DATASET_DIR_NAMES:
        direct = root / name
        if (direct / "params.json").is_file() and (direct / "ev_specs.json").is_file():
            return direct

    for path in root.rglob("params.json"):
        parent = path.parent
        if parent.name in DATASET_DIR_NAMES or (parent / "ev_specs.json").is_file():
            if (parent / "ev_specs.json").is_file():
                return parent

    raise FileNotFoundError(
        f"Could not find EVRPTW_ChargingStations_Dataset under {root}"
    )


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_ev_specs(dataset_root: Path) -> EVSpecs:
    data = load_json(dataset_root / "ev_specs.json")
    return EVSpecs(
        battery_capacity=float(data["battery_capacity"]),
        energy_consumption_rate=float(data["energy_consumption_rate"]),
    )


def load_dataset_params(dataset_root: Path) -> dict[str, Any]:
    return load_json(dataset_root / "params.json")


def normalize_instance_stem(path: Path) -> str:
    """Canonical instance key such as ``C1_10_1`` from file name."""
    stem = path.stem
    if stem.endswith("_stations"):
        stem = stem[: -len("_stations")]
    return stem.upper()


def parse_family_and_parent(instance_key: str) -> tuple[str, str]:
    match = FAMILY_PATTERN.match(instance_key)
    if not match:
        raise ValueError(f"Cannot infer family from instance key {instance_key!r}")
    family = match.group("family").upper()
    parent_key = instance_key
    return family, parent_key


def _parse_homberger_instance(path: Path) -> tuple[int, int, list[Node]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    vehicle_parts = lines[4].split()
    fleet_size = int(vehicle_parts[0])
    load_capacity = int(vehicle_parts[1])

    nodes: list[Node] = []
    for line in lines[9:]:
        parts = line.split()
        if len(parts) < 7:
            continue
        node_id = int(parts[0])
        x, y = float(parts[1]), float(parts[2])
        demand = float(parts[3])
        ready_time = float(parts[4])
        due_date = float(parts[5])
        service_time = float(parts[6])
        if node_id == 0:
            ntype = NodeType.DEPOT
        elif node_id <= 1000:
            ntype = NodeType.CUSTOMER
        else:
            ntype = NodeType.STATION
        nodes.append(
            Node(
                node_id=node_id,
                node_type=ntype,
                x=x,
                y=y,
                demand=demand,
                ready_time=ready_time,
                due_date=due_date,
                service_time=service_time,
            )
        )
    return fleet_size, load_capacity, nodes


def load_station_csv(path: Path) -> dict[int, StationAttributes]:
    out: dict[int, StationAttributes] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {
            "station_id",
            "charging_rate",
            "price_mu",
            "price_sigma",
            "wait_mu",
            "wait_sigma",
            "density_score",
        }
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"Station CSV missing columns at {path}")
        for row in reader:
            sid = int(row["station_id"])
            out[sid] = StationAttributes(
                station_id=sid,
                charging_rate=float(row["charging_rate"]),
                price_mu=float(row["price_mu"]),
                price_sigma=float(row["price_sigma"]),
                wait_mu=float(row["wait_mu"]),
                wait_sigma=float(row["wait_sigma"]),
                density_score=float(row["density_score"]),
            )
    return out


def build_instance(
    instance_path: Path,
    stations_path: Path,
    variant: VariantCode,
    *,
    partition: PartitionName = "unknown",
    dataset_params: dict[str, Any] | None = None,
    ev_specs: EVSpecs | None = None,
) -> Instance:
    if not stations_path.is_file():
        raise FileNotFoundError(f"Missing stations CSV: {stations_path}")

    instance_key = normalize_instance_stem(instance_path)
    family, parent_key = parse_family_and_parent(instance_key)

    fleet_size, load_capacity, nodes = _parse_homberger_instance(instance_path)
    station_attrs = load_station_csv(stations_path)

    node_id_to_index = {n.node_id: i for i, n in enumerate(nodes)}
    customer_node_ids = [n.node_id for n in nodes if n.node_type == NodeType.CUSTOMER]
    station_node_ids = [n.node_id for n in nodes if n.node_type == NodeType.STATION]

    coords = build_coordinate_array(nodes)
    dist = precompute_distance_matrix(coords)
    depot = next(n for n in nodes if n.node_type == NodeType.DEPOT)

    if ev_specs is None:
        ev_specs = EVSpecs(battery_capacity=600.0, energy_consumption_rate=1.0)

    return Instance(
        instance_key=instance_key,
        family=family,
        variant=variant,
        parent_key=parent_key,
        partition=partition,
        instance_path=instance_path.resolve(),
        stations_path=stations_path.resolve(),
        instance_file_sha256=sha256_file(instance_path),
        stations_file_sha256=sha256_file(stations_path),
        fleet_size=fleet_size,
        load_capacity=float(load_capacity),
        depot_closing_time=float(depot.due_date),
        num_customers=len(customer_node_ids),
        num_stations=len(station_node_ids),
        nodes=nodes,
        node_id_to_index=node_id_to_index,
        customer_node_ids=customer_node_ids,
        station_node_ids=station_node_ids,
        station_attributes=station_attrs,
        coordinates=coords,
        distance_matrix=dist,
        dataset_params=dataset_params or {},
        ev_specs=ev_specs,
    )


def _parents_in_family(paths: Iterable[Path]) -> dict[str, list[str]]:
    by_family: dict[str, set[str]] = {}
    for path in paths:
        key = normalize_instance_stem(path)
        family, parent = parse_family_and_parent(key)
        by_family.setdefault(family, set()).add(parent)
    return {fam: sorted(parents) for fam, parents in by_family.items()}


def assign_partitions(
    parents_by_family: dict[str, list[str]],
    development_per_family: int,
) -> dict[str, PartitionName]:
    """Map parent instance key to development or holdout."""
    assignment: dict[str, PartitionName] = {}
    for family, parents in parents_by_family.items():
        dev = set(parents[:development_per_family])
        for parent in parents:
            assignment[parent] = "development" if parent in dev else "holdout"
    return assignment


def load_experiment_splits_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def iter_instance_files(
    dataset_root: Path,
    variant: VariantCode,
) -> Iterator[Path]:
    variant_dir = dataset_root / VARIANT_DIRS[variant]
    if not variant_dir.is_dir():
        raise FileNotFoundError(f"Variant directory missing: {variant_dir}")
    for path in sorted(variant_dir.glob("*.txt")):
        if path.name.startswith("."):
            continue
        yield path


def load_all_instances(
    project_root: Path | str,
    *,
    families: Iterable[str] | None = None,
    variants: Iterable[VariantCode] | None = None,
    development_parents_per_family: int = 2,
    dataset_subdirectory: str = "dataset",
) -> list[Instance]:
    """Load all benchmark instances matching filters with partition labels."""
    root = Path(project_root).resolve()
    ds_bundle = discover_dataset_root(root / dataset_subdirectory)
    params = load_dataset_params(ds_bundle)
    ev_specs = load_ev_specs(ds_bundle)

    family_filter = {f.upper() for f in families} if families else None
    variant_list: list[VariantCode] = list(variants) if variants else ["A", "B"]

    variant_a_paths = list(iter_instance_files(ds_bundle, "A"))
    parents_by_family = _parents_in_family(variant_a_paths)
    partition_map = assign_partitions(parents_by_family, development_parents_per_family)

    instances: list[Instance] = []
    for variant in variant_list:
        for txt_path in iter_instance_files(ds_bundle, variant):
            key = normalize_instance_stem(txt_path)
            family, parent = parse_family_and_parent(key)
            if family_filter and family not in family_filter:
                continue
            stations_path = txt_path.with_name(f"{txt_path.stem}_stations.csv")
            part = partition_map.get(parent, "unknown")
            instances.append(
                build_instance(
                    txt_path,
                    stations_path,
                    variant,
                    partition=part,
                    dataset_params=params,
                    ev_specs=ev_specs,
                )
            )
    return instances


def load_single_instance(
    project_root: Path | str,
    instance_key: str,
    variant: VariantCode,
    *,
    dataset_subdirectory: str = "dataset",
) -> Instance:
    root = Path(project_root).resolve()
    ds_bundle = discover_dataset_root(root / dataset_subdirectory)
    txt_path = ds_bundle / VARIANT_DIRS[variant] / f"{instance_key}.txt"
    if not txt_path.is_file():
        txt_path = ds_bundle / VARIANT_DIRS[variant] / f"{instance_key.lower()}.txt"
    stations_path = txt_path.with_name(f"{txt_path.stem}_stations.csv")
    return build_instance(
        txt_path,
        stations_path,
        variant,
        dataset_params=load_dataset_params(ds_bundle),
        ev_specs=load_ev_specs(ds_bundle),
    )


def inventory_summary(instances: list[Instance]) -> dict[str, Any]:
    """Lightweight counts for auditing."""
    from collections import Counter

    counts = Counter((i.variant, i.family, i.partition) for i in instances)
    return {
        "num_instances": len(instances),
        "by_variant_family_partition": {f"{k[0]}/{k[1]}/{k[2]}": v for k, v in sorted(counts.items())},
        "unique_parents": len({i.parent_key for i in instances}),
    }


def load_instance(
    project_root: Path | str,
    instance_key: str,
    variant: VariantCode,
    *,
    dataset_subdirectory: str = "dataset",
) -> Instance:
    """Alias for :func:`load_single_instance`."""
    return load_single_instance(
        project_root,
        instance_key,
        variant,
        dataset_subdirectory=dataset_subdirectory,
    )


def iter_instances(
    project_root: Path | str,
    *,
    families: Iterable[str] | None = None,
    variants: Iterable[VariantCode] | None = None,
    development_parents_per_family: int = 2,
    partition: PartitionName | None = None,
    dataset_subdirectory: str = "dataset",
) -> Iterator[Instance]:
    """Yield instances matching filters."""
    all_inst = load_all_instances(
        project_root,
        families=families,
        variants=variants,
        development_parents_per_family=development_parents_per_family,
        dataset_subdirectory=dataset_subdirectory,
    )
    for inst in all_inst:
        if partition is not None and inst.partition != partition:
            continue
        yield inst


def build_partition_manifest(
    project_root: Path | str,
    *,
    development_parents_per_family: int = 2,
    dataset_subdirectory: str = "dataset",
) -> dict[str, Any]:
    """Frozen development/holdout manifest with file hashes."""
    root = Path(project_root).resolve()
    ds_bundle = discover_dataset_root(root / dataset_subdirectory)
    variant_a_paths = list(iter_instance_files(ds_bundle, "A"))
    parents_by_family = _parents_in_family(variant_a_paths)
    partition_map = assign_partitions(parents_by_family, development_parents_per_family)

    entries: list[dict[str, Any]] = []
    for variant in ("A", "B"):
        for txt_path in iter_instance_files(ds_bundle, variant):
            key = normalize_instance_stem(txt_path)
            family, parent = parse_family_and_parent(key)
            stations_path = txt_path.with_name(f"{txt_path.stem}_stations.csv")
            entries.append(
                {
                    "instance_key": key,
                    "variant": variant,
                    "family": family,
                    "parent_key": parent,
                    "partition": partition_map.get(parent, "unknown"),
                    "instance_sha256": sha256_file(txt_path),
                    "stations_sha256": sha256_file(stations_path)
                    if stations_path.is_file()
                    else None,
                }
            )
    entries.sort(key=lambda e: (e["family"], e["instance_key"], e["variant"]))
    return {
        "dataset_root": str(ds_bundle),
        "rules": {
            "selection": "lexicographic_first_n_per_family",
            "development_parents_per_family": development_parents_per_family,
        },
        "parents_by_family": parents_by_family,
        "instances": entries,
    }