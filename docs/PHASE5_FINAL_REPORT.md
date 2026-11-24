# Phase 5 — Final experimental report

**Release status:** P5-G0 through P5-G6 pass. The package supports a narrow conference-paper claim: at the registered c64 maximum, STaR improved reliability over the implemented fixed-station partial-charging comparator, FSPC. The extension neither supersedes that confirmatory contrast nor creates a new untouched holdout.

## Coverage, audit and provenance

- All **120 instances (60 A/B parent pairs)** are represented, with **8,606** original customer-covering CON routes: **2,891 exposed** and **5,715 unchanged no-charge**. Development contributes 24 instances and 570 exposed routes; original holdout 96 instances and 2,321 exposed routes. All seven controls and three new ablations have the same c64 route denominators. The instance CSV has **1,200 instance-method rows**, with NA, not a fabricated value, when exposure is empty.
- Reused **16,247** original holdout c64 control records, added **3,990** development controls with 10,000-draw validation, and ran **8,673** new ablations. All **12,663** new plans reproduced final metrics on replay, including **63,315** scalar reference spot checks. The Phase 4 independent auditor again reconciled all 1,248 existing Phase 3 bundles. No holdout control was reoptimized.
- All-on reproduction matched the frozen optimizer's plan, search score, history and counters on **66** fixed development fixtures, including single/multi/no-station routes, observed duplicate hits, analytical rejects and prefix rejects. The three pre-execution component tests passed. The first replay command raised a reporting-only NameError after computing its development checks; the additive replay reporter revalidated the existing batches without rerunning optimization. A discovery-time historical manifest path was corrected before any production outcome.
- Producer base HEAD `4ab2e3297e4791e13f48ea1c88576438069af8ef`, with additive Phase 5 file hashes frozen before execution in `results/phase5/manifests/protocol.json`. Optimizer tag `star-phase3-freeze-v1` still points to `c657aa69d55178c85b4759475933b36d1bcc2181`. Result-commit identity is the GitHub commit containing this report; no self-referential SHA is embedded. Archived and new cohorts used six workers, Python 3.12.10 and single-thread BLAS/OMP on the recorded Windows 11 / Intel host. Identical nominal setup does not justify paired timing inference across runs.

## Results and caveats for the writer

| Main method | All-120 descriptive mean R | All-120 lower-bound attained | Holdout mean R | Holdout lower-bound attained |
|---|---:|---:|---:|---:|
| CON | 79.80% | 2,058/2,891 | 80.97% | 1,686/2,321 |
| MWR | 95.12% | 2,562/2,891 | 95.29% | 2,052/2,321 |
| QBR | 94.76% | 2,709/2,891 | 95.21% | 2,183/2,321 |
| STaR | 97.06% | 2,742/2,891 | 97.31% | 2,211/2,321 |

- **Mandatory confirmatory disclosure:** Holdout STaR–FSPC reliability **+1.24 percentage points** (95% family-stratified parent-cluster interval **0.86 to 1.65**); full completion was **33.15 native units shorter**, exploratory. STaR used 62.67 trials versus FSPC's 20.18 despite the same maximum: no equal-consumed-work or optimal quantity-only claim.
- **Mandatory competitive disclosure:** Holdout STaR–SLS **+0.32 pp**, exploratory; **34.59% fewer incremental search draws** but **29.69 vs. 27.51 ms** elapsed. No speedup. MWR's holdout mean completion is **2.01 native units shorter than STaR** despite lower estimated reliability; STaR and QBR completions are close. Do not imply dominance against either surrogate.
- **Ablations:** On the combined benchmark, full-minus-NPC is **+3.30 pp**, the largest observed quality effect. NSP's pooled difference is **+0.22 pp**, but on development the sign reverses (**−0.14 pp**) and the exploratory interval spans zero. NAS changes reliability by only about **+0.006 pp** on the pooled data, and full STaR uses about **546 fewer draws** per route. NPP yields identical recorded reliability, attainment and completion on all exposed routes; full STaR uses **5,772 fewer draws per route** on average. Neither result implies elapsed savings: development NPP's mean time was **21.85 ms** versus **20.54 ms** for full STaR in a separate execution; archived holdout full and new NPP wall times must not be treated as a common-run speed comparison.
- Lower-bound attainment is the individual one-sided 95% Wilson classification, not the point estimate or a fleet constraint. CON point-below-target and Wilson nonattainment are **826** and **833** on all120; holdout **628** and **635**. STaR still has **149** combined nonattainments, concentrated in R2/RC2. Four distinct station CSV contents were reused across both partitions; waits are synthetic and station hours disabled. Completion always includes late trajectories in native units. Post-selected topology strata are descriptive, not causal.

## Final exhibits and gates

| Gate | Status | Evidence |
|---|---|---|
| P5-G0 | PASS | Pre-execution protocol, exact frozen source and 66-case all-on equivalence |
| P5-G1 | PASS | 120 instances, 2,891 exposed routes, exact archived primary |
| P5-G2 | PASS | 8,673 component records; all new plans replayed and counters checked |
| P5-G3 | PASS | Partition-aware parent bootstrap, instance CSV, full FSPC/SLS disclosure |
| P5-G4 | PASS | 7 main + 8 supplementary 400-DPI PNGs; 20 three-format table bundles compiled in Tectonic |
| P5-G5 | PASS | 8 Phase 5 tests, 79 full-suite tests; 123 derived files reproduced byte-for-byte |
| P5-G6 | PASS | Writer ZIP, claim/number tables, captions, method glossary and source-linked audit |

Figures were visually inspected at the designated relative widths; draw tick density and supplementary stress design were corrected. Two initially overfull appendix tables were shortened and the full TeX compile passed. See `results/phase5/audit/final_gate.json` and `results/phase5/audit/visual.json`. No historical source or manuscript changed.
