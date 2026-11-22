# Baseline reproduction notes

## Deposited code

`baseline.generate_baseline` imports `evrptw_solvers` from `dataset/EVRPTW_ChargingStations_Dataset/code/` and mirrors constructive (CON) and hill-climb (HC) routing. Customer sequences are expanded to explicit depot–station–customer paths via `simulate_route_baseline_expansion`.

## Battery capacity discrepancy

- Packaged `ev_specs.json` sets **Q = 600**.
- Pilot baselines and deposited experiments in this repository often use **Q = 700** (legacy deposited setting).

Do **not** claim bitwise reproduction of published CON/HC tables without a documented parity proof. JSON under `results/baselines/` records hashes, method labels, and validation outcomes for audit.

## Validation

Every generated `Solution` is checked with `route_validator.validate_solution` (coverage + independent simulation). Failures surface in `metadata.validation_issues`.