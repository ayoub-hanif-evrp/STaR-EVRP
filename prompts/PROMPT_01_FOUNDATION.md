# PROMPT 1 OF 3 — BUILD THE COMPLETE SCIENTIFIC FOUNDATION OF STaR-EVRP

## YOUR ROLE AND MISSION

You are a senior research software engineer, operations research specialist, and scientific computing expert working on a PhD-level conference paper.

You are responsible for implementing the **first complete development phase** of a research project named:

**STaR-EVRP: Slack-Targeted Stochastic Charging Repair for Large-Scale Electric Vehicle Routing with Time Windows.**

**Project root directory:** `STaR_EVRP`

The project investigates whether changing charging decisions, without changing customer sequences, can improve the reliability of electric delivery routes under stochastic charging-station waiting times.

Our eventual methodological contribution will combine mathematically safe candidate rejection, slack-targeted charging repair, and computationally efficient stochastic evaluation.

However, **this first prompt is exclusively about creating a correct, reproducible, performant experimental foundation and establishing whether the proposed optimization problem has sufficient research potential.**

You must implement working code, execute meaningful experiments on the supplied dataset, verify correctness, and produce genuine numerical results, publication-quality PNG figures, and paper-ready tables.

**CRITICAL EXECUTION INSTRUCTION: DO NOT STOP UNTIL EVERY TASK AND ACCEPTANCE CRITERION IN THIS PROMPT HAS BEEN ADDRESSED.**

Do not stop after creating folders, implementing a parser, writing a few tests, or producing a preliminary report. Continue through implementation, debugging, real-data execution, validation, reporting, and final auditing.

Work autonomously. Resolve normal engineering decisions yourself. Do not repeatedly ask for confirmation or interrupt the work to present intermediate plans.

If a task encounters an error, investigate and fix it. If an external resource is genuinely unavailable, complete every independent task, record the exact blocker, and never invent a successful result.

Do not fabricate results, silently weaken constraints, or claim that a failing test passed.

---

# 1. SCIENTIFIC OBJECTIVE

The research concerns the Electric Vehicle Routing Problem with Time Windows (EVRPTW), under stochastic waiting times at heterogeneous charging stations.

We will start from deterministic, energy-feasible vehicle routes.

For this project:

- Customer sequences are fixed after baseline generation.
- Customer assignments to vehicles are fixed.
- Customer time windows are hard constraints.
- Battery capacity and energy consumption are explicitly modeled.
- Charging stations have heterogeneous charging rates.
- Charging-station waiting times follow the published lognormal distributions.
- Charging waiting times are exogenous; the model does not simulate queue interactions between the vehicles in our fleet.
- Charging decisions may eventually be modified while preserving the customer sequence.
- The primary target is 95% route-level on-time reliability.

The central future question is:

> Can charging-only repair make deterministic EVRPTW routes more reliable under stochastic waiting times, while minimizing additional operating time and computation?

Before implementing our new optimization algorithm, we must answer four fundamental questions:

**RQ0.1 — Charging exposure:** How many baseline vehicle routes actually visit charging stations?

**RQ0.2 — Stochastic reliability:** How much does station waiting-time uncertainty reduce route-level reliability?

**RQ0.3 — Failure mechanisms:** Which instance families, charging-station properties, and time-window characteristics explain unreliability?

**RQ0.4 — Repair opportunities:** Do there exist alternative charging decisions that could improve the unreliable routes without changing the customer sequence?

These questions determine whether the future algorithm is scientifically justified.

Do not assume the dataset will produce strong results. Measure the actual effects.

---

# 2. DATASET — MANDATORY REQUIREMENTS

I will place the dataset inside a folder named:

`STaR_EVRP/dataset/`

The dataset is:

**EVRPTW Benchmark Dataset with Heterogeneous Charging Stations and Two Time-Window Variants.**

Source publication:

https://doi.org/10.3390/data11040083

Zenodo:

https://doi.org/10.5281/zenodo.19443014

The dataset extends the 1,000-customer Homberger benchmark.

It contains 60 original instances from six families:

- C1
- C2
- R1
- R2
- RC1
- RC2

There are two EVRPTW time-window variants per original instance:

**Variant A:** original customer time windows.

**Variant B:** relaxed customer due dates.

This gives 120 augmented benchmark instances.

## 2.1. Dataset discovery

Do not assume the ZIP archive has already been extracted into a particular nested path.

Implement a robust dataset-discovery module that supports the actual extracted structure under `dataset/`.

According to the publication, the archive contains components named approximately:

```text
dataset/
    homberger_1000_customer_instances/
    variant_A_original_TW/
    variant_B_relaxed_TW/
    code/
    params.json
    ev_specs.json
    README.md
```

The archive might contain an additional enclosing directory.

Inspect the actual files before implementing the parser.

Read the dataset's original README, the EV specifications, generation scripts, and any included baseline or validation code.

Use the deposited files as the primary source of truth for ambiguous implementation details.

**Do not modify the original dataset files.**

## 2.2. Required data parser

Implement a reliable parser for:

1. The augmented Homberger-style `.txt` instance files.
2. The corresponding `*_stations.csv` files.
3. `ev_specs.json`.
4. `params.json`.
5. Fleet-size and load-capacity parameters from the instance headers.

The instance files include depot, customer, and charging-station nodes.

Node identifiers follow the published convention:

- Depot: `0`.
- Customers: `1` through `1000`.
- Charging stations: identifiers greater than `1000`.

Station CSV attributes include:

- `station_id`
- `charging_rate`
- `density_score`
- `wait_mu`
- `wait_sigma`
- `price_mu`
- `price_sigma`

Join station attributes to charging-station nodes using the actual station identifier, never row position.

Validate:

- Unique node IDs.
- Matching station records.
- Valid charging rates.
- Finite waiting-time parameters.
- Nonnegative `wait_sigma`.
- Valid time windows.
- Nonnegative service times and demands.
- Fleet size and capacity.
- Battery and consumption parameters.
- Dataset-family and variant identification.
- Customer coverage and expected customer count.

Record any malformed instances explicitly. Never silently discard them.

Create typed Python structures for instances, nodes, stations, routes, charging visits, route traces, and simulation outcomes.

## 2.3. Data inventory

Produce a complete, reproducible dataset inventory containing:

- Number of instances per variant and family.
- Customer counts.
- Charging-station counts.
- Available fleet sizes.
- Load capacities.
- Charging-rate distributions.
- Waiting-time distribution parameters.
- Expected station waiting times.
- Station waiting-time 95th percentiles.
- Customer time-window distributions.

Use the correct lognormal parameterization:

\[
W_s\sim\operatorname{LogNormal}(\mu_s,\sigma_s^2)
\]

The arithmetic mean is:

\[
\mathbb E[W_s]=\exp(\mu_s+\sigma_s^2/2)
\]

The median is \(\exp(\mu_s)\).

Do not confuse the logarithmic location parameter with arithmetic mean waiting time.

Create SHA-256 hashes for source files and record dataset provenance.

---

# 3. MATHEMATICAL MODEL AND ROUTE SEMANTICS

Implement the benchmark's deterministic physics exactly.

Use the official `ev_specs.json` values and documented dataset conventions.

Our primary battery configuration is:

\[
Q=700
\]

Use the published consumption rate, which is \(h=1\) in the reported baseline experiments, unless an actual source-code discrepancy requires an explicit documented correction.

For nodes \(i,j\):

\[
d_{ij}=\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}
\]

Energy consumption:

\[
e_{ij}=h\,d_{ij}
\]

Use the source benchmark's travel-time convention. The published verification procedure uses travel time equal to Euclidean distance in native benchmark units.

Do not incorrectly label native benchmark time as real-world minutes or hours unless the dataset documentation establishes the conversion.

At charging station \(s\), adding energy \(q_s\) requires:

\[
t_s^{charge}=\frac{q_s}{r_s}
\]

where \(r_s\) is the station's published charging rate.

The baseline should initially use the charging policy specified by the source implementation. If that is full recharging, reproduce full recharging.

Design the simulator so that partial charging can be supported later, without requiring substantial rewriting.

## 3.1. Deterministic route trace

For each route, calculate and store at every visit:

- Node identifier.
- Node type.
- Arrival time.
- Service or charging start time.
- Departure time.
- Waiting caused by early arrival.
- Customer service time.
- Battery energy on arrival.
- Battery energy on departure.
- Energy charged.
- Vehicle load or cumulative served demand.
- Remaining time-window slack.
- Remaining battery capacity.

Enforce:

\[
0\leq E_k\leq Q
\]

for every leg and visit.

Enforce customer service start:

\[
B_i=\max(a_i,A_i)
\]

with:

\[
B_i\leq b_i
\]

Also enforce depot-return deadlines, station availability constraints where applicable, fleet-size limits, load capacity, and complete customer coverage.

Determine and document the exact ordering of station-arrival, opening-time waiting, queue waiting, and battery charging from the source semantics.

The same ordering must be used consistently in every simulator.

## 3.2. Independent feasibility checker

Implement a separate deterministic route validator.

It must not simply trust the baseline algorithm's own reported feasibility.

Check:

- Each customer served exactly once across the entire solution.
- No missing or duplicated customers.
- Customer sequences valid.
- Route starts and ends at the depot.
- Battery never negative.
- Battery never exceeds capacity.
- Charging quantities are physically feasible.
- All route time windows respected.
- Depot closing respected.
- Vehicle load within capacity.
- Fleet size within allowed limits.

Return detailed failure reasons and numerical traces.

Use conservative numerical tolerances appropriate to the dataset's floating-point conventions.

Do not silently repair a failed route inside the validator.

---

# 4. DETERMINISTIC BASELINE GENERATION

This is one of the most important tasks.

The paper reports two deterministic baseline methods:

**CON:** construction-only.

**HC:** hill climbing applied to construction solutions.

At \(Q=700\), the published paper reports complete feasible solutions for both methods across 60/60 instances per variant.

However, do not assume the published dataset archive contains ready-made route-solution files.

## 4.1. Search for existing baseline implementations

Inspect:

- Deposited code.
- Dataset README.
- Available baseline scripts.
- Any serialized route outputs.
- Any solution-format documentation.

Prioritize reusing the actual published baseline implementation if it exists and can be executed correctly.

If route files exist, import them and validate independently.

If the source implementation exists without serialized solutions, execute it and export complete route-level outputs.

If neither is available, implement a documented, independently reconstructed deterministic constructive heuristic based on the publication, including charging-aware reachability, return-to-depot feasibility, fleet constraints, and customer time windows.

You may add efficient deterministic construction improvements if necessary to produce valid solutions, but identify them separately.

**Never label an independently reconstructed implementation an exact replication of published CON or HC unless equivalence has actually been demonstrated.**

Do not make up reference routes to match published aggregate statistics.

## 4.2. Baseline performance requirements

Because every instance contains 1,000 customers, efficiency matters.

Use appropriate computational techniques:

- Precomputed coordinate arrays.
- Efficient distance calculations.
- Candidate filtering.
- Vectorized operations where useful.
- Caching repeated geometric computations.
- Deterministic tie breaking.
- Safe loop-termination conditions.
- No repeated unnecessary parsing.

Avoid an unnecessarily expensive implementation that prevents completing the pilot.

Use bounded, reproducible search and multistart construction if justified.

Every constructed solution must be validated independently.

If complete feasible solutions cannot be obtained for particular instances, keep those failures in the results and diagnose them.

Do not falsely report infeasible instances as complete.

## 4.3. Baseline artifacts

For every successfully constructed baseline, save:

- Complete ordered routes.
- Customer order.
- Charging-station visit order.
- Charging quantities.
- Detailed deterministic route traces.
- Feasibility report.
- Total distance.
- Number of vehicles.
- Number of charging visits.
- Total charging time.
- Total customer service time.
- Completion times.
- Algorithm runtime.
- Random seed and configuration.
- Source code and input dataset hashes.

Use structured JSON or another documented, lossless format for the authoritative route outputs.

Do not rely on lossy CSV rounding when serializing routes.

Provide a command that regenerates every baseline from scratch.

---

# 5. STOCHASTIC CHARGING WAITING-TIME SIMULATOR

Implement a fully working Monte Carlo simulator.

This must use the published station-specific waiting-time distributions.

For station \(s\):

\[
W_s=\exp(\mu_s+\sigma_s Z),\qquad Z\sim N(0,1)
\]

The simulator must support arbitrary fixed charging plans, not only those produced by our initial baseline.

## 5.1. Simulation rules

For each scenario:

1. Load the fixed route and charging decisions.
2. Sample waiting time at every charging visit.
3. Propagate arrival and departure times through the route.
4. Include deterministic travel, charging, customer service, and early-arrival waiting.
5. Apply customer time windows.
6. Check station windows and depot return.
7. Record whether the entire route succeeds.

The primary simulation model assumes independent waiting-time samples for different charging visits.

Repeated visits to the same station must be treated as separate sampled visits under this initial model.

Document that this independence assumption is a modeling choice; the dataset only specifies marginal station distributions.

Do not introduce empirical traffic, measured queue lengths, or other unsupported stochastic processes.

## 5.2. Route-level reliability

Define a route as successful only if:

- Every customer time window is satisfied.
- The depot-return deadline is respected.
- Any applicable station timing restrictions are respected.
- The charging plan remains physically valid.

Compute:

\[
\widehat{P}_{success}(r)
=
\frac{1}{N}\sum_{k=1}^{N}I_k
\]

where \(I_k=1\) if the route succeeds in simulation scenario \(k\).

The default research target is:

\[
P_{success}\geq0.95
\]

**This is route-level reliability, not customer-level reliability or whole-fleet reliability.**

Report the following metrics separately:

- Route-level all-deadlines success probability.
- Proportion of customers served on time.
- Probability of at least one late customer.
- Probability of a late depot return.
- Mean and maximum customer tardiness.
- Expected route completion time.
- 95th percentile completion time.
- Expected total charging-station waiting time.

For a route with no charging visits, stochastic waiting-time uncertainty has no effect. Its simulated success must equal its deterministic feasibility indicator.

## 5.3. Statistical correctness

Use deterministic, documented random seeds.

Separate random-number streams for:

- Development diagnostics.
- Future optimization.
- Future independent final testing.

Implement common-random-number support so that different charging policies can be evaluated fairly under matched underlying random draws.

Use stable identifiers and deterministic seed derivation, not Python's process-dependent `hash()`.

Provide Wilson confidence intervals for estimated route-success probabilities, including extreme probabilities near zero and one.

Monte Carlo scenarios are simulation replications, not independent EVRP instances.

Do not calculate paper-level confidence intervals by treating millions of simulated trajectories as independent benchmark instances.

Reserve a separate random stream for future confirmatory comparisons.

Implement efficient batch simulation, preferably vectorized over scenarios wherever correct and useful.

---

# 6. SAFE STOCHASTIC-INFEASIBILITY SCREEN — RESEARCH FOUNDATION

Although the complete STaR repair algorithm will be developed in Prompt 2, implement and thoroughly test the mathematical building blocks now.

For a deterministic charging plan \(p\), consider its charging visits \(j=1,\ldots,m\).

Let:

\[
\tau_j(p)
\]

be the maximum isolated waiting time at charging visit \(j\) that the route can tolerate while satisfying every deadline, with all other charging waits fixed to zero.

Compute this quantity using a mathematically justified procedure.

Because charging waits are nonnegative and downstream arrival times are monotone in the waits, route success implies that no individual wait exceeds its corresponding isolated-wait threshold.

Consequently:

\[
P(\text{route succeeds}\mid p)
\leq
U(p)=\min_j F_j(\tau_j(p))
\]

where \(F_j\) is the published lognormal CDF at charging visit \(j\).

For target reliability \(1-\alpha\):

\[
U(p)<1-\alpha
\]

is a **necessary-condition rejection test**.

If \(U(p)<0.95\), the fixed charging plan cannot achieve 95% route reliability under the stated marginal waiting-time model.

It may therefore be rejected without Monte Carlo evaluation.

A plan with \(U(p)\geq0.95\) is not necessarily reliable.

**Do not incorrectly treat passing this bound as a reliability certificate.**

## 6.1. Implementation requirements

Create:

- Isolated waiting-time threshold calculation.
- Lognormal CDF evaluation.
- Route-level upper reliability bound.
- Critical charging-visit identification.
- A mathematically safe rejection decision.

Handle:

- Routes with zero charging visits.
- Routes with one charging visit.
- Multiple charging visits.
- Tight customer time windows.
- Depot deadline violations.
- Numerically infinite waiting-time tolerance.
- Zero or near-zero remaining slack.
- Routes already infeasible when waits are zero.

Numerical threshold calculations must be conservative: an underestimated tolerated wait could cause an unsafe rejection.

Use an analytical latest-time propagation method if it can be derived and verified. Otherwise, use a carefully controlled monotone search with a conservative upper approximation.

Write the proof and assumptions in:

`docs/SAFE_SCREENING_MATHEMATICS.md`

Include mathematical tests demonstrating that the calculated upper probability bound does not incorrectly reject a truly target-reliable route in analytically solvable and exhaustive small cases.

A Monte Carlo estimate by itself is not proof of safe rejection.

---

# 7. EXPERIMENTAL SPLIT — PREVENT DATA LEAKAGE

Do not tune the final method on all 120 instances.

Create a deterministic development/holdout partition using the 60 original Homberger parent instances.

**Development set:**

Two parent instances from each of the six families.

Total:

12 parent instances × 2 variants = 24 EVRPTW benchmark instances.

Select them deterministically using the first two canonical sorted parent identifiers per family, after normalizing instance names.

**Holdout set:**

The remaining 48 parent instances.

Total:

48 × 2 = 96 benchmark instances.

The A and B versions of the same original instance must remain in the same partition.

Record the exact instance identifiers, file hashes, and partition-construction rules in a frozen manifest.

Do not select the development instances based on how favorable their preliminary results look.

**Do not evaluate or tune our future new optimization method on the holdout in this first development phase.**

Dataset integrity validation may inspect all 120 files, but stochastic research experiments must follow the frozen split.

---

# 8. RUN THE COMPLETE INITIAL EXPERIMENT

After implementing and testing the parser, baseline and stochastic simulator, execute a complete real-data development pilot.

Primary configuration:

```yaml
experiment: baseline_stochastic_audit
battery_capacity: 700
energy_consumption_rate: 1.0
target_route_reliability: 0.95

dataset:
  root: dataset
  families: [C1, C2, R1, R2, RC1, RC2]
  variants: [A, B]
  development_parents_per_family: 2
  holdout_parents_per_family: 8

simulation:
  scenarios_per_route: 2000
  independent_station_visit_waits: true
  scenario_seed: 20261122

reporting:
  save_raw_results: true
  save_route_traces: true
  generate_png_figures: true
  generate_csv_tables: true
  generate_latex_tables: true
```

Use the effective energy-consumption rate read from the official EV specs; the configuration above expresses the published \(h=1\) baseline setting.

Start with a smoke test on one instance, then run the complete 24-instance development pilot.

Make execution restartable so failures or interruptions do not destroy completed results.

Do not rerun successful experiments unnecessarily.

## 8.1. Essential measurements

For every route, report:

- Instance and family.
- Variant.
- Vehicle/route identifier.
- Number of customers.
- Number of charging visits.
- Whether the route is deterministically feasible.
- Deterministic completion time.
- Minimum deterministic customer time-window slack.
- Depot-return slack.
- Total energy charged.
- Expected charging-station waiting time.
- Estimated route reliability.
- Wilson confidence interval.
- Expected customer tardiness.
- Expected route completion time.
- Safe upper reliability bound \(U(p)\).
- Most critical charging visit, when applicable.

This is the core dataset for the future scientific analysis.

## 8.2. Separate three populations

Report results separately for:

**Population A — All routes.**

**Population B — Charging-exposed routes only.**

**Population C — Charging-exposed routes whose reliability is estimated below 95%.**

This distinction is essential.

If most routes have no charging visits, an overall reliability average can hide meaningful stochastic failures among the charging-exposed population.

Do not use only the all-route average.

## 8.3. Failure classification

Classify each route according to its observed simulation behavior:

- No stochastic charging exposure.
- High-reliability charging route.
- Customer time-window failures.
- Depot-return failures.
- Both customer and depot failures.
- Deterministically infeasible baseline.
- Statistical uncertainty near the reliability threshold.

Keep categories mutually exclusive where appropriate, or explicitly identify when multiple failure indicators can coexist.

Use confidence intervals when deciding whether a route is reliably above or below 95%.

Do not force statistically ambiguous routes into a confident classification.

---

# 9. PRELIMINARY CHARGING-REPAIR OPPORTUNITY AUDIT

This is a small but important addition to the original foundation plan.

We must investigate whether unreliable charging routes can realistically be improved without changing customer order.

**Do not yet implement the full STaR search algorithm. That belongs to Prompt 2.**

Instead, implement a transparent, limited repair-opportunity probe.

For a reproducibly selected subset of unreliable charging routes:

1. Identify the original charging visits.
2. Find up to five geographically nearby alternative stations per visit.
3. Generate simple single-station replacement candidates.
4. Optionally test removal of a charging stop if the resulting route remains energy-feasible.
5. Keep all customers in exactly the original order.
6. Preserve vehicle assignments.
7. Use the original baseline charging policy initially.
8. Validate deterministic energy and timing feasibility.
9. Evaluate valid alternatives using matched stochastic scenarios.
10. Compare their estimated reliability and completion time with the unchanged route.

Use a modest, fixed evaluation budget.

Save all attempted candidates and their validation outcomes, including rejected ones.

This probe is **not** a final optimization method and must not be presented as one.

Its purpose is to establish whether basic charging changes provide useful repair opportunities.

Report:

- Number of unreliable charging routes examined.
- Number with at least one deterministic charging alternative.
- Number with at least one reliability-improving alternative.
- Number with an alternative estimated to meet the 95% target.
- Best observed reliability improvement.
- Associated expected completion-time change.
- Cases where no viable alternative was found.

Use independent diagnostic scenarios for checking selected alternatives so that selection optimism is visible.

Do not claim global irreparability simply because this limited probe found no better candidate.

---

# 10. PUBLICATION-QUALITY FIGURES — PNG ONLY

This requirement is extremely important.

Every scientific figure must be produced from real experimental data by reproducible Python scripts.

**All figures must be PNG. Do not produce SVG, PDF, or JPEG figure outputs.**

Use Matplotlib and appropriate scientific visualization libraries.

Requirements:

- Minimum 300 DPI; preferably 400 DPI.
- Clean and professional academic styling.
- Readable fonts at conference-paper column size.
- Consistent colors throughout all figures.
- Colorblind-accessible palette.
- Correct axes and measurement units.
- No clipped tick labels or legends.
- No unnecessary 3D plots.
- No decorative charts.
- Clear separation of variants A and B.
- Clear number of observations represented.
- Appropriate uncertainty indicators.
- No fabricated values.
- No plotting test fixtures as scientific results.

Generate at least the following figures.

### Figure 1 — Charging exposure

`fig01_charging_exposure_by_family_variant.png`

A grouped or stacked comparison showing the fraction of routes with:

- Zero charging visits.
- Exactly one charging visit.
- Two or more charging visits.

Organize by benchmark family and time-window variant.

This figure establishes the magnitude of the actual problem.

### Figure 2 — Baseline stochastic route reliability

`fig02_baseline_route_reliability.png`

Show the empirical distribution or ECDF of estimated route-success probabilities.

Clearly distinguish all routes from charging-exposed routes, using separate panels or visual encodings.

Mark the 95% reliability target.

### Figure 3 — Time-window slack versus reliability

`fig03_slack_vs_reliability.png`

Show the relationship between minimum deterministic customer time-window slack and estimated route reliability for charging-exposed routes.

Use distinct markers or facets for benchmark family or variant.

Include enough information to distinguish the correlation from the many routes with zero stochastic exposure.

### Figure 4 — Waiting-time risk across stations

`fig04_station_waiting_time_risk.png`

Visualize how expected waits and 95th-percentile waits vary across charging stations or charging-station density groups.

Use the true lognormal parameters.

Clearly distinguish station attributes from realized simulated waiting times.

### Figure 5 — Stochastic failure modes

`fig05_failure_modes.png`

Show the relative frequencies of customer time-window violations, depot-return violations, and other applicable timing failures.

Separate benchmark family or time-window variants where the sample size supports it.

Do not portray deterministic energy violations as consequences of random waiting if energy consumption is deterministic.

### Figure 6 — Preliminary charging-repair headroom

`fig06_repair_headroom.png`

For routes included in the repair-opportunity probe, compare the unchanged baseline reliability with the best simple alternative found under the fixed probe budget.

Label the experiment as an exploratory diagnostic, not the final proposed algorithm.

If no successful repair is found, the chart must truthfully show that result.

### Figure generation scripts

Provide a single command that regenerates every figure from saved raw results.

Use a common figure-style module.

Use titles and captions that accurately describe the plotted metrics.

Also create a figure index identifying the corresponding source CSV files and suggested manuscript captions.

---

# 11. PAPER-READY TABLES

Generate tables in three formats:

- `.csv` for auditing and analysis.
- `.tex` for direct use in LaTeX manuscripts.
- `.md` for easy inspection.

Create at least these six tables:

**Table 1 — Dataset characteristics**

Instance families, number of instances, station counts, time-window characteristics, and waiting-time attributes.

**Table 2 — Deterministic baseline performance**

Complete feasible solutions, number of vehicles, charging stops, travel distance, charging time, and runtime.

**Table 3 — Baseline stochastic reliability**

Mean and distribution of route-level reliability, fraction of exposed routes, customer violation frequencies, and depot-return violations.

**Table 4 — Reliability by benchmark family and time-window variant**

Include all-route and charging-exposed analyses separately.

**Table 5 — Charging-repair opportunity probe**

Number of tested routes, available alternative charging plans, observed reliability gains, and additional operating-time cost.

**Table 6 — Numerical and implementation validation**

Tests passed, reference checks, analytical versus simulated probability comparisons, and source parity results.

Tables should use consistent decimal precision and appropriate units.

Use `N/A` for genuinely inapplicable comparisons.

Do not replace missing results with zero.

Do not average conditional costs across methods covering different sets of routes without an explicit qualification.

---

# 12. SOFTWARE ARCHITECTURE

Create a clean, modular, research-grade Python project.

Use the following structure as a guide; adjust only where there is a clear engineering reason.

```text
STaR_EVRP/
│
├── dataset/
│   └── ... user-supplied original dataset ...
│
├── configs/
│   ├── default.yaml
│   ├── pilot.yaml
│   └── experiment_splits.yaml
│
├── src/
│   └── star_evrp/
│       ├── __init__.py
│       ├── types.py
│       ├── data_loader.py
│       ├── data_validation.py
│       ├── geometry.py
│       ├── baseline.py
│       ├── route_validator.py
│       ├── deterministic_simulator.py
│       ├── stochastic_simulator.py
│       ├── risk_bounds.py
│       ├── repair_probe.py
│       ├── statistics.py
│       ├── experiment_runner.py
│       ├── results_io.py
│       ├── plotting.py
│       └── cli.py
│
├── tests/
│   ├── test_data_loader.py
│   ├── test_data_validation.py
│   ├── test_deterministic_simulator.py
│   ├── test_stochastic_simulator.py
│   ├── test_battery_feasibility.py
│   ├── test_time_windows.py
│   ├── test_lognormal_waits.py
│   ├── test_risk_bounds.py
│   ├── test_baseline.py
│   ├── test_reproducibility.py
│   └── test_repair_probe.py
│
├── scripts/
│   ├── inspect_dataset.py
│   ├── generate_baselines.py
│   ├── run_pilot.py
│   ├── run_repair_probe.py
│   ├── generate_figures.py
│   ├── generate_tables.py
│   └── audit_results.py
│
├── results/
│   ├── manifests/
│   ├── baselines/
│   ├── raw/
│   ├── processed/
│   ├── figures/
│   ├── tables/
│   └── reports/
│
├── docs/
│   ├── DATASET_AUDIT.md
│   ├── MATHEMATICAL_MODEL.md
│   ├── BASELINE_REPRODUCTION.md
│   ├── SIMULATION_CONTRACT.md
│   ├── SAFE_SCREENING_MATHEMATICS.md
│   ├── EXPERIMENT_PROTOCOL.md
│   ├── FIGURE_INDEX.md
│   ├── LIMITATIONS.md
│   └── PHASE1_FINAL_REPORT.md
│
├── pyproject.toml
├── requirements.txt
├── README.md
└── .gitignore
```

Do not duplicate all routing logic across baseline, deterministic simulation, stochastic simulation, and validation.

Share stable data structures while keeping independent correctness checks possible.

Use type hints, docstrings, clear error messages, and structured logs.

Support Python 3.11+.

Avoid unnecessary heavyweight dependencies.

Use sensible caching without allowing stale cached results to survive a changed configuration or dataset hash.

---

# 13. MANDATORY AUTOMATED TESTS

Implement actual executable tests, not test placeholders.

At minimum, verify the following:

1. Dataset parser correctly loads depot, customers, stations, and fleet parameters.
2. Station attributes are joined by station identifier correctly.
3. Invalid instance structures are rejected.
4. Zero-energy and negative-energy edge cases are handled.
5. Battery underflow is rejected.
6. Overcharging beyond battery capacity is rejected.
7. Customer time-window violations are detected.
8. Depot closing violations are detected.
9. Load-capacity violations are detected.
10. Missing or duplicate customers are detected at solution level.
11. Charging time follows \(q/r_s\).
12. Lognormal sampling reproduces analytical means and quantiles within statistical tolerance.
13. Zero extra waiting gives the same timing outcome as deterministic simulation.
14. Increasing a charging wait cannot make a previously violated downstream deadline feasible.
15. A route with no charging stations has deterministic reliability.
16. A one-station route agrees with its analytically calculated success probability.
17. The isolated-wait upper bound is valid in carefully constructed exact toy examples.
18. Numerical approximations do not cause unsafe rejection near the 95% threshold.
19. Random seeds produce reproducible results independent of processing order.
20. A and B instances from the same parent stay in the same development/holdout partition.
21. Repair-probe candidates preserve the original customer sequence.
22. Repair-probe candidates preserve energy and time feasibility.
23. Output tables can be regenerated from authoritative raw results.
24. Figure generation completes without errors.
25. Resuming an interrupted run does not duplicate or corrupt previous results.

Use synthetic miniature routes **only for unit testing**. They must never be mixed with official benchmark results.

Run the complete test suite and include the output in the final phase report.

---

# 14. REPRODUCIBILITY AND EXPERIMENT CONTROL

Implement a command-line interface or equivalent reliable scripts supporting:

```bash
python scripts/inspect_dataset.py
python scripts/generate_baselines.py --config configs/pilot.yaml
python scripts/run_pilot.py --config configs/pilot.yaml
python scripts/run_repair_probe.py --config configs/pilot.yaml
python scripts/generate_figures.py
python scripts/generate_tables.py
python scripts/audit_results.py
python -m pytest -q
```

These commands are required interface targets; implement them so they work from the project root.

The project must run on Windows and Linux without editing absolute paths.

Save:

- Python version.
- Relevant library versions.
- Operating system.
- CPU information.
- Random seeds.
- Dataset hashes.
- Git commit identifier, if available.
- Configuration file hash.
- Experiment timestamps.
- Per-instance runtime.
- Success and failure statuses.

Results must be restartable and auditable.

All figures and tables must be regenerated from saved experimental records, not manually copied numbers.

Never overwrite historical experiments without preserving provenance.

---

# 15. SCIENTIFIC HONESTY AND NOVELTY PROTECTION

These requirements are mandatory for conference publication quality.

Do not claim that:

- The dataset contains observed real-world charging queues.
- The waiting-time parameters were measured from Moroccan charging stations.
- The baseline routes are stochastic-feasible because they are deterministic-feasible.
- Monte Carlo estimates establish mathematical reliability guarantees.
- The safe upper bound certifies successful routes.
- The planned STaR algorithm already outperforms other methods.
- A reconstructed baseline exactly reproduces published CON/HC without proof.
- A route-level 95% reliability target guarantees 95% whole-fleet reliability.
- Charging-only repair solves the unrestricted EVRPTW.
- Every route without a found repair is mathematically impossible to repair.

The current stage is foundation and diagnostic research.

Only make claims supported by actual implementation, numerical output, and tests.

The following literature should inform the research context:

1. Hanif et al. (2026), EVRPTW Heterogeneous Charging-Station Dataset.  
   https://doi.org/10.3390/data11040083

2. Keskin, Çatay and Laporte, simulation-based EVRPTW with stochastic charging-station waits.  
   https://doi.org/10.1016/j.cor.2020.105060

3. Electric Vehicle Routing with Heterogeneous Charging Stations, *Computers & Operations Research*.  
   https://doi.org/10.1016/j.cor.2025.107374

4. Stochastic Dual Dynamic Programming for Fixed-Route EV Charging under Congestion Uncertainty.  
   https://doi.org/10.1177/03611981261476042

5. Intention-Aware Electric Vehicle Routing with Markovian Queuing.  
   https://doi.org/10.1049/itr2.70180

Do not copy their algorithms or make unsupported novelty comparisons.

---

# 16. FINAL SCIENTIFIC GATES

At the end of this first phase, evaluate three research gates.

## Gate G0 — Reproducible foundation

PASS only if:

- Dataset loading works.
- Routes can be generated or imported and independently validated.
- Stochastic simulation works.
- Correctness tests pass.
- Raw experimental output is reproducible.

If the baseline algorithm cannot reproduce the published figures exactly, document the discrepancy. Exact numerical parity is not required for G0 if the independently reconstructed baseline is transparent, correctly validated, and usable.

## Gate G1 — Meaningful stochastic risk

Determine:

- How many routes actually charge.
- How many charging-exposed routes fall below 95% reliability.
- Whether those failures are significant or negligible.
- Whether some benchmark families exhibit greater exposure.

Do not impose a favorable numerical result.

Classify the evidence as strong, limited, or insufficient.

## Gate G2 — Charging repair headroom

Determine whether the limited repair-opportunity probe finds feasible alternatives capable of improving reliability on meaningful numbers of routes.

Report the percentage of examined routes with improved alternatives and the associated time costs.

If a gate fails, explain why.

Do not conceal the failure or change the benchmark assumptions secretly.

If the original benchmark provides insufficient charging exposure or repairability at \(Q=700\), you may investigate other published battery settings, especially \(Q=600\), as **clearly labeled exploratory diagnostics**, but do not substitute them into the primary protocol without documenting the scientific reason and preserving the original \(Q=700\) results.

Do not use the holdout set to select a favorable battery capacity.

---

# 17. FINAL DELIVERABLES

Before ending, ensure the project contains the following completed deliverables.

### Working software

- Functional data-loading and validation package.
- Reproducible deterministic baseline generator/importer.
- Independent route-feasibility validator.
- Deterministic route simulator.
- Stochastic waiting-time simulator.
- Isolated-wait upper-bound calculation.
- Limited charging-repair opportunity probe.
- Working configuration system.
- Reproducible experiment runners.
- Automated tests.
- Clear documentation.

### Experimental results

- Complete dataset inventory.
- Development-instance baseline routes or explicit failed-case diagnostics.
- Per-route stochastic reliability results.
- Statistical confidence intervals.
- Charging-exposure analysis.
- Failure-mode analysis.
- Limited charging-repair opportunity analysis.
- Raw CSVs and structured source results.

### Figures

Produce all six requested scientific figures as publication-quality PNG files, generated exclusively from actual experimental results.

### Tables

Produce all six requested scientific tables in CSV, LaTeX, and Markdown.

### Reports

The main report:

`docs/PHASE1_FINAL_REPORT.md`

must contain:

1. Executive summary of actual completed work.
2. Dataset inventory and integrity status.
3. Deterministic baseline methodology and reproducibility.
4. Published-baseline parity assessment.
5. Model assumptions and simulation semantics.
6. Stochastic reliability findings.
7. Charging-exposure findings.
8. Repair-opportunity findings.
9. Mathematical screening validation.
10. Runtime and computational environment.
11. Figure and table inventory.
12. Statistical and scientific limitations.
13. G0, G1, and G2 decisions with evidence.
14. Exact instructions to reproduce every output.
15. Known unresolved problems, if any.
16. Specific recommendations for the STaR algorithm to be developed in Prompt 2.

Do not write a vague report such as "implementation successful" without actual numerical evidence.

Include real measured values and refer to the corresponding raw-result files.

---

# 18. NON-NEGOTIABLE COMPLETION INSTRUCTIONS

**YOU MUST COMPLETE THIS ENTIRE FIRST PHASE BEFORE STOPPING.**

Follow this execution sequence:

1. Inspect and understand the actual dataset.
2. Build the parser and validation infrastructure.
3. Implement deterministic baseline generation/import.
4. Validate deterministic routes independently.
5. Implement the stochastic simulator.
6. Implement statistical evaluation.
7. Implement and test the safe-risk bound.
8. Run smoke experiments.
9. Run the complete development pilot.
10. Run the limited repair-opportunity probe.
11. Generate all PNG figures.
12. Generate all paper-ready tables.
13. Run comprehensive automated tests.
14. Audit raw results and all reporting outputs.
15. Fix defects revealed by tests or experiments.
16. Write the final scientific report.
17. Verify that all required deliverables exist and can be reproduced.

Do not treat implementation alone as completion.

Do not treat a passing test suite without executed benchmark experiments as completion.

Do not treat generated figures without validated source data as completion.

If a scientifically important result is negative, preserve it honestly. Do not optimize the results through undisclosed dataset selection.

If the dataset is missing or inaccessible, do not substitute invented instances for the official experiments. Complete the code and synthetic correctness tests, state the missing-input blocker precisely, and identify the exact commands that remain unexecuted. Such a run must be reported as incomplete.

**Final response format after finishing the work:**

- State what was actually implemented and tested.
- Report the real G0/G1/G2 findings.
- Show the most important verified numerical results.
- List the produced PNG figures and tables.
- Identify any unresolved errors or limitations.
- Give exact reproduction commands.
- Explain whether the evidence supports proceeding to Prompt 2.

The guiding principle is:

**Build a scientifically correct foundation first. Strong conference-paper results must come from a valid model, a suitable dataset, fair evaluation, and a method that genuinely improves the measured outcomes—not from forcing positive results.**

BEGIN IMPLEMENTATION NOW. CONTINUE AUTONOMOUSLY UNTIL ALL FIRST-PHASE ACCEPTANCE CRITERIA HAVE BEEN COMPLETED OR AN EXPLICIT, DOCUMENTED EXTERNAL BLOCKER PREVENTS THEM.