# Figure Captions

## F06-01_charging_complexity

Station visits include zero-quantity stops. Left compares the original CON distribution in the development and holdout partitions. Right gives matched CON and STaR visit counts for 2,891 exposed routes; darker shading uses log(1 + count) to show sparse transitions. Descriptive archived data.

Data: `data/charging_complexity.csv; data/visit_transitions.csv`

## F06-02_route_mechanism

All 2,891 exposed routes. Positive and negative observed reliability differences contribute separately to the route-weighted STaR mean. Nonattainment uses the one-sided Wilson lower bound; counts are failures over routes, with source minimum customer slack quartiles frozen on development. The strata overlap across feature types. Exploratory.

Data: `data/paired_directions.csv; data/mechanism_strata.csv`

## F06-03_analytical_single_visit

113 prospectively selected routes, originally single-visit. Left compares the new 10,000-row tape for AS1 and saved plans, with pointwise clustered 95% intervals. The CON reference is in T06-03. Right uses the AS1 plans still containing one visit. The analytical optimizer considers zero or one visit. Frozen STaR and SLS may use multiple visits. Exploratory panel.

Data: `data/as1_paired_effects.csv; data/as1_exact_vs_mc.csv`

## F06-04_fixed_topology

118 fixed comparator panel routes on the new 10,000-draw tape. Includes valid fallback plans on every uncertified route. Solver status counts: below target certified 1, replay or solver failure 16, single visit oracle 96, target certified 4, target completion only 1. Points are paired route means and bars are pointwise 95% parent-cluster intervals. FT-SAA received a separate solver budget. Exploratory panel.

Data: `data/fixed-topology_paired_effects.csv; data/fixed-topology_route_results.csv`

## F06-05_controlled_runtime

118 paired routes and three repeats per method per nominal guard. Left uses within-route mean reliability and pointwise 95% parent-bootstrap intervals. Center shows the median and interquartile range of per-route median wall time, with nominal guards as gray ticks. Right shows mean incremental search draws. The 50 ms guard was primary. Cooperative guards can overshoot. Exploratory panel.

Data: `data/timing_summary.csv; data/timing_paired_effects.csv`
