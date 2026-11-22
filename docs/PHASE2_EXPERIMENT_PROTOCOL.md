# Phase 2 Experiment Protocol

## Scope

- **Development only:** 24 EVRPTW instances (12 parents × A/B).
- **Holdout sealed:** 96 instances unused for tuning or method selection.
- **Primary physics:** Q=700, h=1.0, independent lognormal waits, station TW off (deposited convention).

## Populations

1. All routes (service summary only).
2. Charging-exposed routes.
3. Exposed routes with baseline reliability < 0.95 (repair-eligible).

Zero-charge routes are never counted as repaired.

## Stages

| Stage | Purpose |
|-------|---------|
| D1 | P0 correctness reconciliation; crosswalk old/new metrics |
| D2 | Smoke on fixed routes |
| D3 | Freeze panel + budgets on development |
| D4 | Main method comparison + ablations on frozen panel |
| D5 | Freeze configs/SHA for Phase 3 (no holdout run) |

## Frozen development panel

- Built from Phase 1 `aggregate_routes.csv` among **charging-exposed** development routes.
- Stratified by family × variant × reliability bin.
- Manifest: `results/phase2/manifests/dev_panel.json`.

## Methods (same start plan, same neighborhood, same budget)

- B0 NoRepair-CON
- B1 MeanWait-Greedy
- B2 UniformQuantile
- B3 FullScenario-LS
- STaR_v1 (+ ablations)

## Budgets (development)

See `configs/phase2_dev.yaml`: wall-clock, candidate, and progressive scenario caps are identical across methods.

## Validation

- Optimization uses `opt` scenario tape.
- Final selected plans validated on independent `val` tape (`N_val`).
- Target certification requires one-sided Wilson lower bound ≥ 0.95 on validation scenarios; otherwise `uncertain` / empirical.

## Seeds

Master seed `20261122`. Stream derivation via hashlib (not Python `hash()`).
