# Dataset audit

## Inventory

- Bundle: `dataset/EVRPTW_ChargingStations_Dataset/`
- Variants: `variant_A_original_TW/`, `variant_B_relaxed_TW/`
- Sidecars: `ev_specs.json`, `params.json`, per-instance `*_stations.csv`
- Deposited solvers: `dataset/EVRPTW_ChargingStations_Dataset/code/`

`scripts/inspect_dataset.py` prints family counts and SHA-256 fingerprints via `data_loader.build_partition_manifest`.

## Hashes

Each `Instance` stores:

- `instance_file_sha256` for the Homberger `.txt`
- `stations_file_sha256` for the matching CSV

Manifest entries in `build_partition_manifest` duplicate these hashes for reproducibility audits. Prefer SHA-256 over ad hoc checksums when comparing downloads.

## Split rules

- Parents inferred from variant **A** instance stems per family (`C1`, `C2`, …).
- Lexicographic sort; first `development_parents_per_family` (default **2**) → **development**; remaining parents → **holdout**.
- Variant B instances inherit the same partition label as their A sibling (`parent_key`).

Configuration mirror: `configs/experiment_splits.yaml`.