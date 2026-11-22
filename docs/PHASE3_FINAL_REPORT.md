# Phase 3 final scientific report

**Narrow result.** The holdout supports incremental topology benefit over B4 but not a claim of general superiority over B3.

Frozen executable: `c657aa69d55178c85b4759475933b36d1bcc2181` (`star-phase3-freeze-v1`). This was one preregistered holdout
run following the original train/test split; no method, configuration, or analysis changes were made after performance access.
Secondary intervals are exploratory and pointwise, not simultaneous.

## Held-out results

The frozen test included **48 parents / 96 variants**, **6,864 CON routes**,
**2,321 charging-exposed routes**, **4,543 no-charge routes**, and **628 exposed
B0 routes below the empirical 0.95 target**. All exposed routes were paired for the primary comparison.

| Method | Mean reliability | Attained / exposed | Full completion (native) | Mean draws | Wall ms |
|---|---:|---:|---:|---:|---:|
| B0 | 80.97% | 1,686/2,321 | 3,391.25 | 0 | 0.22 |
| B1 | 95.29% | 2,052/2,321 | 3,133.83 | 0 | 27.39 |
| B2 | 95.21% | 2,183/2,321 | 3,135.71 | 0 | 27.45 |
| B3 | 97.00% | 2,193/2,321 | 3,137.43 | 19,911 | 27.51 |
| B4 | 96.07% | 2,161/2,321 | 3,168.98 | 4,257 | 8.38 |
| STaR | 97.31% | 2,211/2,321 | 3,135.83 | 13,024 | 29.69 |
| STaR_no_partial | 94.19% | 2,096/2,321 | 3,230.53 | 8,400 | 27.41 |

STaR minus B4 (primary) was **+1.24 [+0.86, +1.65] percentage points** (estimate [95% cluster interval]).
Parent-balanced sensitivity: **+1.12 pp**
[+0.79, +1.47].
Completion difference: **-33.15 [-34.86, -31.48]** native units; on the **2,158** common attaining routes:
**-35.56 [-37.45, -33.70]**. Attainment difference: **+2.15 [+1.49, +2.90] pp**.

STaR minus B3 reliability: **+0.32 [+0.13, +0.49] pp**; 13,024 vs 19,911 search draws; 29.69 vs 27.51 ms wall; 2,211 vs 2,193 attained; 3,135.83 vs 3,137.43 time units.
The paired elapsed difference was **+2.18 [+1.63, +2.73] ms**. Counts measure incremental simulation work, not elapsed efficiency.
At the 8,192-scenario budget the reliability difference versus B3 was **+0.39 [+0.07, +0.70] pp**.
The second search seed yielded **+1.25 [+0.87, +1.65] pp** versus B4.
Removing partial charging changed reliability by **+3.12 [+2.22, +3.97] pp** (STaR minus ablation).
Observed stratum contributions to the primary effect: same_topology: -0.08 pp, topology_changed: +1.32 pp. These are associations from the saved routes,
not attribution to a single edit independent of the accompanying charge allocation.

STaR nonattainment (nonattained/exposed): C1-A: 0/67; C1-B: 0/19; C2-A: 1/188; C2-B: 0/142; R1-A: 0/328; R1-B: 0/368; R2-A: 48/237; R2-B: 18/191; RC1-A: 0/216; RC1-B: 0/163; RC2-A: 22/226; RC2-B: 21/176. Negative cases include customer misses,
depot misses, joint losses, and point-positive routes whose lower limits do not clear the target.
The fixed R2-A case is **R2_10_2/A/0**, chosen without outcome information.

Fixed-plan synthetic robustness for STaR, without reoptimization:
- scale125: 96.00% reliability, 2,112/2,321 attained.
- sigma125: 97.00% reliability, 2,150/2,321 attained.
- copula035: 97.32% reliability, 2,201/2,321 attained.

## Integrity and deliverables

- P3-G0: preflight passed, including 62 tests and source/producer reconciliation.
- P3-G1: tagged code, protocol, split and file hashes checked before execution; separate post-tag development smoke passed.
- P3-G2: all 96 holdout instances and all exposed routes accounted for under every declared profile.
- P3-G3: 37,136 selected plans independently reconstructed and validated at 10,000
  draws per plan/model, with 5 reference-simulator checks per plan/model.
- P3-G4: sole confirmatory contrast STaR–B4, paired parent clustering; B3 quality, wall and draw costs separately reported.
- P3-G5: 10 audited 400-DPI PNGs and 11 CSV/LaTeX/Markdown table families.
- P3-G6: 1,248 hashed compressed batches and report/artifact lineage matched the freeze;
  replay ran in 36.6 seconds.

See `docs/PHASE3_REPRODUCIBILITY.md`, `docs/PHASE3_FIGURE_INDEX.md`, and
`docs/PHASE3_MANUSCRIPT_DRAFT.md`. The 40-ms development diagnostic was not repeated, as preregistered.
Timing reflects six-worker execution with possible contention. The synthetic station model and fixed CON customer
orders limit external applicability; do not infer a universal queue policy or global EVRPTW improvement.

## Execution notes

The first invocation hit a Windows multiprocessing permission error before a worker scored any route.
The same command then ran with process-pipe permission, without changing the freeze or discarding outcomes.
All declared profiles and robustness evaluations completed. The 5-second cooperative guard had zero measured overruns.
The 40-ms historical diagnostic was excluded in advance, as recorded in the frozen analysis plan.

The Phase 2.5 producer commit is `3532fbe5f7f2b531a445baa82c843d164f57d6c5`. The pre-outcome
freeze evidence is public at `44b136a`, separately from the executable tag and the outcomes. Historical datasets
and Phase 1/2/2.5 result trees were preserved.

The GitHub package stores the 96 baseline bundles in `results/phase3/con_bundles.zip` because
Git on Windows cannot stage the `raw/con` path directly. Extraction restores the exact audited files.
