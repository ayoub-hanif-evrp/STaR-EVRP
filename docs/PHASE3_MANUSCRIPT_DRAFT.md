# Charging-topology repair for fixed electric-vehicle routes with uncertain station waits

Alternative title: *When fixed-station partial charging is not enough: a held-out EVRPTW benchmark study*

## Abstract

We test whether changing the station sequence improves charging repair relative to optimizing energy amounts at fixed stations.
STaR uses local search with an isolated-delay necessary condition and a fixed-draw optimistic bound.
In a frozen held-out study over 2,321 charging-exposed routes, the paired reliability difference versus fixed-station
partial charging was +1.24 [+0.86, +1.65] percentage points. Against iterative scenario local search,
the difference was +0.32 [+0.13, +0.49] points; 13,024 vs 19,911 search draws; 29.69 vs 27.51 ms wall; 2,211 vs 2,193 attained; 3,135.83 vs 3,137.43 time units. The holdout supports incremental topology benefit over B4 but not a claim of general superiority over B3.

Alternative concise abstract: We benchmark offline station and charge-quantity repair for fixed customer routes using synthetic waits.
We separate measured time from simulation work and validate selected plans on independent scenario tapes.
The primary test directly compares topology repair with a strong restricted charging baseline. The holdout supports incremental topology benefit over B4 but not a claim of general superiority over B3.

## 1. Motivation and related work

Station queues can make deterministic routes miss hard deadlines. Keskin, Çatay and Laporte (2021) address stochastic
station waiting in a two-stage simulation-based EVRPTW method with route construction and recourse. Our question is narrower:
how much benefit is available from offline repair alone when vehicle assignments and ordered customers cannot change?
We use the heterogeneous charging extension of the 1,000-customer Homberger benchmark described by Hanif et al.
Partial charging is already established in EVRPTW (Keskin and Çatay, 2016), and Roberti and Wen (2016) study a
related deterministic single-vehicle time-window problem. The contribution tested here is the incremental value of
station-topology edits under stochastic waits, with a fixed-route comparator and an independently validated,
budget-matched protocol. The comparisons do not establish novelty of partial charging or scenario local search.

## 2. Model

Take a depot–customers–depot sequence and insert charging stop decisions between fixed customers. On each leg of length d,
elapsed travel increases by d and battery falls by d (h=1). At station s add an allowed amount q such that state of charge
remains within [0,700], using linear time q/r_s. Waiting is exp(mu_s + sigma_s Z), with independent standard normal visit shocks.
At customers take the maximum of arrival and opening time before service; success requires all latest starts and final depot
deadline. Station operating windows are off for source compatibility. Load/capacity and fleet/customer coverage inherit the
original route structure and are independently checked. Optimize lexicographically: seek estimated reliability ≥0.95 then
minimize mean full completion; below target prefer higher reliability and break ties by completion. No recourse or early-abort
completion is used.

## 3. Algorithms and bounds

All repair methods begin from the same CON solution. Candidate generation inserts, removes, replaces and relocates stations,
and adjusts quantities using downstream segment reserves, charger rates, coordinate moves and pairwise transfers.
B1 uses deterministic mean waits; B2 assigns per-visit probability 0.95^(1/K) and uses the lognormal quantiles.
B3 restarts first-improvement search from each incumbent and scores on 512 common scenarios. B4 restricts that search
to the original ordered station positions and optimizes energy. STaR prioritizes large marginal isolated delay risks.
A backward pass bounds how much single-visit wait can be absorbed before any downstream deadline. Omitting future ready-time
floors cannot delay the route further in that pass. Joint success implies satisfaction of each marginal cap; consequently the
minimum CDF is an upper bound, not a certificate of acceptance. Screen only after the search incumbent attains the sample
target. For a sampled prefix, credit every unscored draw as a success and give it zero-wait completion; prune only if this
optimistic score cannot outrank the incumbent on the fixed tape. Prefixes reuse the same ordinal shocks and station-specific
lognormal transforms. Neither the search nor the reported statistical attainment proves true model feasibility.

## 4. Frozen design and statistics

The six-family split blocks sibling A/B variants by parent. The primary endpoint is the route-weighted STaR–B4 difference
at 64 unique trials. Confidence intervals resample all routes and both variants of each parent together within family.
There are 9,999 bootstrap resamples; parent-balanced weighting is a sensitivity check. Final validation uses 10,000
independent draws per selected plan and a one-sided 95% Wilson lower bound for attainment. Other paired effects and
budget/stress comparisons are descriptive. Completion includes the entire route even when service fails.

## 5. Results

The frozen test included **48 parents / 96 variants**, **6,864 CON routes**,
**2,321 charging-exposed routes**, **4,543 no-charge routes**, and **628 exposed
B0 routes below the empirical 0.95 target**. All exposed routes were paired for the primary comparison.

| Method | Mean reliability | Attained / exposed | Full completion (native) | Mean draws | Wall ms |
|---|---:|---:|---:|---:|---:|
| B0 | 80.97% | 1,686/2,321 | 3,391.25 | 0 | 0.22 |
| B1 | 95.29% | 2,052/2,321 | 3,133.83 | 0 | 27.39 |
| B2 | 95.21% | 2,183/2,321 | 3,135.71 | 0 | 27.45 |
| B3 | 97.00% | 2,193/2,321 | 3,137.43 | 19,911 | 27.51 |
| B4 | 96.07% | 2,161/2,321 | 3,168.98 | 4,257 | 8.38 |
| STaR | 97.31% | 2,211/2,321 | 3,135.83 | 13,024 | 29.69 |
| STaR_no_partial | 94.19% | 2,096/2,321 | 3,230.53 | 8,400 | 27.41 |

STaR minus B4 (primary) was **+1.24 [+0.86, +1.65] percentage points** (estimate [95% cluster interval]).
Parent-balanced sensitivity: **+1.12 pp**
[+0.79, +1.47].
Completion difference: **-33.15 [-34.86, -31.48]** native units; on the **2,158** common attaining routes:
**-35.56 [-37.45, -33.70]**. Attainment difference: **+2.15 [+1.49, +2.90] pp**.

STaR minus B3 reliability: **+0.32 [+0.13, +0.49] pp**; 13,024 vs 19,911 search draws; 29.69 vs 27.51 ms wall; 2,211 vs 2,193 attained; 3,135.83 vs 3,137.43 time units.
The paired elapsed difference was **+2.18 [+1.63, +2.73] ms**. Counts measure incremental simulation work, not elapsed efficiency.
At the 8,192-scenario budget the reliability difference versus B3 was **+0.39 [+0.07, +0.70] pp**.
The second search seed yielded **+1.25 [+0.87, +1.65] pp** versus B4.
Removing partial charging changed reliability by **+3.12 [+2.22, +3.97] pp** (STaR minus ablation).
Observed stratum contributions to the primary effect: same_topology: -0.08 pp, topology_changed: +1.32 pp. These are associations from the saved routes,
not attribution to a single edit independent of the accompanying charge allocation.

STaR nonattainment (nonattained/exposed): C1-A: 0/67; C1-B: 0/19; C2-A: 1/188; C2-B: 0/142; R1-A: 0/328; R1-B: 0/368; R2-A: 48/237; R2-B: 18/191; RC1-A: 0/216; RC1-B: 0/163; RC2-A: 22/226; RC2-B: 21/176. Negative cases include customer misses,
depot misses, joint losses, and point-positive routes whose lower limits do not clear the target.
The fixed R2-A case is **R2_10_2/A/0**, chosen without outcome information.

Fixed-plan synthetic robustness for STaR, without reoptimization:
- scale125: 96.00% reliability, 2,112/2,321 attained.
- sigma125: 97.00% reliability, 2,150/2,321 attained.
- copula035: 97.32% reliability, 2,201/2,321 attained.

Use `results/phase3/tables/overall.tex` for the main benchmark and `paired.tex` for uncertainty.
Use Figures 17–19 for the paired objective outcomes, 20–21 for scenario versus elapsed cost, 22–25 for family
and mechanism results, and 26 for near-threshold uncertainty. The captions and exact paths are in `PHASE3_FIGURE_INDEX.md`.

## 6. Threats to validity and conclusion

Queues are synthetic, not estimates from real station operations. Copula/scale stresses do not model fleet interactions,
state-dependent or endogenous congestion. Objective gains are conditional on the CON starting solutions and fixed customer
orders, not outcomes for unrestricted VRP fleets. The bootstrap assumes comparable parents within each family, and the
runtimes are machine- and scheduling-dependent. The selected-plan topology strata are descriptive, and finite budgets do
not prove unrepaired routes cannot be repaired. The holdout supports incremental topology benefit over B4 but not a claim of general superiority over B3.

## References

- Hanif, A.; Abid, M.; Tabaa, M.; Bensag, H.; Youssfi, M. (2026). Electric Vehicle Routing with Time Windows and
  Heterogeneous Charging-Station Attribute Dataset. *Data* 11(4), 83. DOI: 10.3390/data11040083.
- Keskin, M.; Çatay, B.; Laporte, G. (2021). A simulation-based heuristic for the electric vehicle routing problem with
  time windows and stochastic waiting times at recharging stations. *Computers & Operations Research* 125, 105060.
  DOI: 10.1016/j.cor.2020.105060.
- Keskin, M.; Çatay, B. (2016). Partial recharge strategies for the electric vehicle routing problem with time windows.
  *Transportation Research Part C* 65, 111–127. DOI: 10.1016/j.trc.2016.01.013.
- Roberti, R.; Wen, M. (2016). The Electric Traveling Salesman Problem with Time Windows.
  *Transportation Research Part E* 89, 32–52. DOI: 10.1016/j.tre.2016.01.010.
