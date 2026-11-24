# Table notes

Use booktabs, graphicx and longtable. Long tables belong in a one-column appendix. R = mean estimated reliability; LB = route achieves one-sided 95% Wilson lower limit >=0.95. Point estimates and target straddling from two-sided Wilson intervals are separate. All completion data are unconditional full depot-return (native units); NA means no eligible routes or pooled timing intentionally omitted.

## T01_population
Coverage of all 120 original fleets. No-charge routes remain unchanged and outside repair estimates. Point-below-target and Wilson nonattainment are distinct.

## T02_main_methods
Main presentation methods only; SLS and FSPC also tested. T07 is mandatory disclosure. R and LB higher is better; completion is full depot return, native time units, lower is better. No pooled wall statistics. Archived Phase 3 and new Phase 5 runtime cohorts are separate. The 5-second guard is cooperative. No speedup is inferred from draw counts.

## T03_main_paired_effects
STaR minus control; unadjusted exploratory parent-cluster 95% intervals. Positive favors reliability and attainment; negative favors completion.

## T04_ablation_quality
One component disabled at a time (NPC combines removal of amount changes with full allocation on new topology moves). All ablation effects exploratory. Native full completion.

## T05_ablation_work
Per-route means. Holdout STaR/NPC come from Phase 3; other times are newly measured; development controls and ablations used separate runs. NAS screen rejections are zero but it still computes priorities. NPP full-batch search has no prefix pruning. Archived Phase 3 and new Phase 5 runtime cohorts are separate. The 5-second guard is cooperative. No speedup is inferred from draw counts.

## T06_family_results
Attaining counts in distinct family and variant cells; originally exposed routes only. All 120 includes development; descriptive.

## T07_primary_evidence
Mandatory main-text disclosure, even when full SLS and FSPC exhibits are supplementary. 95% parent-cluster intervals. A shared maximum of 64 unique plans does not imply equal consumed work; FSPC is a restricted heuristic, not a quantity-only optimum. Archived Phase 3 and new Phase 5 runtime cohorts are separate. The 5-second guard is cooperative. No speedup is inferred from draw counts.

## S01_complete_benchmark
All ten methods under c64. Combined timing not reported. All comparisons except the archived STaR–FSPC holdout reliability contrast are exploratory or descriptive.

## S02_all_instances
One row per source instance, including empty exposure. NA is not zero. The long-format instance CSV covers all ten methods, with counters, uncertainty, time, and runtime cohort.

## S03_archived_profiles
Original holdout profiles only. Different caps are not a single monotone sweep. Seed 2 reuses the same parents. Profiles (plan cap/draw cap): c64 64/131,072; c24 24/131,072; s8192 128/8,192; c64 seed 2 repeats c64 with a second optimizer seed.

## S04_component_paired
Full STaR minus ablation; unadjusted parent-cluster intervals, all exploratory. Additional paired plans/CPU/elapsed are in paired_effects.csv when comparable.

## S05_work_distributions
Archived consumed trials and counter-derived limits. Under c64, unhit limits are consistent with neighborhood exhaustion; they are not explicit termination labels. Under scenario caps an affordable remainder can be too small for the next batch. A shared maximum of 64 unique plans does not imply equal consumed work; FSPC is a restricted heuristic, not a quantity-only optimum.

## S06_failures
Predominant route-level failure classifications. Point-only: estimate >=0.95 but one-sided lower bound <0.95. The failure-mode data CSV also gives individual scenario counts and two-sided target straddling.

## S07_robustness
Original saved holdout fixed-plan synthetic stresses only, no reoptimization.

## S08_topology
Observed ordered station-gap strata from STaR and FSPC selected plans. Post-selection contributions are additive arithmetically, not causal. Native time and energy units.

## S09_registered_route
Registered first eligible R2-A route; exact customer rows are retained in data/registered_route_events.csv. Station deadlines were not enforced. FSPC/STaR overlap is real.

## S10_directions
Observed STaR direction over complete pairs; identical success counts tie, completion tolerance 1e-8. Observed, not true per-route dominance.

## S11_work_and_common_attainment
Unadjusted pointwise intervals. Common attainment includes only both-LB-attaining pairs. Cross archive/new and pooled runtime inference omitted.

## S12_station_attributes
Four byte-distinct contents, reused across partitions; not unseen station networks.

## S13_holdout_parents
All 48 original parent means retain sibling A/B and routes together. Descriptive effects; only pooled registered FSPC reliability is confirmatory.
