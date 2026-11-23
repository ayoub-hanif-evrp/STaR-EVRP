# Table notes

Use \input with booktabs, graphicx and, where needed, longtable. Small fragments resize to the current linewidth. For two-column manuscripts place longtable supplementary fragments in a one-column appendix. CSV, TeX and Markdown are derived from the same display cells. The JSON and paired CSV preserve full precision.

LB = one-sided 95% Wilson lower limit at least 0.95; R = empirical validation reliability; pp = percentage points; MC = incremental search Monte Carlo. Conditional completion compares only joint LB-attainers.

## T01_population
File: `tables/main/T01_population.tex`. Source: data/summary.json: population, station_tables.
The same held-out parents contribute both variants. Initially exposed routes form the main denominator; point-estimate failure and lower-bound nonattainment are different.

## T02_primary_methods
File: `tables/main/T02_primary_methods.tex`. Source: data/summary.json: overall.
Matched c64 methods. R and attainment: higher is better; full completion, elapsed time and work are distinct; completion uses native time units. Zero optimizer MC draws do not imply zero work. Validation is excluded from search time/draw counts.

## T03_paired_contrasts
File: `tables/main/T03_paired_contrasts.tex`. Source: data/summary.json: paired.
Signed STaR minus control; positive favors reliability, negative favors time/work. Family-stratified parent-cluster intervals; only STaR–B4 c64 reliability is confirmatory.

## T04_frozen_budgets
File: `tables/main/T04_frozen_budgets.tex`. Source: data/summary.json: budget.
Secondary frozen profiles are discrete comparisons, not a monotone sweep. Seed 2 reuses the benchmark parents. Five-second wall guard is cooperative; archived elapsed and CPU times reflect six workers.

## T05_family_attainment
File: `tables/main/T05_family_attainment.tex`. Source: data/summary.json: family_variant, population.
Family and A/B strata, with different route counts. LB = one-sided lower-bound attainment; all strata are descriptive.

## T06_mechanism
File: `tables/main/T06_mechanism.tex`. Source: data/summary.json: mechanism, paired.
Topology strata compare STaR with B4; the ablation compares a different method. Saved-plan topology strata are descriptive and post-selection, not separate interventions.

## T07_robustness
File: `tables/main/T07_robustness.tex`. Source: data/summary.json: robustness.
Synthetic fixed-plan robustness; no reoptimization. Scale125 multiplies all waits; sigma125 multiplies log-scale spread; copula035 changes dependence with preserved marginals.

## S01_primary_estimands
File: `tables/supplementary/S01_primary_estimands.tex`. Source: data/summary.json: paired.
Exact primary estimand and parent-equal sensitivity; family-stratified parent-cluster percentile interval. Only the route-weighted effect is confirmatory.

## S02_parent_effects
File: `tables/supplementary/S02_parent_effects.tex`. Source: data/summary.json: parent_effects.
Each parent mean pools A/B routes; these descriptive points are not independently tested effects.

## S03_family_variant
File: `tables/supplementary/S03_family_variant.tex`. Source: data/summary.json: family_variant.
Full family/variant method counts; the two-sided straddle category can overlap both attainment categories.

## S04_candidate_work
File: `tables/supplementary/S04_candidate_work.tex`. Source: data/summary.json: work.
One trial counts the initial plan; generated proposals and cache hits are not additional trials. At c64, no-limit stops are consistent with exhaustion of the implemented neighborhood; no explicit stop reason was stored. Equal caps, unequal consumed trials. B4 adjusts quantities only and is not a quantity oracle.

## S05_runtime_accounting
File: `tables/supplementary/S05_runtime_accounting.tex`. Source: data/summary.json: budget.
Mean archived work per route. Score includes deterministic surrogate evaluation for B1/B2; component timers need not sum to total elapsed. Five-second wall guard is cooperative; archived elapsed and CPU times reflect six workers.

## S06_nonattainment
File: `tables/supplementary/S06_nonattainment.tex`. Source: data/summary.json: failures.
STaR route classifications. Point-only indicates estimate at least 0.95 but Wilson nonattainment. Other nonattainments use the most common observed failure mode per route; scenario-count ties follow customer, depot, joint order.

## S07_uncertainty_ties
File: `tables/supplementary/S07_uncertainty_ties.tex`. Source: data/summary.json: overall.
One-sided lower bounds do not give a joint guarantee. Two-sided 95% straddle counts are a separate, nonpartitioning statistic.

## S08_paired_directions
File: `tables/supplementary/S08_paired_directions.tex`. Source: data/summary.json: ties.
Post-hoc directions of observed estimates, not statements about individual true superiority. Reliability ties mean equal successes out of 10,000; completion ties are absolute difference at most 1e-8 native time units.

## S09_common_and_work
File: `tables/supplementary/S09_common_and_work.tex`. Source: data/summary.json: paired.
Exploratory pair contrasts. Route-relative completion uses positive comparator completion per route; common attainment conditions on both selected plans.

## S10_negative_examples
File: `tables/supplementary/S10_negative_examples.tex`. Source: data/summary.json: negative.
Post-hoc examples: lexicographically first nonattaining route per observed mode. Counts are overlapping scenario failures over 10,000 draws, not additional routes.

## S11_registered_route_stops
File: `tables/supplementary/S11_registered_route_stops.tex`. Source: data/summary.json: case_routes.
Registered R2_10_2/A/0: station and depot event rows in saved stop order. Zero-wait time and energy are native units; station deadlines shown but not enforced. The full exact event list is in data/registered_route_events.csv.

## S12_station_content
File: `tables/supplementary/S12_station_content.tex`. Source: data/summary.json: station_tables.
Byte-identical station-attribute CSVs grouped by full SHA-256. This is not a holdout of unseen station attribute tables.

## S13_reproduction
File: `tables/supplementary/S13_reproduction.tex`. Source: results/phase3/manifests/freeze.json.
Producer environment, not a new Phase 4 benchmark run.

## S14_methods
File: `tables/supplementary/S14_methods.tex`. Source: src/star_evrp/competitive_search.py: frozen optimizer.
Reviewer-facing method truth table. B2 uses independent lognormal visit quantiles, not medians. Equal caps, unequal consumed trials. B4 adjusts quantities only and is not a quantity oracle. Zero optimizer MC draws do not imply zero work. Validation is excluded from search time/draw counts.

## S15_stop_limits
File: `tables/supplementary/S15_stop_limits.tex`. Source: data/summary.json: work.
Recorded-counter categories, not archived termination labels. In s8192 a residual scenario budget can be too small for a full extension even below the exact cap; therefore only c64 supports the narrower neighborhood-exhaustion inference.
