# STaR-EVRP Phase 2.5 final report

**Decision: CONDITIONAL GO.** Charging topology edits add value beyond strong fixed-station partial charging. STaR is competitive with genuine scenario local search and uses fewer optimization replications, but the experiment does not establish a general reliability or wall-clock advantage over B3. The 96 benchmark holdout instances were not simulated or used for development. Phase 3 was not started.

## Scope and principal results

The corrected experiment used all 570 charging-exposed routes among 1,742 routes in 24 development instances from 12 Homberger parents. Every method shared the original deposited-CON routes, customer assignments and order, native Euclidean time/energy, battery capacity 700, hard customer/depot deadlines, independent synthetic lognormal visit waits, and an independent 4,096-draw validation stream. The original 127 routes are flagged in the new data; the principal results do not select for performance on that panel. Zero-station routes are pass-through routes, not repairs.

| Method | Mean validation reliability | Attained / 570 | Mean full completion | Mean search ms | Mean search draws |
|---|---:|---:|---:|---:|---:|
| B0 | 75.07% | 372 | 3,556.96 | 0.18 | 0 |
| B1 mean | 94.40% | 508 | 3,302.77 | 20.26 | 0 |
| B2 quantile | 92.90% | 526 | 3,302.95 | 19.63 | 0 |
| B3 scenario LS | 96.13% | 531 | 3,305.30 | 20.15 | 20,020 |
| B4 quantities only | 94.05% | 517 | 3,336.26 | 6.55 | 4,549 |
| STaR | 96.02% | 530 | 3,303.05 | 22.17 | 13,275 |
| STaR without partial charge | 91.98% | 497 | 3,383.82 | 19.96 | 8,489 |

Primary profile: 64 distinct candidate trials per route. Attainment uses a one-sided 95% Wilson lower bound of at least 0.95. Completion is unconditional over validation scenarios, including late routes; units are benchmark time. Values come from `results/phase25/tables/main.csv`.

- **Against B4:** STaR gains **1.97 percentage points** in paired reliability (parent-bootstrap 95% interval 0.44 to 3.88), attains on 13 additional routes net, and reduces mean completion by **33.21** time units (interval 29.33 to 36.82 lower). On the 514 routes attained by both, its mean completion is 37.10 units lower. B4 is materially faster; topology edits buy quality, not speed, relative to B4.
- **Against B3:** At 64 plans STaR uses about **34% fewer draws** but is about **10% slower**. The reliability difference is −0.12 pp (interval −1.25 to +0.60), and the attainment count is 530 versus 531. At the shared 8,192-draw cap, STaR gains 1.21 pp in reliability, attains 534 versus 528, and reduces mean completion by 7.67 units, but takes 18.39 versus 10.71 ms. The attained-count difference is uncertain. At the cooperative 40 ms limit both methods remain close (537 versus 535 attained). This is evidence of a **scenario-budget trade-off**, not a replication of the historical speedup.
- **Stress cases:** All 40 STaR nonattainments at the primary budget are in R2 (31) and RC2 (9). CON averages 3.75 and 2.97 station visits respectively, versus about one elsewhere; 109/114 R2 and 84/101 RC2 routes visit multiple stations. Multiple waits accumulate; restoring timing requires redistributing charges across segments or altering station locations. These are observed associations and model mechanisms, not a proof of irreparability. STaR restored 35/66 empirically below-target R2 routes and 29/38 RC2 routes. For example, R2_10_1 A route 0 went from 1.68% to 75.66% yet did not attain.
- **Partial charging:** Removing partial charging reduced attainment from 530 to 497 and mean reliability by 4.03 pp. The same-sequence B4 example RC1_10_1 A route 98 kept station 1085 but cut energy from 517.17 to 35.66, charging duration from 402.24 to 27.74, and mean full completion from 1,834.83 to 1,460.32; empirical reliability rose from 0 to 1 at the sampled resolution. This illustrates earlier downstream departures, not real-world reliability.
- **Historical D1:** All 127 corrected rows replayed with the legacy wait stream. Reliability matched the history, while 46 full completions increased relative to Phase 1 (maximum increase 4,534.27). The previous equal-runtime-budget speed claim, exact completion-equivalence statement and i.i.d.-route inference are unsupported and must not carry into the paper.

## Reproduction and artifacts

Run from the repository root with Python 3.12.10. The run manifest records the actual checkout base, source and input hashes, split, parameters, packages, seeds and environment. Use a separate output tree for a fresh run; resuming an existing tree checks the manifest, per-batch digest and exact key coverage. An exact source snapshot is identified by hashes in addition to the base commit; the commit alone is not the corrected version.

```powershell
python -m pip install -e .
python -m pip install numpy==2.5.3 scipy==1.18.1 PyYAML==6.0.3 matplotlib==3.11.2
python -B -m pytest -p no:cacheprovider -q
$env:OPENBLAS_NUM_THREADS='1'
python -B scripts/run_phase25.py --output results/phase25_reproduction
python -B scripts/run_phase25.py --output results/phase25_reproduction --verify
python -B scripts/verify_phase25_search.py --output results/phase25_reproduction
python -B scripts/analyze_phase25.py --output results/phase25_reproduction
```

- `results/phase25/raw/`: 96 instance/profile batches and 15,960 selected plans. Every saved plan passed reconstructed deterministic validation and independent 4,096-scenario replay; three scenarios per plan also matched the scalar reference. All 11,970 count-budget searches reproduced their selected plans, scores and work counters. The wall profile intentionally makes no bit-for-bit search claim. The full test suite passed (58 tests).
- `results/phase25/tables/`: reproducible CSV and LaTeX main, parent-paired, family/variant, stress, repairability, history-panel, overhead and example tables, plus route-level source data. LaTeX outputs using `longtable` require that package.
- `results/phase25/figures/`: ten data-backed 400 DPI PNGs covering validation, equal budgets, paired B4 comparison, runtime and scenario cost, successful/unsuccessful completion, the partial ablation, family stress, measured overhead and charging mechanism. The original Phase 2 placeholder files are preserved, not overwritten.

## Limits and Phase 3

The 40 ms profile uses an admission/selection cutoff, not OS pre-emption. An in-flight operation or scheduling delay can overrun; the worst observed search elapsed time was 61.8 ms across methods. Do not present this as a strict process deadline. The hard candidate and scenario caps did not overrun. These are development data under one optimization-seed regime and a synthetic, independent waiting model; twelve parent clusters yield exploratory intervals. Charge plans are offline, not adaptive or fleet-coupled, and the heuristics do not claim global optimality. Confirmatory work should follow `docs/PHASE3_FREEZE_PROTOCOL.md`, subject to a separate instruction.
