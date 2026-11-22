# Holdout figure index

All figures use the frozen `python -B scripts/phase3.py analyze` command with `src/star_evrp/phase3_analysis.py` and audited compressed batches under `results/phase3/raw/` and `results/phase3/plans/`. Output files are in `results/phase3/figures/` at 400 DPI. `results/phase3/processed/provenance.json` links the raw and derived hashes. Labels use native benchmark time units.

| PNG | Manuscript caption and source |
|---|---|
| `fig17_holdout_reliability_stars_vs_b4_b3.png` | Paired independent validation success by original route at 64 unique plan trials. The diagonal denotes equality. The two panels compare STaR to B4 and B3. Source: c64 validation records. |
| `fig18_holdout_target_attainment.png` | Point estimates at least 0.95 versus pointwise one-sided 95% Wilson lower limits at least 0.95; right panel pools variants within each family (not families across routes). Sources: c64 records, overall and family-variant tables. |
| `fig19_reliability_completion_frontier.png` | Paired objective trade-off at 64 plans. Upper left denotes simultaneously higher empirical success and lower full completion. Completion includes late trajectories. Source: c64 records. |
| `fig20_search_scenarios_vs_reliability.png` | Mean reliability versus actual incremental optimizer scenario evaluations across frozen profiles. Vertical lines are 95% family-stratified parent-cluster bootstrap intervals. Source: budget profiles and validation records. |
| `fig21_runtime_vs_reliability.png` | Reliability versus measured wall time including search overhead and excluding independent validation. Parallel execution and scheduler make time descriptive. Source: budget profiles and wall counters. |
| `fig22_stochastic_repair_by_family_variant.png` | Reliability by benchmark family and A/B window convention, matched on original routes within each cell. Source: family-variant table. |
| `fig23_partial_vs_topology_repair.png` | Distributions of paired STaR–B4 changes in success and full completion, stratified by whether the ordered station-gap sequence changed. These are descriptive strata, not randomized treatments. Source: c64 metrics plus exact plans. |
| `fig24_ablation_and_budget_sensitivity.png` | Lower-bound attainment under frozen caps/seeds and paired effects of removing partial charging at 64 plans (95% cluster intervals). Sources: budget and paired tables. |
| `fig25_individual_route_case_study.png` | First eligible R2-A route under lexicographic parent/route ordering, regardless of performance. Left: zero-wait customer and depot margins; right: full completion quantiles. Exact stops, time and energy in the case-routes table. |
| `fig26_validation_uncertainty.png` | Independently estimated reliability near 0.95 and two-sided Wilson uncertainty. These intervals are not the one-sided attainment rule. Source: c64 B3/STaR validation records. |
