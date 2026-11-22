# Phase 2 → Phase 3 Readiness

## Frozen for Phase 3

| Item | Location |
|------|----------|
| Development panel | `results/phase2/manifests/dev_panel.json` |
| Freeze manifest | `results/phase2/manifests/phase2_freeze.json` |
| Configs | `configs/phase2_*.yaml` |
| Method | `STaR_v1` (`star_optimizer.py`) |
| Baselines | B0–B3 (`baseline_optimizers.py`) |
| Holdout | **SEALED** — not read for tuning |

## Phase 3 holdout specification (do not run yet)

1. Load the 96 holdout instances from the frozen Phase 1 split.
2. Start from deposited CON baselines regenerated at Q=700 (or import Phase 1–style CON solutions if produced for holdout later).
3. Run B0 and STaR_v1 (and optionally B3) under **identical** budgets as `configs/phase2_dev.yaml`.
4. Validate selected plans on an independent `holdout` scenario stream derived from `(master_seed, parent, variant, route_id, "holdout")`.
5. Report Populations B/C only for charging-exposed routes; never retune thresholds after seeing holdout outcomes.

Entry point (to be created in Prompt 3): `scripts/run_phase3_holdout.py`.

## Recommendation

STaR_v1 is competitive with strong same-neighborhood baselines on the development panel, with **material speed advantage** and a clear ablation signal that **partial charging** matters. It merits a Phase 3 confirmatory holdout study for a conference paper, with honest reporting that MeanWait-Greedy / UniformQuantile can match attainment under this budget.
