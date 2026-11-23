# Phase 4 — Independent results audit

**Decision: publication exhibits cleared for a narrow claim.** At the registered 64-plan maximum, STaR improved route reliability over the implemented fixed-station B4 by **1.24 percentage points** (95% family-stratified parent-cluster interval **0.86–1.65**). The parent-equal sensitivity was **1.12 pp [0.79, 1.47]**. This does not establish general dominance over scenario-based local search or over an optimal quantity-only solver.

## Lineage and verified population

- Audit checkout HEAD: `149d9f4d8f616d78ce0c295696515f1bbc342967`; Phase 4 scripts are working-tree additions identified by SHA-256 in the handoff manifest, not code from that old commit. The frozen executable remains `c657aa69d55178c85b4759475933b36d1bcc2181`, tag `star-phase3-freeze-v1`. No new optimization, stress design, holdout experiment, or manuscript edits.
- Verified 244 frozen dataset files, the tagged source blobs, the published artifact bytes (allowing only Git text line-ending normalization for Git comparisons), and **1,248** compressed bundles. The archived CON ZIP was read directly and compared with the locally restored copies. All **6,864** original CON routes passed deterministic checks, including **2,321 initially exposed** and **4,543 no-charge** routes, across **96 A/B problems from 48 parents**. Phase 4 reconstructed and checked **37,136** selected plans deterministically and checked their stored final-validation summaries, including **27,852** saved stress summaries. The earlier archived stochastic and scalar replay evidence was verified, not regenerated.
- Recomputed all nine published CSV families used for numerical reconciliation: overall, population, family/variant, paired, budget, mechanism, robustness, parent effects, and registered case events. Counts and keys match exactly. Rounded numeric tolerance is max of `5.1e-8 × magnitude` and `1e-11` in each archival field's own units. No scientifically material discrepancy. The final Phase 3 report's headline counts, means and contrasts agree. The Wilson formulas were implemented separately from Phase 3, and the 9,999-draw bootstrap resamples complete A/B parent blocks within the six fixed family strata.
- Four byte-distinct station-attribute CSV contents cover the 120 problems, appearing on 40, 40, 20 and 20 problems respectively. All four were present in development; none is an unseen station table. This is a holdout of Homberger parents, not an infrastructure generalization test.

## What to report

- **STaR–B4:** 2,211 vs. 2,161 Wilson-attaining routes out of 2,321; unconditional full completion **−33.15** native time units [−34.86, −31.48], an exploratory endpoint. Candidate trials averaged **62.67 vs. 20.18** (median 64 vs. 10). STaR hit 64 on 1,980 routes and B4 on 291. B4's 2,030 no-limit stops are consistent with exhaustion of its implemented neighborhood; the archive does not store explicit termination labels. Do not call this equal actual work.
- **STaR–B3:** **+0.32 pp** [0.13, 0.49] exploratory reliability difference; 13,024 vs. 19,911 mean incremental search draws (**34.59% lower**, denominator B3) but **29.69 vs. 27.51 ms** mean search wall time under six-worker contention. B4 averaged 8.38 ms. The 5-second guard is cooperative, not preemptive.
- **Negative cases:** B0 has 628 point-below-target routes but 635 Wilson nonattainments. STaR's 110 Wilson nonattainments consist of 4 point-only, 104 predominantly customer-only, 2 predominantly joint, and no predominantly depot-only cases; 109 occur in R2 or RC2. “Predominantly” refers to the route's most numerous observed scenario failure category. The one-sided bound is a pointwise classification, not a synchronized or fleet-level guarantee.
- **Paired route outcomes:** STaR vs. B4 has 160 higher, 2,050 equal and 111 lower observed success counts; full completion is shorter on 1,215, tied on 1,002, longer on 104 (absolute native-unit tolerance `1e-8`). Directions describe sampled estimates. Topology strata are post-selection, not causal; their weighted contributions sum to the pooled estimate. In the registered example, B4 and STaR have identical completion quantiles, so their curves overlap.

## Main exhibits

| Main PNG (in `results/phase4/figures/main/`) | Purpose | Companion table bundle |
|---|---|---|
| `F01_primary_parent_effects.png` | Pooled confirmatory interval plus all 48 parent means | `T03_paired_contrasts` |
| `F02_method_reliability_attainment.png` | Separate mean reliability and count-based attainment | `T02_primary_methods` |
| `F03_paired_reliability_completion.png` | Route-paired quality trade-off against B4 and B3 | `T03_paired_contrasts` |
| `F04_scenario_work.png` | Incremental draws at discrete budget profiles | `T04_frozen_budgets` |
| `F05_wall_runtime.png` | Measured elapsed cost versus reliability | `T04_frozen_budgets` |
| `F06_family_variant_attainment.png` | Unequal denominators and hard R2/RC2 strata | `T05_family_attainment` |
| `F07_topology_and_ablation.png` | Descriptive topology strata and distinct no-partial contrast | `T06_mechanism` |
| `F08_fixed_plan_robustness.png` | Three synthetic stresses without reoptimization | `T07_robustness` |

The remaining main table, `T01_population`, gives the population accounting. There are 3 supplementary PNGs (registered hard route, Wilson uncertainty, consumed trials) and 15 supplementary table bundles. All 22 table bundles include CSV, TeX and Markdown. See the exhibit index for file-level lineage and captions.

## Acceptance gates

| Gate | Status | Evidence |
|---|---|---|
| P4-G0 Independent audit | PASS | Exact coverage and source/plan hashes; all published comparison cells and primary interval reconcile |
| P4-G1 Comparator integrity | PASS | Frozen method truth table, count distributions, honest exhaustion inference, CPU/elapsed/MC distinction |
| P4-G2 Figures | PASS | 8 main + 3 supplementary PNGs; audited PNG CRC, dimensions and 400 DPI; two proof scales reviewed |
| P4-G3 Tables | PASS | 22 matched three-format bundles; compiled together with Tectonic/booktabs/longtable/graphicx |
| P4-G4 Descriptive checks | PASS | All 110 failures categorized; pair directions, work, stress, threshold uncertainty and topology audit |
| P4-G5 Quality/reproducibility | PASS | 9 Phase 4 tests and 71 full-suite tests; clean-repeat canonical data, PNG and table hashes match; frozen inputs unchanged |
| P4-G6 Handoff | PASS | Source-linked exhibit index, claims and numbers, captions, limitations and validated ZIP |

The original Tectonic cache lacked a standard class file; after fetching standard resources, the final compile passed. Unchanged Phase 3 sources and archive checks, tests, PNG/DPI/captions, repeatability and ZIP round trip are recorded in `results/phase4/audit/final_quality_gate.json`. No scientific figure was exported as PDF/SVG/JPEG; the temporary TeX table compile output was not retained.

## Reproduce

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python -B scripts/run_phase4_results.py all
python -B scripts/run_phase4_results.py all --output results/phase4_repeat
python -B -m pytest -p no:cacheprovider -q tests/test_phase4_results.py
python -B -m pytest -p no:cacheprovider -q
python -B scripts/finalize_phase4_quality.py
```

The finalizer verifies captured test transcripts, visual review hashes and the clean re-run; see `docs/PHASE4_RESULTS_HANDOFF.md` for evidence paths. The compact writing-agent bundle is `results/phase4/STaR_EVRP_RESULTS_HANDOFF.zip`.
