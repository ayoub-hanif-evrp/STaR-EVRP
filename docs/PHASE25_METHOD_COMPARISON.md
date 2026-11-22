# Phase 2.5 method comparison

All methods start from the identical deposited-CON route at battery 700 and unit energy consumption, preserve the original customers and replay against the same independent validation tape. No method sees validation results during search.

| Method | Search objective and allowed moves |
|---|---|
| B0 | Keep the CON plan; no search simulation. |
| B1 | Iterative deterministic search using per-visit arithmetic mean waits. Prefer feasibility in that fixed timing replay, then smaller completion. |
| B2 | Iterative deterministic search using candidate-specific per-visit lognormal quantiles. With (K) independent visits, allocate the same probability (0.95^{1/K}) to each. If the route succeeds with all waits at their quantiles, the corresponding rectangular event has probability at least 0.95. This is sufficient, not necessary; prefer quantile replay feasibility, then completion. |
| B3 | First-improvement scenario local search, restarting the shared move enumeration from each accepted incumbent. All stochastic candidates get the same complete 512-scenario optimization tape. |
| B4 | Same stochastic score and iterative search as B3, but the ordered station stops cannot change. Try minimal-reserve and speed-aware allocations, full recharge, coordinate adjustments and pairwise energy transfers at four scales. This is a strong bounded heuristic, not an exact continuous optimum. |
| STaR | Same stochastic objective and operator set as B3. Order station edits by isolated-wait marginal risk, prioritize nearby gaps, use target-only analytical rejection and deterministic fixed-tape prefix pruning. |
| STaR no partial | Retain topology edits and STaR ordering/screening, but disable quantity steps and rebuild full charge schedules for topology changes. |

The shared topology operators are replacement, removal, insertion and relocation. Geometry shortlists the three smallest-detour station alternatives after a single-leg battery filter. Feasible charge allocations are computed over whole segments to the next station/depot, not just the next node. The speed-based policy carries energy from a faster charger through slower downstream chargers when battery headroom permits. Coordinate steps and pairwise transfers can trade earlier charging time against later charging time, slack, and residual energy. Static visits with zero added energy still incur the visit's queue; dropping that visit is a topology move and is unavailable to B4. This isolates the value of station edits. The first-improvement search is bounded and may miss feasible simultaneous multi-edits.

## Protocol

Primary comparator and outcomes: STaR minus B4 on the 64-plan profile, using mean paired validation reliability and expected full completion; also report attainment and completion on the intersection of independently attaining routes. B3 is the direct control for STaR's search efficiency; B1/B2 check against simpler surrogate methods. Treat all family, profile and mechanism comparisons as development evidence, not externally preregistered or confirmatory.

Compare 24- and 64-plan caps, 8,192 stochastic replications, and a 40 ms admission deadline. All caps apply per route; elapsed time excludes the separate final validation. B0 has no search. B1/B2 need zero search scenarios and can use the guard candidate limit in the scenario-capped profile; B4 may exhaust its neighborhood before any cap. A max-budget comparison does not imply equal work consumed. The 40 ms profile is machine-specific and cooperative (late challengers discarded, timing overshoot reported); do not interpret that profile as a strict process deadline.

Validation uses 4,096 draws. A route attains only if its **pointwise one-sided 95% Wilson lower bound** is at least 0.95. This is neither a mathematical certificate nor a simultaneous guarantee. Pair methods by parent, variant and original route ID. The 95% intervals come from 9,999 whole-parent percentile bootstrap draws (all routes and both variants travel together), using the route-weighted estimand and 12 development parents. This small-cluster, deliberately stratified, development-only benchmark does not justify population-wide claims. No significance threshold is used to select a favorable budget. Example figures show an extreme restoration and a deterministic choice of unrepaired R2 route, not representative distributions.
