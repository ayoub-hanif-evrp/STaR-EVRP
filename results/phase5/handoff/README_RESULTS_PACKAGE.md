# Final STaR-EVRP results handoff

This Phase 5 package is the authoritative set of publication exhibits. It does not replace the earlier raw archives, tags or preregistration.

**Mandatory disclosure:** the sole confirmatory comparison is the original holdout STaR minus FSPC reliability effect, +1.24 [+0.86, +1.65] percentage points across 2,321 exposed route pairs from 48 parents. Include T07 or disclose it in the main text. STaR uses 34.59% fewer draws than SLS but takes 29.69 vs 27.51 ms. Do not hide either comparator when streamlining the main baseline presentation.

Read the glossary, caption notes and claim matrix. Summary and instance results use c64 and 10,000-draw validation, with distinct development and holdout labels. The 120-instance results include tuning data and are descriptive. Full SLS and FSPC results, frozen secondary budgets and saved robustness stress outcomes are supplementary.

## Files for the writer

- `data/instance_results.csv`: every instance × all ten methods, with NA when exposure is zero and metrics at full precision.
- `data/population_by_instance.csv`: source fleet and original exposure accounting.
- `data/paired_effects.csv`, `data/family_ablation.csv`, `data/failure_modes.csv`, `data/work_by_cohort.csv`: complete analysis tables.
- `data/registered_route_events.csv`: the registered route's exact saved ordered events. `data/paired_routes.csv` and `data/route_results.csv` are in the repository with complete pairs and per-route rows.
- Tables in CSV, TeX and Markdown; figures in 400-DPI PNG with exact-value sidecars. See EXHIBIT_INDEX. Use the specified physical width.

## Limits

Synthetic independent waits and four shared station CSV contents; fixed offline CON customer orders; no real queue inference, fleet guarantee, or global routing optimality. The one-sided Wilson classification is pointwise. All intervals other than the original primary contrast are descriptive/exploratory and unadjusted. Topology strata are post-selection, not causal. A shared maximum of 64 unique plans does not imply equal consumed work; FSPC is a restricted heuristic, not a quantity-only optimum. Archived Phase 3 and new Phase 5 runtime cohorts are separate. The 5-second guard is cooperative. No speedup is inferred from draw counts.

Reproduce using `python -B scripts/run_phase5.py all` with the recorded thread settings and production output, or rebuild derived outputs with `analyze` and `build-exhibits` against existing audited batches. This package does not contain a manuscript.
