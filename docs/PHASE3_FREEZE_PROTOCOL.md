# Phase 3 freeze protocol — prepared, not authorized

## Identified development snapshot

- Base Git SHA: `de78ccb2421862ad880954345c9a97425b3f0c25`. Corrected code is in the working tree. The exact sources/configurations/CON inputs and dataset hashes used for Phase 2.5 are identified by `results/phase25/manifest.json`. Keep the frozen bytes or regenerate the manifest against an unchanged semantic source snapshot when the work is committed; do not attribute the corrected code to the base commit alone.
- `results/phase25/analysis_manifest.json` records the analysis and search-replay source hashes, raw batch hashes, and the parent-resampling protocol.
- `configs/phase25.yaml`: 512 optimization draws, 4,096 validation draws, master seed 20261122, parent bootstrap seed 18463. Conditions: Q=700, h=1, target=0.95, station hours off, independent synthetic visit waits, CON starting routes. See `docs/PHASE25_METHOD_COMPARISON.md` for methods and budgets.
- No Phase 3 outcomes have been generated. The older readiness report and any draft Phase 3 instructions are not authorization, and do not supersede the audited protocol automatically.

## Comparison specification to lock before unsealing

1. After explicit authorization, record the actual corrected commit, source and dataset hashes, resolved config and dependency versions in an immutable run namespace. Validate the frozen parent allowlist and the A/B sibling rule. Regenerate deposited CON deterministically for held-out routes at Q=700/h=1 only after the holdout run is authorized. Record and report all baseline failures rather than silently excluding them.
2. Primary test: compare STaR with B4 at the common 64-plan cap, on all charging-exposed CON routes, using paired validation reliability and full completion. Also report B0–B3, attainment, common-attainment completion, and separate all-route and empirically below-target service summaries. B3 at the common 8,192-draw cap is the efficiency comparison; report runtime and overhead, not just scenarios. Retain the 24-plan profile for sensitivity and treat any timed profile as diagnostic unless an independently verified worker cutoff is added and frozen before unsealing.
3. Use the same declared physical constraints, shared ordinal standard-normal tapes, independent final validation and one-sided Wilson rule across methods. Use a separate, keyed final holdout validation split and keep it out of all decisions. If multiple optimizer seeds are wanted, fix the grid and aggregation rule before running; do not select the best post hoc.
4. Pair within the original route and resample the Homberger parent with both variants and all routes intact. Report reliability, expected completion, cost on the common attaining routes, attainment, elapsed work, compute budgets and failures. Treat secondary comparisons as such; any simultaneous claims require a prespecified multiplicity rule. Store ordered plans and independent verification records and produce only data-backed PNG figures at 300–400 DPI.
5. Never change methods, screens, target thresholds or budgets based on observed holdout outcomes. A holdout miss means that the proposed claim did not confirm, not that the method is entitled to retuning.

**Gate:** Conditional scientific case for incremental topology benefit and scenario efficiency, not a confirmed general advantage. The holdout driver and signed-off release freeze are future work, not part of this development run. Keep the holdout sealed until explicitly instructed.
