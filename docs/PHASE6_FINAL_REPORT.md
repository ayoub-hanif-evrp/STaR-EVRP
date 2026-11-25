# Phase 6 final scientific report

**Decision.** Keep frozen STaR as the paper's method and use the Phase 6 results as an exploratory supplement. The clearest additions are the one-visit analytical result, the concentration of nonattainment on complex and tight source routes, and controlled evidence of simulation savings. The exploratory panels establish neither a runtime advantage nor a reliability advantage over a fixed-topology quantity oracle.

## Lineage and inference

The execution baseline is Phase 5 commit `bf6a4d86422350275a043c2424b7dd86d3b20b27`. The frozen optimizer is `c657aa69d55178c85b4759475933b36d1bcc2181` at `star-phase3-freeze-v1`. The containing release commit identifies this report. The prospective [manifest](../results/phase6/manifests/protocol.json) records code, data, configuration, exact panel IDs, timestamp and environment. The Phase 4 auditor reverified 1,248 Phase 3 bundles and exact primary reconciliation. Phase 5 checked 585 release hashes and 432 new raw/plan bundle hashes. The Phase 3 primary remains **STaR − FSPC +1.24 pp [0.86, 1.65]** across 2,321 routes and 48 holdout parents. Actual trial counts differed, 62.67 versus 20.18. Archived STaR − SLS was +0.32 pp, with 34.59% fewer draws and higher mean wall time, 29.69 versus 27.51 ms.

Every Phase 6 interval is exploratory, pointwise, conditional on sampled validation and clustered by parent. Combined analyses stratify by family and partition. Both panels deliberately sample by original visits and give panel-specific estimates. No new independent benchmark parents or charging environments were tested. Phase 5 remains the 120-instance source of truth, including 97.06% STaR reliability, 2,742/2,891 Wilson attainments and the four ablations. Preserve its surrogate and competitor trade-offs, synthetic station model, and timing cohort caveats.

## Charging complexity and route mechanisms

- Across 8,606 original routes, the counts for 0, 1, 2, 3 and at least 4 visits are **5,715, 1,959, 188, 239 and 505**. Originally single-visit routes are 22.76% of all routes and 67.76% of exposed routes. STaR selected one visit on **1,795/2,891 (62.09%)** exposed routes. Stripping stations was energy-feasible on zero originally exposed routes. The matched CON plans had 5,260 visits and 5,215 summed route-distinct stations. Selected STaR plans had 5,630 visits, 5,573 summed route-distinct stations, 205 zero quantities and 20 small positive quantities within the frozen no-duration threshold.
- STaR changed the ordered gap/station topology on 1,664 routes. It changed at least one quantity beyond NUM_TOL on 970 of the remaining 1,227 routes. Exactly 257 plans retained the same complete fingerprint. These are descriptions of the selected solutions with fixed customer order. The reported gap and station-ID sequence differences can overlap.
- All-route STaR–FSPC reliability directions were **208 gains, 2,546 ties, 137 losses**. Positive and negative contributions were **+1.524 and −0.139 pp** for net **+1.385 pp**. STaR–SLS gave **208, 2,522, 161** and **+0.742 and −0.511 pp** for net **+0.231 pp**. Omitting one parent at a time left FSPC means within 1.24–1.44 pp and SLS means within 0.18–0.32 pp. Equal success counts are ties on the observed tape. Completion directions, signed magnitudes and quantiles are in `data/paired_directions.csv`.
- STaR gained Wilson attainment on 67 routes and lost it on five versus FSPC, gained 34 and lost 17 versus SLS, gained 46 and lost 13 versus QBR, and gained 684 and lost zero versus CON. The transition CSV also records common attained and neither cells. The net count is the difference between gains and losses.
- STaR had 149 Wilson nonattainments. R2 contributed 97/542 and RC2 51/503. Among all 149, 143 were predominantly customer-only, two were joint and four had a point estimate at or above target. Twelve exposed routes had a two-sided Wilson interval containing the target. Source 3+ visits had 140/744 nonattainments versus 4/1,959 for one visit. The lowest source minimum-customer-slack quartile had 96/703 and the highest had 0/683. This is consistent with greater exposure and limited ability to absorb waits. The group comparisons do not identify causal mechanisms. They include differing route lengths, topology choices and source schedules.

[Route diagnostic report](PHASE6_DIAGNOSTIC_REPORT.md) · [F06-01 and F06-02](../results/phase6/figures) · [Per-route data](../results/phase6/data/route_features.csv)

## Mathematical and analytical checks

The [mathematical audit](PHASE6_MATHEMATICAL_AUDIT.md) proves a one-visit delay cap and lognormal reliability, an unconditional stop-loss completion mean, and weak dominance of the minimum feasible charge for a fixed single-visit topology. It distinguishes the true-reliability marginal screen from the optimistic prefix bound on the fixed finite tape. A positive-probability empirical counterexample demonstrates why the analytical screen does not preserve every sample score. A separate numerical test found a one-ulp customer-start issue when adding tolerance instead of reproducing the frozen subtraction. The Phase 6 code handles that cutoff. No frozen code was changed.

The 11 prereun mathematical tests passed. Independent forward/backward, dense trajectory and quadrature checks covered 226 CON/AS1 single-visit plans. The largest quadrature discrepancy was (3.12\times10^{-11}) native units. The frozen isolated cap exceeded the calculated one-visit cap by (1.76\times10^{-7}) to (4.21\times10^{-5}) native units. All 113 selected AS1 model probabilities were inside their new-tape two-sided Wilson intervals. On 106/113 AS1 plans, completion agreed within two simulation SEs or the 1e-8 roundoff allowance. The sample mean error in AS1 estimated reliability was −0.0033 pp on the new tape.

## AS1 restricted comparison

The eligibility gate passed with 1,959/2,891 originally single-visit exposed and 372 development routes. The fixed panel contained **113 routes from 59 parents** (21 development, 92 holdout). All enumerations completed. AS1 considered 714,731 zero/one-visit candidates, with 611,084 energy rejections, 75,131 timing rejections and 28,516 scored candidates. Its score uses analytical model quantities. Both tapes used the same saved plans. All selected AS1 plans used one visit.

On the new validation tape, **AS1 − STaR was −0.018 pp [−0.059, 0.022]** and **−14.04 [−23.71, −6.11] native completion units**. AS1 and STaR each attained on 111/113 routes. AS1 − SLS was −0.304 pp [−1.055, 0.120] and −9.31 native completion units. The reliability intervals support no improvement claim. AS1 enumeration median was 22.86 ms and maximum 551.76 ms, recorded separately from validation and without a paired speed comparison to archived methods. AS1 remains a supplementary restricted optimizer. The optional hybrid was excluded before outcomes.

## Stronger fixed-topology comparator

The panel contains **118 routes from all 60 parents** (23 development, 95 holdout), with 96 one-visit and 22 multi-visit source routes. Retain 96 one-visit oracle classifications, five complete linear-model MILP certificates, one completion-only classification and 16 uncertified multi-visit cases. After audit, one run label was downgraded because the tie-stage incumbent failed the independent replay. All 118 final plans were valid. Fifteen of the 16 uncertified cases used CON/FSPC, and the other retained a valid optimization-tape incumbent that scored 486/512 against a solver indicator count of 487. No route exceeded 30 seconds. The preserved solver records show that formal solver success often did not survive exact replay close to the hard timing or energy thresholds. The independent replay rules control the label, and no extra solver runs were added after seeing the panel.

On this fixed panel, **FT-SAA − FSPC was +0.041 pp [0.000, 0.124]**. STaR − FSPC was −0.343 pp [−1.059, 0.050], and **STaR − FT-SAA was −0.384 pp [−1.183, 0.050]**. STaR reduced complete return by **44.45 [34.04, 55.67]** native units versus FT-SAA. Three methods attained on 116/118 routes. A different pressure on station topology, sample objective, and compute budget means these differences do not identify the causal contribution of topology. The panel cannot establish a reliability advantage over optimal fixed-topology quantity allocation, and its baseline contrast differs from the archived full holdout. The handoff includes all-panel and certified-subset results.

## Controlled runtime comparison

Frozen STaR and SLS ran serially on the 118-route panel, with three repeats per guard and method, common seeds, fixed randomized order and separate development warm-up. Windows, Python and the library versions are recorded. Process affinity and instantaneous machine load were unavailable in the recorded environment. The 50 ms primary result was **−0.13 pp [−0.51, 0.09]** for STaR − SLS and **+0.23 ms [−1.02, 1.46]** for the mean paired difference in route median wall time. STaR used **15,004 fewer draws per route** on average (44.52% relative to SLS). Median route-median wall time was 24.78 vs 27.39 ms, a different statistic from the paired mean. The cooperative guard was exceeded in 122/354 STaR repeats and 117/354 SLS repeats, by up to 22.18 and 19.96 ms. All repeats returned an incumbent and no logged trial or scenario cap bound. Results at 20 and 100 ms also show fewer STaR draws and reliability intervals spanning zero. No speedup is established. No new prefix-only run was scheduled. The frozen Phase 3 s8192 profile reported STaR − SLS +0.39 pp [0.07, 0.70] as historical exploratory context.

## Release audit

| Gate | Status | Evidence |
| --- | --- | --- |
| P6-G0 | PASS | Prospective protocol, signed panel hashes, original Phase 3 and Phase 5 reconciliation |
| P6-G1 | PASS | All 120 cases, route features, paired directions, transitions and parent influence |
| P6-G2 | PASS | Proofs, synthetic math tests and 226 real one-visit reference checks |
| P6-G3 | PASS | AS1 opened and completed 113 routes. Hybrid skipped prospectively |
| P6-G4 | PASS | All 118 attempted and validated. Limited multi-visit solver certification disclosed |
| P6-G5 | PASS | 2,124 measured runs, including 50 ms primary and 20/100 ms sensitivity |
| P6-G6 | PASS | All 3,279 rows, 1,113 distinct within-stage plan checks and 11,130 scalar checks. Five 400-DPI PNGs, five table bundles, full-suite tests and byte-identical clean derived rebuild |
| P6-G7 | PASS | Protected input checks, conservative workspace cleanup and current repository navigation |

The result arrays and replay are in `results/phase6/data` and `audit`. All visual files were checked at native size and 675 pixels wide. All five LaTeX exhibits compiled without overfull or missing-character warnings at 178 mm. The [cleanup report](PHASE6_REPOSITORY_CLEANUP.md) lists exact removals and byte counts. Use the [handoff](PHASE6_RESULTS_HANDOFF.md) for the exhibit index, allowed claims and release archive. The Phase 6 work does not test literature priority, establish a fleet-level guarantee, or extend the original registered claim.
