# PROMPT 2 OF 3 — SCIENTIFIC REPAIR, ALGORITHM DEVELOPMENT, AND FAIR DEVELOPMENT-SET EXPERIMENTS

**Project:** STaR-EVRP — Slack-Targeted Stochastic Charging Repair for Large-Scale Electric Vehicle Routing with Time Windows  
**Actual repository/root:** `STaR-EVRP/` (GitHub: `ayoub-hanif-evrp/STaR-EVRP`)  
**Input dataset:** `dataset/EVRPTW_ChargingStations_Dataset/` under the project root  
**Authoritative Phase 1 source:** `prompts/PROMPT_01_FOUNDATION.md`, `docs/PHASE1_FINAL_REPORT.md`, Phase 1 raw route/solution JSON files.  
**This file must be stored as:** `prompts/PROMPT_02_ALGORITHM.md`.

## NON-NEGOTIABLE INSTRUCTION TO THE CODING AGENT

You are the lead operations-research algorithm engineer, numerical-computing engineer, and scientific validation lead. Your mission is to **correct scientifically material Phase 1 problems, implement a genuinely competitive charging-only stochastic-repair method, implement strong fair baselines, run full development-set experiments, and produce reproducible numerical evidence and paper-quality figures/tables.** Do not finish after scaffolding, partial code, a smoke test, an unvalidated claimed speedup, or a research proposal. **Keep working until every requirement and acceptance gate below has been completed and verified.** Diagnose and fix implementation errors. If a genuinely external blocker prevents a specific action, finish every independent requirement, document the precise blocker, and mark that action incomplete. Do not manufacture favorable data, relabel an unsuccessful outcome a success, weaken feasibility constraints, or open the confirmatory holdout for tuning.

You can reorganize modules as needed, but preserve Phase 1 artifacts with their original provenance. Do not overwrite original source datasets, frozen Phase 1 data, or Phase 1 experiments. Work on the existing repository rather than starting a parallel fresh project. Before changing any experiment semantics, record the baseline commit SHA and original model contract. The eventual manuscript must compare methods under *identical validated physics, stochastic assumptions, dataset splits, and computational budgets*.

---

## 0. AUDIT FINDINGS — REQUIRED CORRECTIONS BEFORE ANY NEW RESEARCH CLAIM

The following findings are grounded in a review of the current GitHub `main` code and Phase 1 outputs at commit `39a49b12d86fc4f4bfb7966ae1c36bf624ca8212`. Reinspect HEAD first: do not blindly apply changes that are already fixed. The repo reports 24/24 feasible development baselines, 1,742 routes (570 charging-exposed), 197 exposed routes with estimated reliability below 95%, a preliminary probe on 40 routes, six PNG figures, and 41 passing tests. **These are repository-reported results; independently re-run and audit them before treating them as publication-ready.**

### P0-A — The purported safe bound is not yet numerically safe

`src/star_evrp/risk_bounds.py::isolated_wait_threshold` returns the **feasible lower bisection endpoint** `lo`, with default absolute tolerance `1.0`. If the true maximum isolated wait is `tau*`, then `lo <= tau*` and consequently `F(lo) <= F(tau*)`. Thus `F(lo)` is NOT necessarily an upper bound on the relevant event probability and can falsely reject a feasible candidate when the target is close to 0.95. The Phase 1 documentation mistakenly describes downward rounding as conservative for an **upper** reliability bound. Fix this before using the screen as a proof or optimization shortcut.

Required repair: compute a mathematically justified **upper bracket** for each `tau*`, ensuring `tau* <= tau_upper`, then form `U = min_j F_j(tau_upper[j])` (and, under independent visit waits, optionally the tighter `U_indep = prod_j F_j(tau_upper[j])`). On a monotone feasible/infeasible bisection, maintain an infeasible upper bracket and return it; if the search reaches a cap without finding infeasibility, set the corresponding upper bound to `+infinity` (CDF=1) rather than pretending the cap is an upper threshold. Include small outward numerical slack, explicit handling of the deadline boundary and deterministic infeasibility, `sigma=0` point-mass cases, and a tolerance test focused specifically on decisions near 0.95. If the upper-bracket proof cannot be established under a particular simulator configuration, **disable certified rejection for that configuration**, label it heuristic screening, and keep candidates eligible for full evaluation.

Create `docs/PHASE2_SAFE_BOUND_PROOF.md` with the event containment proof, monotonicity assumptions, float-rounding policy, independent versus dependence-robust bounds, and property-based/tiny exact tests. The bound is a **necessary-condition rejection test**, never an acceptance certificate. Run direct numerical counterexamples against the old code and demonstrate the fix.

### P0-B — Overcharge and malformed charging quantities can be silently accepted

`src/star_evrp/deterministic_simulator.py::_charge_at_station` performs `battery_after = min(Q, battery + energy_added)` then tests whether `battery_after > Q`; this check can never trigger. Negative proposed charging amounts are also clamped silently to zero. `src/star_evrp/stochastic_simulator.py::_fast_time_outcome` similarly clips energy to Q. Repair both and the route validator: **reject** NaN/inf, negative or otherwise invalid charges, station charging outside battery capacity, invalid charging rates, battery underflow, non-depot starts or ends, invalid node visits, and mismatches between `customer_indices` and customers actually listed in `stops`. A stop with `None` means full recharge; an explicit amount means exactly that physical energy added, never a clipped approximation. Invalid candidates must never appear as feasible.

### P0-C — Stochastic completion and tardiness measurements are biased by early termination

`src/star_evrp/stochastic_simulator.py::_fast_time_outcome` stops at the **first** failed customer window/depot condition. That can make `e_completion`, `p95_completion`, customer-on-time proportions, and tardiness reflect a truncated prefix rather than the *actual route finishing time*. It can also hide simultaneous customer and depot violations, making failure-mode reports ambiguous. Develop a correct full-route replay that, for an energy-valid plan, **continues propagating time to the actual final depot even after late customers**. Record all missed customer deadlines, first-failure time separately, actual depot return time, mean/max tardiness over ALL served customers, fraction of customers on time, and whether any customer/depot deadline was missed. Provide separate structural invalidity indicators; do not keep propagating an impossible battery path as though it were a valid physical route. Unit-test a route that is late early but finishes much later to show the old code underestimated completion. Recompute all affected Phase 1 summaries after patching, **under a new Phase 2 audit directory**; preserve the originals and write a documented old/new numerical crosswalk.

### P0-D — The original stochastic fast path and deterministic path must share the same model

The fast stochastic evaluator ignores the `SimulatorConfig.enforce_station_time_windows` flag, and stops/charging semantics can diverge. Establish one authoritative event and energy semantics contract (travel, station ready wait if enabled, sampled exogenous wait, charge, customer early wait/service, depot closing). Provide a reliable reference full replay and an optimized fast implementation with matched event ordering. Differential-test both for thousands of randomized small routes/scenarios and for sampled official routes. Ensure fast evaluation matches reference within specified tolerances on success/failure, times, battery feasibility, and all statistics. Use the published convention `station TW enforcement off` as the primary benchmark **only if verified against the deposited solver**, and label any alternative station-window enforcement a separate sensitivity, not an unannounced correction.

### P0-E — Existing probe outcome counts and comparisons are not sufficiently rigorous

`src/star_evrp/repair_probe.py` reports `candidates_improving_reliability` and `candidates_meeting_target` as **candidate counts**, not the numbers of distinct routes repaired. Its current stochastic comparison uses unmatched/reseeded streams for replacement candidates; the probe also makes route selection from a separate 200-scenario estimate and often only probes Variant A due to traversal order and global budget. Recalculate: attempted candidates, deterministically valid candidates, distinct routes with any feasible alternative, distinct routes improved, distinct routes with a selected policy meeting target on independent scenarios, plus corresponding paired cost changes and uncertainty. Use fixed development route selection and matched standard-normal shocks (see CRN below). Do not cite “17 repaired routes” based on 17 candidates. Make A/B coverage balanced in development sampling, with route selection fixed independently of observed improvements. Preserve original raw probe files.

### P0-F — Better auditing and scientific reporting

`src/star_evrp/experiment_runner.py::classify_failure_mode` currently uses an arbitrary `lo >= target - 0.02` rule to label high reliability. Replace with explicit classifications such as `proven_above_by_one_sided_CI`, `proven_below_by_one_sided_CI`, and `uncertain`; list the confidence level and sample size. Completion-time comparisons must never reward a route for failing early. The raw reporting table is overly sparse on stage-specific counts and uncertainty. The existing LaTeX table renderer joins labels without escaping underscores or special characters; implement valid manuscript-ready `.tex` output with escaped labels and `booktabs` style, and compile a small standalone LaTeX example if available. Audit the claimed 41 tests by executing them, not reading only `pytest_summary.txt`.

P0 gate: do **not** build on or publish the old “safe rejection” and truncated-cost calculations without fixing/revalidating them.

---

## 1. LOCK THE OPTIMIZATION PROBLEM

**Primary family:** official 2026 Hanif et al. heterogeneous charging EVRPTW dataset, 1,000 customers per instance; official original and relaxed time-window variants A/B, six families C1/C2/R1/R2/RC1/RC2. **Primary battery** Q=700, consumption h=1 in the source's native units, linear charging with station-specific rates, stochastic lognormal waiting times with published `wait_mu`/`wait_sigma` and independent visit shocks. Keep the original customer order, depot, number of vehicles, customer-to-vehicle assignment, and all customer windows unchanged. Charging stops (including insertion/removal/replacement/relocation) and quantities may change.

For fixed customer sequence `r` and a charging plan `p`, define `success(p, W)=1` iff its valid full-route execution respects every customer latest-service-start deadline and final depot return deadline. All plans must be strictly deterministic-energy/load/route feasible. Let `R(p) = P(success(p,W)=1)` and `C(p)=E[T_return(p,W)]` using **full-route completion even when late**. Formal target: minimize `C(p)` among valid plans with `R(p) >= 0.95`; if none is found in the prescribed budget, return the best reliable-improvement candidate flagged **below target** and do not call it chance-feasible. Keep operational success probability, expected completion time, distance, charging time, wait time, charge amounts, number of stations and time-window lateness as separate metrics; prices are out of scope for the primary objective.

A computational search cannot generally prove the true 95% chance constraint solely with Monte Carlo. Distinguish: `sample-feasible` under optimization scenarios, `empirically validated` under independent scenarios, `one-sided statistical lower-confidence-bound >= 0.95`, and `analytically proven impossible` under sound necessary-condition screening. Never conflate those labels. A failed/missed chance constraint must not be offset by lower cost in the primary comparison. Use an **explicit, common lexicographic incumbent policy**: first deterministic validity; then reaching the target on the optimization estimate (with a prespecified conservatism margin), then minimizing estimated expected completion; when no target-reaching candidate exists, maximize estimated reliability, tie-break on expected completion. Expose alternative scalar scores only as controlled ablations.

**Fairness:** all methods start from the exact same fixed customer route, use the same source benchmark physics, consume the same wall-clock budget and/or charge-evaluation budget, and are evaluated on identical independent scenario tapes. No method may reorder customers or borrow information about future sampled waits. A charging policy chooses a fixed offline schedule; no adaptive after-realization rerouting or forecast updates in the primary study.

---

## 2. BUILD CORRECT, FAST, REPRODUCIBLE STOCHASTIC EVALUATION

1. Add a **route/scenario evaluation interface** with immutable route plans, validated charge amounts, and explicit policy IDs; no hidden mutable global RNG state.
2. Generate *standard-normal* scenario tapes `Z` using stable `hashlib`/NumPy seed sequences derived from (`master_seed`, `parent_instance`, `variant`, `route_id`, `scenario_split`). For a given scenario and planned charging visit slot, transform `W_s = exp(mu_s + sigma_s Z)`. **Never compare different station candidates by feeding the same absolute waiting times; share Z, not W.** For replacement, preserve the relevant slot ID; for insertion/deletion, define an unambiguous stable slot/mapping rule and test matched marginal distributions. Permuting evaluation order must not change results. Keep separate development optimization, development independent validation, and Phase 3 holdout test streams.
3. Reuse scenario tapes/cached fixed-route geometry and energy prefixes. Vectorize over scenarios or use tested JIT compilation if it genuinely speeds execution; provide a reference Python implementation to validate all optimizations.
4. Provide progressive candidate evaluation stages configurable, e.g. 64 → 256 → 1,024 scenario replications, with hard per-route and per-instance maximum budgets and final independent `N=5,000` on development. Intermediate sample sizes may be calibrated **only on development** and must be explicitly recorded. Do not stop evaluation of an uncertain candidate based on invalid independent-binomial assumptions after arbitrary adaptive peeking; if using sequential confidence rules, implement a valid spending schedule or treat stages as heuristic screening only.
5. Compute one-sided confidence intervals correctly (Wilson/Clopper-Pearson with documented confidence level); for multiple candidate comparisons, avoid claiming simultaneous guarantees unless adjusted. The statistical reliability classification of a final selected route must be evaluated using **independent validation scenarios not used for selecting it**.
6. Handle deterministic and `sigma=0` distributions exactly. Ensure `N>=1`, `0<=target<=1`, finite parameters. Assert distribution/independence assumptions.
7. Add optional *robustness-only* correlated shock generation in the development experiments (e.g. a shared Gaussian factor plus visit-specific residuals, preserving each marginal standard normal); document it as hypothetical dependence, not observed station congestion and not a rerouting scenario.
8. Record scenarios evaluated, stochastic runtime, deterministic-check runtime, safe-bound runtime, number of candidates, candidate selection stage, cache hits/misses and timeouts for each method.

---

## 3. ENGINEER THE MAIN STaR OPTIMIZATION METHOD

Implement an actual, testable optimization method — not a new name for the earlier 5-nearest-station probe. It must be computationally practical for **route-by-route repair embedded in 1,000-customer instances**, including difficult R2/RC2 routes. Name the implemented version `STaR_v1`; do not promise mathematical optimality.

### 3.1 Candidate generation and energy feasibility

Keep the ordered list of customers fixed. Implement these local changes to charging visits:

- `replace`: replace a station stop with an alternative station between the same neighboring nonstation stops; consider geographically close stations **and** competitive low-wait/high-rate stations reachable under battery constraints.
- `remove`: remove redundant charging stop(s) if the full route remains energy feasible.
- `insert`: add a charging visit between consecutive existing stops (including adjacent customer/customer, customer/depot and depot/customer gaps), re-evaluating all subsequent battery states.
- `relocate`: remove one station and reinsert it at a different legal gap while preserving customer order.
- `charge_amount`: adjust existing or new charging quantities, including feasible partial recharging rather than only full charges.
- `two-edit` or bounded beam/large neighborhood: allow a combination of up to two charging edits, because one-step station replacement may be insufficient in R2/RC2. Bound the search and record each applied move.

Avoid blind full 333-station scans per candidate: use spatial/geometric candidate lists, energy reachability, rate/wait-tail attributes and latest-start time slack. Index stations for efficient lookup. Ensure searches do not cycle (tabu/fingerprint or strict incumbent logic). Deduplicate identical physical plans. Reject zero-charge detours unless there is a source-justified reason (normally remove them). Route charges must obey energy availability; re-simulate exactly after every modification.

**Partial-charge candidate strategy:** for linear charging, generate physically meaningful energy amounts based on (a) minimum charge to reach the next target or charging opportunity with a small numerical reserve, (b) a few discretized intermediate targets, and (c) full charge. Include a bounded charge-quantity refinement step using a one-dimensional search or mathematical feasibility intervals when valid. Avoid floating-grid explosions; do not claim exact quantity optimization without proof. For all variants retain the same energy/timing validation.

### 3.2 Safe rejection (must remain truly safe)

For each deterministically valid candidate, compute an upper bound `U>=R`. Under the stated independent per-visit lognormal model, the product of individual CDFs at **safe upper** isolated-wait thresholds is an upper bound: `R <= product_j F_j(tau_j_upper) <= min_j F_j(tau_j_upper)`. Include both independent-product and dependence-robust min versions, clearly label assumptions, and verify test cases. Use certified rejection only when `U < target` beyond documented numerical slack.

**Critical design rule:** a mathematically sound rejection of a candidate as **unable to meet 95%** does NOT imply it is useless for **improving reliability when no target-feasible plan has been found**. Do not discard all below-target candidates if the current route is highly unreliable (for example R2). Maintain two modes: (1) certified filter for searching target-feasible incumbents; (2) controlled *repairability/exploration* search that can retain and compare non-certifiable candidates based on estimated reliability improvement, without calling them certified. Report these two modes separately.

Reuse backward latest-allowable-time propagation, isolated waiting-time criticality `1 - F_j(tau_j_upper)` and downstream-window slack for prioritized neighborhoods where valid. Criticality is a prioritization score, not a causal contribution to the joint failure probability.

### 3.3 Targeted search and progressive simulation

Implement a budget-aware hybrid local search with clearly separated components:

1. Start from the unchanged benchmark charging plan (incumbent).
2. Analyze time-window slack and isolated-wait criticality.
3. Generate a restricted, diverse candidate pool (geometric, low-wait, fast-charge, partial-charge, multi-edit).
4. Run cheap structural, energy and deterministic deadline checks.
5. Apply mathematically safe stochastic infeasibility rejection where its meaning is appropriate (see above).
6. Rank survivors using a cheap, documented estimate (e.g. expected wait plus charging/travel time, available slack, upper-bound criticality). Use no black-box training.
7. Apply progressive scenario batches under a strict common budget and matched scenario tapes.
8. Update elite/archive of nondominated `(estimated reliability, expected completion)` plans, tracking validity and uncertainty; do not use incorrectly truncated costs.
9. Intensify around high-potential plans using bounded two-edit/charge-amount search; keep a diversification option to escape local traps.
10. Independently validate selected final plans on unused development scenarios, saving the full route and results.

Treat the above as the minimum design. You may choose a more elegant data structure/algorithm, but do not silently omit a required move type or the strong comparisons. Use profiling, not guesswork, to optimize bottlenecks.

### 3.4 Hard computation limits and robust stopping

Implement deterministic, configurable per-route caps for seconds, candidate evaluations and total scenario evaluations, plus per-instance caps. Stop safely at the limit, return the best **valid** incumbent, and log deadline overtime. No method may run with hidden extra optimization budget. Persist checkpoints/restart state without contaminating random streams or mixing configurations.

---

## 4. STRONG BASELINES — MUST BE FAIR, NOT STRAW MEN

Implement all baselines on the **same fixed customer order, exact same move neighborhood, physically correct simulator, scenario distribution, and primary computational budget**:

- **B0: NoRepair-CON.** Existing deterministic CON charging plan, evaluated under stochastic waits. Include optional deposited HC as a *separately labeled* alternative construction seed/reference (not an apples-to-oranges competitor with a different customer sequence).
- **B1: MeanWait-Greedy.** Candidate charging edits scored using station arithmetic mean waits and full deterministic time propagation, then independent stochastic validation.
- **B2: UniformQuantile.** Uniformly allocated per-charge risk budget plus true route deadline propagation; distinguish analytical feasibility from empirical outcomes and allow the **same** moves as other methods.
- **B3: FullScenario-LS.** Strong stochastic local search using the **same candidate edit types** as STaR, direct fixed-batch Monte Carlo scoring, unbiased completion costs, equal wall-clock/candidate budgets, multiple restarts and incumbent protection.
- **B4: SimulationGuided-ALNS-Lite (if implementable fairly).** Bounded destroy/repair charging edits, empirical scenario scoring, and adaptive move selection, still keeping customer sequences fixed. This is an *adapted charging-only baseline inspired by simulation-based ALNS*, **not** a claimed exact reproduction of Keskin et al. (2021). If no fair meaningful ALNS can be implemented, document why and strengthen B3 with simulated annealing/tabu and two-edit moves rather than claiming a fake literature replication.
- **Proposed STaR_v1** and the ablations below.

Baselines must use the same search starting solution, budget, available move operators (or an explicitly documented difference attributable to the method), and independent validation. UniformQuantile is a supporting simple reference, **not** the sole comparison. Show **time-to-first target-reaching plan**, target-reaching routes, expected completion on **common target-reliable routes**, empirical reliability, runtime, scenario cost, and paired route-level differences. Never declare victory on a subset that excludes failures without explaining the selection bias.

---

## 5. REQUIRED ABLATIONS AND DECISIVE RESEARCH QUESTIONS

Implement at least:

- STaR-FULL.
- STaR without certified rejection.
- STaR without slack/criticality targeting (same candidate and evaluation budgets).
- STaR without progressive scenario evaluation (full batch only).
- STaR without partial-charge actions (station edits only).
- STaR without multi-edit/beam search (single edit only).
- STaR with dependence-robust min bound versus independence-product bound where appropriate.

Give each ablation the *same total wall-clock limit* and report the effective number of evaluations. Record percentage of candidates rejected, correct rejection rationale, distribution of bound slack, computational time spent in bounds, and whether rejected candidates would otherwise be required to reach a good improvement. For certified rejection, validity is mathematical, not empirical. Include a small empirical false-rejection audit as an additional sanity check, not a substitute for proof.

Research questions: **(RQ1)** reliability restoration at fixed customer sequence, **(RQ2)** expected-completion cost at matched reliability, **(RQ3)** computation to reach reliable plans, **(RQ4)** which component helps on R2/RC2, and **(RQ5)** effect of independent versus hypothetically correlated waits.

A successful method is NOT simply one that improves average reliability at any cost. It must establish a competitive reliability–time–computation trade-off against the scenario-based search baselines.

---

## 6. DEVELOPMENT EXPERIMENT PROTOCOL — HOLDOUT MUST REMAIN SEALED

**Use all 24 development instances** (12 frozen parent IDs × variants A/B) for method development; **do not read/use performance outputs from the other 96 held-out EVRPTW instances for optimization choices.** Keep the original frozen parent split intact. The primary Q=700/h=1 experiments must include all family/variant cells, including low-exposure C1 as a negative control and difficult R2/RC2 as stress cases. Charging-exposed routes, below-target routes, and all routes are distinct populations; report each. Avoid choosing only favorable routes/instances.

Recommended development stages:

**D1 — P0 correctness reconciliation.** Re-run Phase 1 baseline audit with fixed simulator/safe bound and publish changed counts, broken assumptions and preserved unchanged fields. Stop scientific interpretation until all math/energy/fast-versus-reference tests pass.

**D2 — Method smoke/pilot.** On fixed preselected development routes spanning family, variant, and reliability levels (include very unreliable R2/RC2 cases), verify each new move, baseline, budget and simulator. Benchmark no improvement as a valid negative outcome. Profile CPU time.

**D3 — Controlled development selection.** Choose parameters such as neighborhood size, beam width and batch sizes on development only; use route-parent grouped summaries, not per-scenario pseudo-replication. Record all tuning campaigns and select one frozen configuration before D4.

**D4 — Full development evaluation.** Compare final selected algorithm, baselines and key ablations on the complete eligible charging-exposed development population; zero-charge routes are pass-through controls. Use independent validation scenarios (default 5,000 per selected plan on development, increase for near-threshold uncertainty as allowed by the frozen budget). Use paired common-random-number evaluation. Run enough independent random algorithm seeds (at least three for stochastic search, preferably five where compute allows), but avoid interpreting repeated seeds/variants as independent parent instances. For expensive ablations, a predeclared balanced panel is acceptable if every method uses the same panel; include full development for main comparisons.

**D5 — Freeze for Phase 3.** Lock algorithm, configurations, all decision thresholds, baselines, figure code, and evaluation scripts. Write a manifest with git SHA, input hashes, scenario seed streams and expected holdout experiment entry point. Do **not** launch the Phase 3 holdout now.

### Decision / reliability rules

- Target: 0.95 route success probability under the specified model.
- Development search may use an explicitly documented sample-based reliability proxy.
- For **publication-grade claims that a selected plan meets target**, use a one-sided independent test confidence lower bound at a declared confidence level. If the estimate is near 95% and the lower bound does not exceed 95%, classify **uncertain/not certified**, not successful. If the method only achieves a high point estimate, label it empirical and provide interval.
- Zero-charge routes are never counted as repaired; include them in all-route service summaries only.
- Improvement is measured per **original baseline route**. Count one route at most once when reporting `routes_improved` and `routes_meeting_target`, even if it had 100 improving candidate plans.
- For expected completion costs, use full stochastic completion for all scenarios; report cost on common independently reliable cases, along with target-attainment and unconditional reliability differences. Do not rank mean cost from differing feasible sets without qualifying it.
- Prefer paired parent-level bootstrap intervals or hierarchical/cluster bootstrap with parent as resampling unit. Clearly distinguish nested routes and A/B variants within a parent; separate method-seed variability from parent-instance variability.
- If a method cannot reach target reliably on R2, report relative reliability improvements and nonattainment rather than quietly dropping R2.

---

## 7. DELIVERABLE FIGURES — STRICTLY PNG, REAL DATA ONLY

Generate **at least eight** clean publication-quality PNG figures (>=300 dpi, 400 dpi preferred; vector source formats not requested; do not output SVG/PDF/JPEG figures). Use one consistent accessible palette, publication-column readable axes, descriptive units and denominators, unambiguous confidence bars, no clipped labels, and source CSV traceability:

1. `fig07_before_after_route_reliability.png`: baseline versus selected STaR per route on exposure/repair-eligible development routes; show targets, pairing, failure cases.
2. `fig08_target_attainment_by_method.png`: distinct original routes meeting 95% with independent uncertainty qualification, by family and variant; distinguish estimate-only versus lower-bound-certified.
3. `fig09_reliability_cost_pareto.png`: reliability versus **full-route** expected completion cost; display method and common route panels, not unequal-denominator misleading averages.
4. `fig10_time_to_target.png`: fraction of routes finding a target-reaching candidate versus optimization wall-clock budget, with no-attainment cases shown.
5. `fig11_computation_efficiency.png`: full stochastic evaluations, total scenarios, screening overhead, and wall time by method.
6. `fig12_stochastic_completion_distributions.png`: calibrated before/after completion-time distributions on representative fixed, predeclared example routes (including challenging R2).
7. `fig13_component_ablation.png`: paired changes from each ablation, including reliability, attainment and runtime, with uncertainty.
8. `fig14_family_stress_and_repairability.png`: C1/C2/R1/R2/RC1/RC2 comparison including exposure and target-attainment denominators.
9. `fig15_safe_screen_diagnostics.png`: true safe upper bound distribution, candidates filtered, time saved, and screening effect; optional two panels.
10. `fig16_partial_charging_mechanism.png`: energy, charging amount and downstream slack before/after selected partial-charge repair (clearly labeled illustrative case drawn from benchmark data).

If fewer than ten figures are scientifically informative, generate the eight strongest and document why some are not warranted. Do not invent positive effects merely to populate a plot. Regenerate every figure from frozen raw records with one command, and write `docs/PHASE2_FIGURE_INDEX.md` with source CSV, caption, interpretation and limits.

---

## 8. PAPER-READY TABLES AND RESULT INTEGRITY

Save authoritative per-route/per-candidate JSON/Parquet/CSV with stable IDs and full configuration manifests. Generate `.csv`, `.md`, and syntactically valid escaped `.tex` tables; no manually typed result numbers.

At least:

- `table07_phase1_corrections`: before/after correctness, which Phase 1 statistics changed and why.
- `table08_method_main_comparison`: original-route denominator, target attainment with confidence qualifier, mean reliability, full expected completion, distance, charges, runtime and scenarios.
- `table09_family_variant_results`: all six families and A/B, counts and paired method outcomes.
- `table10_ablation_results`: component analysis at matched computational limits.
- `table11_screen_efficiency`: mathematical screen rejection rates and actual time/evaluation savings, including its own computational overhead.
- `table12_paired_statistical_analysis`: mean/median paired changes, confidence intervals and valid clustering unit.
- `table13_partial_charging`: count of altered charging quantities, amount/time changes, benefit and any regressions.
- `table14_negative_cases`: methods and routes where target remained unmet, classification of reason and remaining challenge.

Also supply per-instance/per-route source tables, not just aggregated summaries. Provide a table/figure audit asserting all displayed summary values are derived from the frozen raw data and no missing scenario, infeasible plan or failed run was discarded silently.

---

## 9. CODE ORGANIZATION, PERFORMANCE AND TESTING

Refactor existing modules only as necessary; likely new additions under `src/star_evrp/`:

- `route_evaluator.py`, `scenario_tapes.py`, `charge_plan.py`, `charge_moves.py`, `safe_screen.py` (or corrected `risk_bounds.py`), `criticality.py`, `search_common.py`, `star_optimizer.py`, `baseline_optimizers.py`, `budget.py`, `experiment_phase2.py`, `analysis_phase2.py`.
- `configs/phase2_dev.yaml`, `configs/phase2_smoke.yaml`, `configs/phase2_ablation.yaml`.
- `scripts/run_phase2_smoke.py`, `scripts/run_phase2_development.py`, `scripts/run_phase2_ablations.py`, `scripts/build_phase2_figures.py`, `scripts/build_phase2_tables.py`, `scripts/audit_phase2_results.py`.
- `results/phase2/{manifests,raw,processed,figures,tables,reports}/` to avoid overwriting Phase 1.
- `docs/PHASE2_METHOD.md`, `docs/PHASE2_CORRECTIONS.md`, `docs/PHASE2_EXPERIMENT_PROTOCOL.md`, `docs/PHASE2_FINAL_REPORT.md`, `docs/PHASE2_READINESS.md`.

Every route/candidate evaluation must validate the same physical plan under identical settings. Cache route geometry, battery prefixes, station attributes and scenario draws keyed by fingerprint/seed/config. Cache invalidation must include baseline SHA, dataset hashes, Q/h, simulator semantics and method version. Thread/process scheduling may not change RNG results. Benchmark optimization speed on both ordinary and difficult routes; keep reproducibility ahead of micro-optimizations.

MANDATORY tests, above and beyond all Phase 1 tests:

- A charge amount greater than `Q - E_arrival` is rejected (not clipped), negative/non-finite charges rejected.
- A route with invalid final depot or inconsistent `customer_indices` cannot be accepted.
- A customer who becomes late early in a scenario is still included in **full** end-of-route timing and tardiness metrics; late depot can coexist with late customer.
- Fast and reference simulators agree with/without station-window enforcement and for zero/one/multiple stations.
- `sigma=0` and extreme `mu/sigma` are handled without NaN or wrong probability classifications.
- Bound uses an **upper** threshold bracket; demonstrate an explicit near-95% counterexample where the old lower bracket can falsely reject, and verify new code never does.
- Independent-product bound never exceeds the min-CDF bound; both are above true reliability in all small cases with known exact probability.
- For 1-station toy, analytic route success matches MC within sampling error and necessary-condition bound is conservative.
- Insert/remove/replace/relocate/partial-charge/two-edit preserve customer order and physical validity or are rejected.
- Removing a charging station changes scenario slots correctly, without leaking unrelated RNG values.
- Candidate order, caching and resume do not change seeded results.
- When a candidate is structurally invalid, it cannot be rescued by stochastic success.
- Target-unattainable routes return an explicit nonattainment incumbent, not a false success.
- All methods respect configured time/scenario limits, including evaluation overruns, and return best valid incumbent.
- Same route, same scenario tape, same policy yields identical outcomes across every method's evaluation code.
- Full results summary and all `.tex`/PNG files can be regenerated from raw records; no Phase 3 holdout results created.

Run the existing and new test suite on the actual working environment, save test logs and profiling evidence. Add an independent randomized property/differential test campaign; treat numerical warnings as errors where possible. Document any remaining unresolved divergences.

---

## 10. PHASE 2 ACCEPTANCE GATES — NO CLAIM OF SUCCESS WITHOUT EVIDENCE

**P2-G0 (correctness) — mandatory before any scientific optimization result:** the safe bound is proven and numerically conservative; simulator and independent reference replay agree; overcharging/negative amounts are rejected; all relevant tests pass; Phase 1 corrections are reported. Failure here makes the research results invalid and must be fixed first.

**P2-G1 (method completeness):** STaR-v1 and all feasible baseline methods actually run on benchmark charging-exposed routes with fixed customer order, bounded computation, deterministic/physical validation, correct stochastic evaluator and reproducible outputs.

**P2-G2 (development evidence):** complete main comparison on all eligible development charging-exposed routes (or a fully disclosed, justified budget-limited balanced sample), independent validation, route/parent-level statistics, negative cases, component ablations, scenario counts and time-to-target. Do not assert superiority unless paired evidence supports it. Performance improvement is a research hypothesis, not a requirement to fabricate positive results.

**P2-G3 (paper presentation):** at least eight genuine 300+ dpi PNG figures, eight paper-ready table families in CSV/MD/TeX, consistent figure/table audits, complete final method and limitations reports. Every figure/table must be sourced from raw, verified experiments and show failures or zero improvements transparently.

**P2-G4 (Phase 3 readiness):** selected configuration and evaluation code frozen; Phase 3 holdout sealed; full reproducible commands saved; all supporting manifests and tests retained.

If a method does not outperform FullScenario-LS on development, explicitly diagnose why (screening overhead, insufficient moves, conservative filtering, partial charge issue, stochastic uncertainty, low-sample bias, etc.) and perform only prespecified development-set algorithm/debugging improvements; rerun fair baselines. **Do not search for a favorable paper result by secretly loosening chance constraints, excluding hard routes, weakening baselines or testing the holdout.** A credible negative finding is preferable to invalid statistics.

---

## 11. REQUIRED EXECUTION COMMANDS AND FINAL REPORT

Implement and demonstrate (from repository root, on Windows/Linux after `pip install -e .`):

```bash
python -m pytest -q
python scripts/run_phase2_smoke.py --config configs/phase2_smoke.yaml
python scripts/run_phase2_development.py --config configs/phase2_dev.yaml
python scripts/run_phase2_ablations.py --config configs/phase2_ablation.yaml
python scripts/build_phase2_figures.py
python scripts/build_phase2_tables.py
python scripts/audit_phase2_results.py
```

For every command produce meaningful exit status, structured logs, error messages, documented restart/resume behavior, and a real proof-of-execution result file. Do not claim a fresh run based solely on an old log. Do not rerun lengthy completed jobs when a checksum-valid cached artifact exists.

`docs/PHASE2_FINAL_REPORT.md` must provide:

1. Head SHA, environment, validated dataset and frozen split.
2. A point-by-point status for P0-A through P0-F, with old/new results and test evidence.
3. Final mathematical model and exact solver search/move semantics.
4. Detailed algorithm pseudocode, budget accounting, safe screen proof and limitations.
5. Baselines, same-start/same-neighborhood/same-budget fairness controls.
6. All development results including distinct target-reaching routes, empirical reliability with confidence qualification, expected full completion costs, total scenarios, runtime, and negative results.
7. Paired statistical estimates with clustering details and family/variant stratification.
8. Mechanistic ablations and computational profiling, including when screening harms performance.
9. Tables and all PNG paths with readable manuscript captions.
10. Exact reproducing commands, raw data/manifests and reproducibility checks.
11. P2-G0 through P2-G4 PASS/PARTIAL/FAIL with honest rationale.
12. Frozen Phase 3 holdout execution specification, **without performing the holdout**.
13. A concise evidence-based recommendation about whether the method merits a full conference-paper study.

**DO NOT STOP until every relevant P0 correction, implementation, development experiment, strong baseline comparison, ablation, test, PNG figure, table, audit and final report above has been completed.** If a hard resource/external blocker makes part impossible, finish all possible work, mark only that part explicitly blocked, and do not claim a complete phase. Continue autonomously, fix errors, and preserve scientific honesty. **BEGIN PHASE 2 NOW.**
