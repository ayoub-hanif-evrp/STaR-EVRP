# Experiment protocol (Phase 1)

## Partitions

- **Development**: first two lexicographic parents per family (variant A manifest).
- **Holdout**: remaining parents; used only for frozen reporting, not iterative tuning.

Variant A and B of the same parent share a partition label.

## Pilot configuration

See `configs/pilot.yaml`:

- Subset of development instances for runtime-bounded pipelines.
- Baseline generation → stochastic diagnostics → repair probe → figures/tables.

Full factorial sweeps are deferred until Phase 2 STaR search is wired.

## Artifacts

| Stage | Output directory |
|-------|------------------|
| Baselines | `results/baselines/` |
| Raw pilot metrics | `results/raw/` |
| Figures | `results/figures/` |
| Tables | `results/tables/` |
| Manifests | `results/manifests/` |

Each JSON records dataset hashes and seeds where applicable.