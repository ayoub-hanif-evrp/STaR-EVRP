# Standalone figure captions

## F01_primary_parent_effects
File: `figures/main/F01_primary_parent_effects.png`. Source: data/summary.json: paired, parent_effects.
Reliability difference in percentage points (STaR minus B4) on 2,321 initially charging-exposed CON routes at c64 (64-plan maximum). Circles show all 48 parent means (area scales with routes); the diamond shows the route-weighted estimate, with a 95% family-stratified parent-cluster percentile interval (9,999 draws, seed 312406). Only the pooled reliability contrast is confirmatory.

## F02_method_reliability_attainment
File: `figures/main/F02_method_reliability_attainment.png`. Source: data/summary.json: overall.
Seven methods paired on the same 2,321 exposed c64 routes. Mean empirical reliability uses 10,000 held-out draws per plan; attainment counts routes whose one-sided 95% Wilson lower limit is at least 0.95. Counts are not simultaneous guarantees.

## F03_paired_reliability_completion
File: `figures/main/F03_paired_reliability_completion.png`. Source: data/paired_routes.csv (c64).
Each panel represents 2,321 matched original c64 routes. Positive reliability (percentage points) and negative completion favor STaR. Dots are empirical route estimates, not confidence intervals; overlapping points remain possible. Matched original exposed routes, not independent point-cloud replicates. Completion is unconditional depot return, in native units.

## F04_scenario_work
File: `figures/main/F04_scenario_work.png`. Source: data/summary.json: budget, reliability_quality.
Matched quality and mean incremental search draws for 2,321 exposed routes per method/profile; vertical intervals are descriptive 95% family-stratified parent-cluster bootstrap intervals. No interpolated frontier. c64: 64 plans / 131,072 draws; c24: 24 / 131,072; s8192: 128 / 8,192; seed 2: c64 with another search seed. Draw savings do not imply elapsed savings.

## F05_wall_runtime
File: `figures/main/F05_wall_runtime.png`. Source: data/summary.json: budget, reliability_quality.
Matched quality and mean measured search wall time (ms) for 2,321 exposed routes per method/profile; vertical intervals are descriptive 95% family-stratified parent-cluster bootstrap intervals. No interpolated frontier. c64: 64 plans / 131,072 draws; c24: 24 / 131,072; s8192: 128 / 8,192; seed 2: c64 with another search seed. Elapsed time is measured under six workers, excludes final validation and includes search overhead; wall guard is cooperative.

## F06_family_variant_attainment
File: `figures/main/F06_family_variant_attainment.png`. Source: data/summary.json: family_variant.
Family × variant c64 attainment for B0, B3, B4, and STaR. Row labels give eligible routes, and cells give attained count (top) and rounded percent (bottom). A/B are sibling variants, not independent parents. One-sided Wilson rule, descriptive breakdown.

## F07_topology_and_ablation
File: `figures/main/F07_topology_and_ablation.png`. Source: data/summary.json: mechanism, paired.
(a) For the same 2,321 c64 route pairs, split by the exact ordered (customer gap, station ID) list. Weighted stratum contributions sum arithmetically to the primary point estimate but are post-selection, not independent causal effects. (b) Separate exploratory c64 no-partial ablation, with a pointwise 95% parent-cluster interval.

## F08_fixed_plan_robustness
File: `figures/main/F08_fixed_plan_robustness.png`. Source: data/summary.json: robustness.
Lower-bound attainment on 2,321 initially exposed routes per method under three separate synthetic waiting-model stresses. Plans are fixed at c64, validation uses 10,000 draws per plan/model. The Gaussian copula preserves the marginal distributions. The results are descriptive and are not calibration against real station data.

## S01_registered_R2_route
File: `figures/supplementary/S01_registered_R2_route.png`. Source: data/summary.json: case_routes; saved c64 plans and validation.
Preregistered example R2_10_2/A/route 0, the first eligible R2-A route by parent and ID. Markers are horizontally offset only to avoid overlap. The B4 and STaR completion curves coincide at this resolution. Exact stops, customer/depot timing, and charge amounts are supplied in the supplementary case table.

## S02_near_target_Wilson
File: `figures/supplementary/S02_near_target_Wilson.png`. Source: raw/c64 validation; coded subset ±1.5 pp.
Post-hoc diagnostic: c64 route estimates within ±1.5 percentage points of 0.95, using two-sided 95% Wilson intervals. These are not the one-sided lower bounds used for attainment.

## S03_actual_candidate_work
File: `figures/supplementary/S03_actual_candidate_work.png`. Source: raw/c64 search work; data/summary.json: work.
Post-hoc empirical CDFs of distinct candidate trials on 2,321 c64 routes per method. Deterministically rejected plans count toward trials. B4 restricts the neighborhood; this does not identify the best attainable quantity-only result.
