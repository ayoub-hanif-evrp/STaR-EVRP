# Figure captions

## Fig01_spatial_charging_repair

Outcome-selected holdout example C1_10_3/A, route 106. STaR removed station 1253 after the last customer and inserted a visit to 1248 before the first. Observed reliability uses 3,063 and 10,000 successes on the same 10,000-scenario archived validation tape. The observed 100% is an empirical estimate. Maps share equal scale and matched detail bounds. Both plans serve the same customers in order. The battery profiles follow each plan’s own distance from the depot. Horizontal references mark zero and nominal capacity, vertical steps show charging, and numbered circles identify customers. Mean full return includes late scenarios. See the physical ledger for the change in travel, charging and readiness waits. Units are native.

## Fig02_star_framework

Frozen Slack-Targeted Stochastic Charging Repair (STaR). The initial plan is scored on a shared 512-draw search tape. Visit priority follows the marginal isolated-wait reliability bound and gaps near the most critical visit come first. Proposals interleave quantity and topology moves. Duplicates are skipped. A newly admitted plan counts as a trial even when its deterministic check fails. The analytical screen is active only for an empirically attaining incumbent. It bounds true fixed-plan reliability, which the finite-tape estimate may exceed. The 128-draw prefix bound uses the same tape, and survivors extend to 512. The score prefers attainment. At or above target, minimize full return then maximize reliability. Below target, maximize reliability then minimize full return. A strict gain updates and restarts. Exhaustion or a guard returns the incumbent for independent validation without search feedback. Operator sketches are conceptual. New topologies use minimal and, where applicable, downstream-rate-based allocations. Letters identify stations and numbers identify customers.

## Fig03_paired_reliability

Paired reliability on 2,321 exposed holdout routes from 48 parents. Panel (a) shows route-weighted contrasts in percentage points (pp) with pointwise 95% family-stratified parent-cluster bootstrap intervals (9,999 resamples with A/B siblings and routes kept together). Fixed-station repair is confirmatory and scenario search is exploratory. The common 64-candidate maximum yielded 62.67 versus 20.18 mean trials. Panel (b) counts observed directions versus fixed-station repair. Equal denotes matching successes out of 10,000 and does not identify equal true probabilities.

## Fig04_charging_complexity

Holdout routes grouped by original charging visits. Panel (a) shows STaR minus fixed-station repair in percentage points with exploratory pointwise 95% parent-cluster intervals. The one-visit lower endpoint is slightly negative. Panel (b) shows counts and shares failing the individual reliability target criterion, a one-sided 95% Wilson lower bound of at least 0.95. Routes with 3+ visits account for 102 of 110 remaining nonattainments and 89.0% of the net signed gain. Parents may span bins. These associations are descriptive.

## Fig05_quality_simulation_effort

Separate exploratory timing panel of 118 routes from 60 parents (23 development, 95 holdout). Each 20, 50 or 100 ms cooperative runtime guard used three serial repeats per method and route (2,124 runs). Panel (a) shows route-mean independent validation reliability and incremental search draws. Panel (b) shows paired reliability differences with pointwise 95% family-by-partition parent intervals after averaging repeats. At 50 ms, STaR used about 18,696 draws versus 33,699 for scenario search (44.52% fewer). The paired differences were −0.134 pp [−0.510, +0.087] for reliability and +0.233 ms [−1.018, +1.461] for route-median elapsed time. STaR exceeded the guard on 122/354 repeats and scenario search on 117/354. Both intervals include zero. The panel does not establish wall-time superiority or equivalence.

## Sup01_complex_route_repair

Outcome-selected exploratory case RC2_10_3/B, route 15. The rule chose the lower-median customer count among 149 improving R2/RC2 holdout routes with changed topology and target attainment. Maps share equal aspect and identical bounds. S1, S2 and subsequent labels identify charging events in order on each plan. SUPPLEMENTARY_NOTES.md gives all station IDs, charge quantities and rates. Battery profiles use independently accumulated Euclidean distance on common physical scales. Full return is unconditional. This example illustrates a saved repair.

## Sup02_deteriorated_route_diagnostic

Outcome-selected adverse case RC2_10_9/B, route 14. This pair had the largest observed STaR loss versus fixed-station repair on the archived holdout tape. Panel (a) shows paired differences in deterministic customer service-start slack with zero station waits. Panel (b) reports archived stochastic validation. Customer order matches. A smaller slack at a visit can indicate sensitivity to delays. The archive does not identify a causal search mechanism or a stochastic trajectory.
