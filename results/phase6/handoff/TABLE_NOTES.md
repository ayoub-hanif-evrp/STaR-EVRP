# Table Notes

## T06-01_charging_complexity

Exact counts of visits by partition, with counts above three pooled. CON all includes no-charge routes; all selected STaR rows use the initially exposed population or named nonattained subset.

Data: `data/charging_complexity.csv`

## T06-02_mechanism

All 2,891 exposed routes. The within-feature strata partition routes. Bounds are 95% pointwise family-by-partition parent-bootstrap intervals where at least eight parents are represented.

Data: `data/mechanism_strata.csv`

## T06-03_analytical_single_visit

Independent Phase 6 tape on the AS1 panel. Completion is unconditional in native units. Timing and analytic versus empirical uncertainty are in the associated raw CSVs.

Data: `data/as1_summary.csv; data/as1_exact_vs_mc.csv`

## T06-04_fixed_topology

All and certified-subset comparisons on the same independent tape. The certified subset includes the single-visit mathematical oracle and certified linear-model MILP solves. All-panel rows include valid fallbacks. See solver stages for incumbent, replay, bounds and gaps.

Data: `data/fixed-topology_summary.csv; data/fixed-topology_solver_stages.csv`

## T06-05_controlled_runtime

Route-level medians from three repeats. Reliability is mean of the within-route means. Overshoot counts refer to individual repeats. CPU, IQR, work counts and parent-cluster contrasts are in the linked CSVs.

Data: `data/timing_summary.csv; data/timing_paired_effects.csv`
