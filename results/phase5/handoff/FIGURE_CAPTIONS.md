# Figure captions

## F01_benchmark_coverage
All 120 class/variant problems, with 96 holdout and 24 development. Labels are exposed/all original CON routes; only initially station-exposed routes enter the repair comparisons.

## F02_main_methods_reliability_attainment
Identical c64 rule; 2,321 initially exposed holdout routes; 2,891 all-120 exposed routes including 24 development instances (descriptive). Mean success and individual one-sided Wilson lower-bound attainment are distinct. SLS and FSPC were also tested; see the supplementary evidence and mandatory registered primary disclosure.

## F03_main_methods_completion_and_repair
Left: unconditional full depot return on every initially exposed c64 route. Right: lower-bound attainment among routes with CON estimated reliability below 0.95; counts shown over that subset, not over all exposed routes. Both panels are descriptive; paired deteriorations are in the supplementary table.

## F04_ablation_quality
Exploratory paired differences at c64; positive favors full STaR. Bars denote 95% family-stratified parent-cluster percentile intervals, split by partition for the pooled panel. Unadjusted pointwise intervals; not simultaneous.

## F05_ablation_work_and_runtime
Per-route c64 means with six workers. Holdout full/NPC elapsed times are archived Phase 3, whereas NSP/NAS/NPP are Phase 5. Development full/NPC and new ablations were measured in separate runs. No paired elapsed inference across the archive/new boundary; CPU and consumed plans are tabulated separately. Draw counts are not elapsed time.

## F06_family_variant_attainment
All 120 instances including development (descriptive). Family A/B row labels give exposed denominators, cells give attained counts and rounded percentages. Holdout-only strata are available in the family table. R2 and RC2 remain challenging.

## F07_stress_robustness
Archived holdout c64 fixed-plan stresses on 2,321 exposed routes per shown method. Each stress changes one synthetic assumption; copula preserves marginals. No reoptimization, real queue calibration, or extrapolation to new station tables.

## S07_full_robustness
Four archived holdout c64 methods. Change in lower-bound attainment versus the same method's original model, in percentage points, on 2,321 exposed routes per method. Synthetic stress on fixed selected plans, no reoptimization.

## S01_registered_primary_contrast
Sole confirmatory result. Route-weighted reliability on 2,321 original holdout route pairs; interval is the archived 95% family-stratified parent cluster bootstrap. Circles are 48 descriptive parent means. Equal cap does not mean equal actual work. Disclose this result in the main text.

## S02_competitive_quality_work
Archived 96 holdout instances, exploratory intervals for quality only. Distinct profiles, not a continuous frontier. Profiles (plan cap/draw cap): c64 64/131,072; c24 24/131,072; s8192 128/8,192; c64 seed 2 repeats c64 with a second optimizer seed. Lower search draws at c64 did not make STaR faster than SLS.

## S03_competitive_runtime
Archived 96 holdout instances, exploratory intervals for quality only. Distinct profiles, not a continuous frontier. Profiles (plan cap/draw cap): c64 64/131,072; c24 24/131,072; s8192 128/8,192; c64 seed 2 repeats c64 with a second optimizer seed. Lower search draws at c64 did not make STaR faster than SLS.

## S04_topology_and_partial
Archived holdout c64. Left: post-selected ordered station-gap strata, descriptive contributions that sum to the pooled difference, not causal effects. Right: separate no-partial ablation and exploratory 95% parent-cluster interval.

## S05_failure_uncertainty
Holdout c64 nonattainment classified by predominant scenario failure mode, with point-only routes shown separately (point estimate ≥0.95, one-sided Wilson lower bound below 0.95). Route categories are not scenario frequencies.

## S06_registered_route
Registered first eligible R2-A route. Exact charging events are in the supplementary CSV; markers are offset for visibility. FSPC and STaR have overlapping completion quantiles; the case is not selected to favor STaR.

## S08_actual_candidate_trials
Archived c64 route ECDF. All methods share a maximum of 64 unique plan trials, but FSPC's fixed-station quantity neighborhood often ends early; unhit caps are evidence consistent with exhaustion, not explicit runtime termination labels.
