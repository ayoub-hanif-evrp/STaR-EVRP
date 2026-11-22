"""Render scientific report and manuscript from audited Phase 3 results."""

from star_evrp.results_io import load_json


def write(path, content):
    path.write_text(content.strip() + "\n", encoding="utf-8")


def render(root, out):
    result = load_json(out / "processed/summary.json")
    freeze = load_json(out / "manifests/freeze.json")
    reference = load_json(out / "reports/replay.json")
    closed = load_json(out / "reports/audit.json")
    cfg = freeze["config"]
    primary = result["primary"]
    total = result["population"]
    main = cfg["primary"]

    def effect(control, metric, profile=main):
        return next(row for row in result["paired"] if (row["profile"], row["competitor"], row["metric"])
                    == (profile, control, metric))

    def interval(row, scale=1):
        return f'{scale * row["estimate"]:+.2f} [{scale * row["lower95"]:+.2f}, {scale * row["upper95"]:+.2f}]'

    topology = effect("B4", "reliability")
    competitive = effect("B3", "reliability")
    wall = effect("B3", "wall_ms")
    completion = effect("B4", "full_completion")
    both = effect("B4", "full_completion_common_attained")
    if topology["lower95"] <= 0:
        decision = "Negative or inconclusive"
        claim = "The holdout did not establish an incremental reliability benefit over fixed-station partial charging."
    elif competitive["lower95"] > 0 and wall["upper95"] <= 0 and completion["upper95"] <= 0:
        decision = "Strong within the frozen benchmark"
        claim = "The holdout supports a topology benefit and favorable competitiveness under the measured protocol."
    else:
        decision = "Narrow result"
        claim = "The holdout supports incremental topology benefit over B4 but not a claim of general superiority over B3."

    def compared(comparator):
        star, other = primary["STaR"], primary[comparator]
        return (f'{star["search_scenarios"]:,.0f} vs {other["search_scenarios"]:,.0f} search draws; '
                f'{star["search_wall_ms"]:.2f} vs {other["search_wall_ms"]:.2f} ms wall; '
                f'{star["lower_bound_attained"]:,} vs {other["lower_bound_attained"]:,} attained; '
                f'{star["full_completion_time"]:,.2f} vs {other["full_completion_time"]:,.2f} time units')

    families = sorted((r for r in result["family"] if r["method"] == "STaR"),
                      key=lambda row: (row["family"], row["variant"]))
    failure_text = "; ".join(f'{r["family"]}-{r["variant"]}: {r["n"]-r["lower_bound_attained"]}/{r["n"]}'
                             for r in families)
    mechanism = ", ".join(f"{key}: {100 * val:+.2f} pp" for key, val in result["effect_contributions"].items())
    alt_budget = effect("B3", "reliability", "s8192")
    partial = effect("STaR_no_partial", "reliability")
    seed2 = effect("B4", "reliability", "c64_seed2")
    compact = (
        "| Method | Mean reliability | Attained / exposed | Full completion (native) | Mean draws | Wall ms |\n"
        "|---|---:|---:|---:|---:|---:|\n"
        + "\n".join(f'| {name} | {100*r["mean_R"]:.2f}% | {r["lower_bound_attained"]:,}/{r["n"]:,} | '
                    f'{r["full_completion_time"]:,.2f} | {r["search_scenarios"]:,.0f} | {r["search_wall_ms"]:.2f} |'
                    for name, r in primary.items())
    )
    stress = "\n".join(f'- {name}: {100 * reliability:.2f}% reliability, {attained:,}/{n:,} attained.'
                       for name, method, _, _, _, n, reliability, attained, _ in result["stress_results"]
                       if method == "STaR")
    results_text = f"""
The frozen test included **{result['n_parents']} parents / {total[2]} variants**, **{total[3]:,} CON routes**,
**{total[4]:,} charging-exposed routes**, **{total[5]:,} no-charge routes**, and **{total[6]:,} exposed
B0 routes below the empirical 0.95 target**. All exposed routes were paired for the primary comparison.

{compact}

STaR minus B4 (primary) was **{interval(topology, 100)} percentage points** (estimate [95% cluster interval]).
Parent-balanced sensitivity: **{100*topology['parent_equal_estimate']:+.2f} pp**
[{100*topology['parent_equal_lower95']:+.2f}, {100*topology['parent_equal_upper95']:+.2f}].
Completion difference: **{interval(completion)}** native units; on the **{both['n']:,}** common attaining routes:
**{interval(both)}**. Attainment difference: **{interval(effect('B4', 'attained'), 100)} pp**.

STaR minus B3 reliability: **{interval(competitive, 100)} pp**; {compared('B3')}.
The paired elapsed difference was **{interval(wall)} ms**. Counts measure incremental simulation work, not elapsed efficiency.
At the 8,192-scenario budget the reliability difference versus B3 was **{interval(alt_budget, 100)} pp**.
The second search seed yielded **{interval(seed2, 100)} pp** versus B4.
Removing partial charging changed reliability by **{interval(partial, 100)} pp** (STaR minus ablation).
Observed stratum contributions to the primary effect: {mechanism}. These are associations from the saved routes,
not attribution to a single edit independent of the accompanying charge allocation.

STaR nonattainment (nonattained/exposed): {failure_text}. Negative cases include customer misses,
depot misses, joint losses, and point-positive routes whose lower limits do not clear the target.
The fixed R2-A case is **{'/'.join(map(str, result['example']))}**, chosen without outcome information.

Fixed-plan synthetic robustness for STaR, without reoptimization:
{stress}
"""
    write(root / "docs/PHASE3_FINAL_REPORT.md", f"""
# Phase 3 final scientific report

**{decision}.** {claim}

Frozen executable: `{result['commit']}` (`{result['tag']}`). This was one preregistered holdout
run following the original train/test split; no method, configuration, or analysis changes were made after performance access.
Secondary intervals are exploratory and pointwise, not simultaneous.

## Held-out results
{results_text}
## Integrity and deliverables

- P3-G0: preflight passed, including {result['tests']} tests and source/producer reconciliation.
- P3-G1: tagged code, protocol, split and file hashes checked before execution; separate post-tag development smoke passed.
- P3-G2: all {closed['cases']} holdout instances and all exposed routes accounted for under every declared profile.
- P3-G3: {closed['plans']:,} selected plans independently reconstructed and validated at {cfg['validation_samples']:,}
  draws per plan/model, with {cfg['validation_scalar_checks']} reference-simulator checks per plan/model.
- P3-G4: sole confirmatory contrast STaR–B4, paired parent clustering; B3 quality, wall and draw costs separately reported.
- P3-G5: {closed['figures']} audited 400-DPI PNGs and {closed['table_families']} CSV/LaTeX/Markdown table families.
- P3-G6: {closed['raw_plan_files']:,} hashed compressed batches and report/artifact lineage matched the freeze;
  replay ran in {reference['elapsed_seconds']:.1f} seconds.

See `docs/PHASE3_REPRODUCIBILITY.md`, `docs/PHASE3_FIGURE_INDEX.md`, and
`docs/PHASE3_MANUSCRIPT_DRAFT.md`. The 40-ms development diagnostic was not repeated, as preregistered.
Timing reflects six-worker execution with possible contention. The synthetic station model and fixed CON customer
orders limit external applicability; do not infer a universal queue policy or global EVRPTW improvement.
""")
    write(root / "docs/PHASE3_PAPER_OUTLINE.md", f"""
# Conference paper outline

1. **Question:** Does charging-topology repair improve on fixed-station partial charging at the same candidate limit?
2. **Model:** Fixed CON customer order, explicit energy/timing constraints, synthetic lognormal waiting.
3. **Method:** Shared neighborhood, isolated-delay necessary condition, and deterministic optimistic tape bound.
4. **Frozen comparison:** B0–B4, 48 paired parents, separated optimization/validation, and one primary endpoint.
5. **Results:** {claim} Show scenario work and wall time separately.
6. **Mechanisms:** Quantities, topology changes, the ablation, and the pre-selected R2-A case.
7. **Limitations:** Synthetic stress tests, measurement uncertainty, benchmark and runtime scope.
8. **Reproduction:** Frozen tag, compressed plan bundles, audit, and source-linked figures/tables.
""")
    write(root / "docs/PHASE3_MANUSCRIPT_DRAFT.md", f"""
# Charging-topology repair for fixed electric-vehicle routes with uncertain station waits

Alternative title: *When fixed-station partial charging is not enough: a held-out EVRPTW benchmark study*

## Abstract

We test whether changing the station sequence improves charging repair relative to optimizing energy amounts at fixed stations.
STaR uses local search with an isolated-delay necessary condition and a fixed-draw optimistic bound.
In a frozen held-out study over {total[4]:,} charging-exposed routes, the paired reliability difference versus fixed-station
partial charging was {interval(topology, 100)} percentage points. Against iterative scenario local search,
the difference was {interval(competitive, 100)} points; {compared('B3')}. {claim}

Alternative concise abstract: We benchmark offline station and charge-quantity repair for fixed customer routes using synthetic waits.
We separate measured time from simulation work and validate selected plans on independent scenario tapes.
The primary test directly compares topology repair with a strong restricted charging baseline. {claim}

## 1. Motivation and related work

Station queues can make deterministic routes miss hard deadlines. Keskin, Çatay and Laporte (2021) address stochastic
station waiting in a two-stage simulation-based EVRPTW method with route construction and recourse. Our question is narrower:
how much benefit is available from offline repair alone when vehicle assignments and ordered customers cannot change?
We use the heterogeneous charging extension of the 1,000-customer Homberger benchmark described by Hanif et al.
The comparisons test a specific heuristic and operators, not the novelty of partial charging or scenario local search themselves.

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
{results_text}
Use `results/phase3/tables/overall.tex` for the main benchmark and `paired.tex` for uncertainty.
Use Figures 17–19 for the paired objective outcomes, 20–21 for scenario versus elapsed cost, 22–25 for family
and mechanism results, and 26 for near-threshold uncertainty. The captions and exact paths are in `PHASE3_FIGURE_INDEX.md`.

## 6. Threats to validity and conclusion

Queues are synthetic, not estimates from real station operations. Copula/scale stresses do not model fleet interactions,
state-dependent or endogenous congestion. Objective gains are conditional on the CON starting solutions and fixed customer
orders, not outcomes for unrestricted VRP fleets. The bootstrap assumes comparable parents within each family, and the
runtimes are machine- and scheduling-dependent. The selected-plan topology strata are descriptive, and finite budgets do
not prove unrepaired routes cannot be repaired. {claim}

## References

- Hanif et al., dataset article in *Data* 11(4), article 83. DOI: 10.3390/data11040083.
- Keskin, M.; Çatay, B.; Laporte, G. (2021). A simulation-based heuristic for the electric vehicle routing problem with
  time windows and stochastic waiting times at recharging stations. *Computers & Operations Research* 125, 105060.
  DOI: 10.1016/j.cor.2020.105060.
""")
