# Boundaries for interpretation

- 4 distinct station CSV contents across 120 routing problems; all four also occur in development. Holdout parents are distinct, not novel station-attribute tables.
- Synthetic lognormal independent visit waits are a modeling assumption, not real station queues; the copula and scale checks are descriptive and do not reoptimize.
- Fixed offline customer order and assignment from CON, linear station rates, Q=700, h=1. Station operating hours are disabled. Native benchmark time is not minutes.
- Success is the joint route customer/depot event, not fleet service probability or global EVRPTW optimality.
- 10,000 final validation draws per plan. Pointwise Wilson classification and mean paired cluster intervals answer different questions. Near-threshold and tie checks do not establish true route superiority.
- Equal caps, unequal consumed trials. B4 adjusts quantities only and is not a quantity oracle. "No limit hit" is a counter-based diagnosis, not a recorded termination label or a proof of an exhaustive quantity optimum.
- Five-second wall guard is cooperative; archived elapsed and CPU times reflect six workers. Lower simulation work did not make STaR faster than B3.
- Only route-weighted c64 reliability STaR minus B4 is confirmatory. Other endpoints, seeds, stresses and sensitivity intervals are unadjusted and exploratory.
