# PROMPT 3 OF 3 — STaR-EVRP: FROZEN CONFIRMATORY HOLDOUT AND CONFERENCE-PAPER PACKAGE

**Existing repository:** `https://github.com/ayoub-hanif-evrp/STaR-EVRP`  
**Project root:** `STaR-EVRP/` — do not create another project  
**Dataset root:** the existing `dataset/` directory — never alter source data  
**Status on entry:** Phase 2.5 concluded **CONDITIONAL GO**. The 96 holdout instances have not been evaluated.  
**Research model:** Fixed customer order and vehicle assignment; optimize charging stops and charging amounts under published independent lognormal station waits; `Q=700`, `h=1`, target 95% route-level success; depot and customer time-window constraints; station time windows disabled for the primary source-compatible protocol.

## YOUR NON-NEGOTIABLE EXECUTION CONTRACT

**DO NOT STOP UNTIL ALL REQUIREMENTS AND ACCEPTANCE GATES IN THIS PROMPT HAVE BEEN COMPLETED, EXECUTED, TESTED, AUDITED AND DOCUMENTED.** Work autonomously, diagnose and repair normal execution failures, and keep a resumable progress checklist. Do not stop after writing scripts, producing figures, or running smoke tests; complete the entire confirmatory benchmark if the frozen implementation can execute it. Do not ask for routine approvals. If a genuine external blocker occurs, finish all independent work and state which mandatory experiments could not run. Never fabricate observations, infer missing results, or report a passing gate without evidence.

**MOST IMPORTANT SCIENTIFIC RULE: NO POST-HOLDOUT TUNING.** Before reading any holdout-performance outcome, freeze and commit source code, configurations, tests, model-selection decisions, primary comparisons, seeds, analysis scripts and stopping rules. Once any holdout outcomes are inspected, do not revise the method or comparator to make the results better. If a genuine correctness defect requires a fix, retain immutable pre-fix results and report the affected study as exploratory or otherwise clearly qualified; do not silently turn a rerun into a new pristine confirmatory trial.

## 1. RECONCILE THE ACTUAL PHASE 2.5 STATE — BEFORE ANY HOLDOUT RUN

Read the repository's actual current source files, `docs/PHASE25_FINAL_REPORT.md`, `docs/PHASE25_CORRECTIONS.md`, `docs/PHASE25_METHOD_COMPARISON.md`, `docs/PHASE3_FREEZE_PROTOCOL.md`, saved Phase 2.5 experiments and tests. Read the prior Phase 1/2 reports for historical context and the original dataset's readme/code for model semantics.

The previous coding agent reported:

- Development universe: **570 charging-exposed routes** from the **24 development instances**, not the 127-route pilot panel.
- At the **64-plan cap**, STaR versus partial-charge-only B4 improved mean independent validation reliability by **1.97 percentage points** (parent-bootstrap 95% interval **0.44–3.88**), achieved the target on **530 vs 517** routes, and reduced mean full-route completion by **33.2 native benchmark time units**; B4 ran faster.
- Compared to B3, STaR used **34% fewer search scenarios**, but ran **10% slower** and attained the target on **530 vs 531** routes. Therefore do not claim general speed or reliability superiority over B3.
- **15,960 saved plans** independently revalidated; **11,970 count-budget searches** reproduced; **58 tests** passed; ten 400-DPI PNGs produced.
- The 40-ms experiment used a **cooperative** cutoff, not a strict process time limit.

**These statements are hypotheses to verify against local saved records**, not a substitute for inspecting code. Record the actual numbers that are reproduced; if the repository differs, document discrepancies. Some earlier public commits predate Phase 2.5. Ensure the Phase 2.5 work is actually present, committed and pushed before proceeding. A bare report summary is not an adequate freeze.

Create a concise, machine-checkable `docs/PHASE3_PREFLIGHT.md` and `results/phase3/manifests/preflight.json` that verify: complete working tree and code revision; reconstructible plan files; test execution; independent simulator correctness; route identities and valid constraints; actual count caps; scenario-tape stability; corrected objective; correctly implemented B3/B4; parent-level statistics; corrected two-sided vs one-sided Wilson interval labeling; genuine Phase 2.5 PNG plots (not placeholders); dataset hashes; exact split manifest; correct current SHA, not an old Phase 1 SHA.

If any *scientifically material* defect persists, fix it **before** accessing the holdout. Re-run and report the necessary development tests, then freeze. Do not fabricate a successful preflight or proceed past a failing critical gate.

## 2. FREEZE THE CLAIMS AND EXPERIMENTS

Write an immutable, human-readable pre-registration at `docs/PHASE3_PRE_REGISTERED_ANALYSIS.md` and a machine-readable freeze file at `results/phase3/manifests/freeze.json`. Include SHA-256 hashes of executable code, configs, dependencies, frozen splits and source dataset files; Git commit hash; environment; OS and CPU; exact command lines; deterministic seeds and independent scenario streams.

**Primary experiment:** All eligible charging-exposed routes in the **48 holdout Homberger parent instances × two variants = 96 instances**, using the Phase 2.5 selected **64-unique-plan evaluation cap** (not 64 draw count), the exact finalized Phase 2.5 version of STaR, and the same starting CON routes and common physical constraints for all methods. Do not choose a favorable subset based on observed reliability. Preserve zero-charging routes in descriptive and coverage summaries, but exclude them from the predeclared charging-repair estimand.

**Primary scientific contrast:** STaR versus **B4 partial-charging-only**, on independently evaluated mean **route-level success probability**. Paired difference and parent-clustered 95% confidence interval are primary; predeclare weighting (route-weighted with parent-level clustered uncertainty, plus parent-balanced sensitivity). A positive confidence interval supports an incremental benefit from charging-topology edits beyond charge-quantity optimization. Also compare target attainment and expected full-route completion on paired routes, carefully separating reliable and unreliable outcomes.

**Key competitive contrast:** STaR versus **B3 scenario-based local search**. Evaluate route success, reliable-attainment counts, expected completion, wall-clock runtime and actual **incremental Monte Carlo scenario evaluations**. Predeclare that fewer scenarios is a *sample-efficiency* advantage, not a wall-clock speedup. The method does not establish general superiority if B3 attains similar outcomes faster.

**Contextual baselines:** B0 unrepaired CON and corrected B1/B2 if feasible; use the frozen, actually implemented definitions. Do not call B2 a quantile baseline unless it really uses the lognormal quantiles and its stated risk rule. Do not call B3 full-scenario ALNS unless it implements the claimed procedure; use honest names.

**Secondary experiments (predeclare, do not optimize from holdout):** The already frozen other count-budget profiles, independent-seed replications, family/variant heterogeneity, difficult R2/RC2 routes, paired runtime/quality trade-off, component ablations if run with pre-specified flags, and robustness to wait scale/variance or equicorrelated Gaussian-copula station waits. Robustness assumptions are synthetic stress tests, not real queue calibration; validate under a clearly stated joint model. Use saved final plans for robustness evaluation rather than retuning on stress test outcomes.

**No strict runtime claim from a cooperative time cutoff.** Strict process deadlines require separate enforceable supervision; otherwise explicitly label the metric cooperative budget and use measured elapsed time. Distinguish search time, deterministic candidate generation, screening, stochastic scenarios, final validation and plotting/reporting time. If an algorithm spends less on simulation but more on safe screening, account for both.

## 3. VALIDATION SEMANTICS AND REPLAY

The selected plan for EVERY method and eligible route must be saved as an exact, replayable ordered stop list: customer IDs, station IDs, locations of all station visits, exact charging quantities or full-charge sentinel, baseline customer sequence checksum, source hashes and configuration. Never use incomplete fingerprints as a substitute for selected plans. Independently replay and validate battery limits, customer TW, depot return, exact customer order, fleet/customer coverage at solution level, and station opening/closing semantics when enabled.

Use independent scenario tapes for optimization and **final holdout validation**, with common underlying normal variates where possible for matched comparisons. Stable nested MC prefixes and candidate-independent seed derivation are mandatory. Plan-dependent number of charging stops must not alter existing scenario prefixes unintentionally; document the coupling when station visits are inserted/deleted. Validate physical waits as `exp(mu_s + sigma_s * Z)` and keep station-specific marginals.

Choose a **predeclared validation scenario sample size** (prefer 10,000 or greater for near-threshold claims, subject to transparently reported feasibility). If reducing it for runtime, do so **before any holdout results are viewed** and document the reason. Measure empirical route success and Wilson uncertainty separately from the formal necessary-condition upper-bound screen. Label the exact confidence procedure: *two-sided* Wilson interval or mathematically correctly implemented one-sided lower bound. Do not claim that a Monte Carlo lower bound proves formal satisfaction for all distributions.

Report conditional expected route completion correctly: expected *full* completion over every scenario, not early-aborted completion. Avoid cost comparisons that favor unreliable plans just because they fail early. Also report reliability–completion Pareto trade-offs and matched-reliability comparisons; if no reliable candidate exists, show the best attainable reliability and failure reason rather than a fake feasible cost.

Preserve each run's selected route, reliability estimate, success count, validation draws, confidence interval, completion distribution summary, tardiness indicators, terminal-depot timing, determinism, runtime, scenario counts, candidates proposed/validated/evaluated/rejected, screen bounds, rejected reasons, and scenario stream identifier. Make the entire study restartable and idempotent. A file's existence alone must not count as completion; reject stale files whose hashes/config/method/replay schema differ.

## 4. PREHOLDOUT TEST GATE — NO EXCEPTIONS

Run the full reproducibility and correctness test suite after the code freeze. Include property-based or small exhaustive toy tests for route fingerprints, charge-amount feasibility, full-route completion, zero-charge deterministic routes, station-time-window modes, isolated-wait safe upper bound, CRN scenario prefixes, objective ordering below target, budget hard caps, no leakage, and replay reproducibility.

Audit (a) all relevant Phase 2.5 evidence, (b) exact version of B3/B4, (c) calculation of independent validation and parent-bootstrap CIs, and (d) the predeclared experiment command. The tests and preflight must pass without reading holdout outcomes. A sealed development/holdout parent split is mandatory.

**Once and only once this gate passes, commit the final frozen version, create a tag such as `star-phase3-freeze-v1`, record hashes and SHA in the freeze manifest, and run the confirmatory holdout.** Do not edit executable code/config after unblinding. If code must change due to a real defect, disclose the deviations and status of the confirmatory inference.

## 5. RUN THE FULL HOLDOUT STUDY

Implement suitable entry points, such as:

```bash
python -m pytest -q
python scripts/audit_phase3_preflight.py
python scripts/run_phase3_holdout.py --config configs/phase3_frozen.yaml
python scripts/revalidate_phase3_plans.py --config configs/phase3_frozen.yaml
python scripts/analyze_phase3_results.py --config configs/phase3_frozen.yaml
python scripts/build_phase3_figures.py
python scripts/build_phase3_tables.py
python scripts/audit_phase3_results.py
```

These are required interface *targets*; implement and document working equivalents if the repository architecture differs. No absolute Windows paths. Use resumable per-route/method work units, atomic writes, config/hash-aware caches and deterministic seed assignment. Fail visibly when experiments are missing. Run an initial post-freeze smoke test with synthetic data or non-performance-revealing fixture data; do not inspect holdout outcomes until ready to complete the protocol. Every eligible holdout charging route must be processed or explicitly accounted for as a failure/blocker; never silently omit hard routes.

For all eligible holdout routes run the frozen methods under the exact primary 64-plan cap. Include STaR, B3, B4 and B0 at minimum; ideally include frozen B1 and B2. Use equal and transparent candidate budgets plus measured stochastic scenario work and total runtimes. Evaluation samples for the final selected plan must be entirely independent of the search sample. Save all plans, per-route records, independent scenario summaries and validity checks. Include stratified counts by family and variant and exact population denominators.

Repeat the predeclared secondary budget profiles where computationally reasonable. If a secondary experiment is truly too expensive, document the reason and mark it missing, not completed. **Do not change the primary budget or choose only routes where STaR performs well.**

## 6. SCIENTIFIC STATISTICS AND INTERPRETATION

- Primary unit of comparison is the **matched fixed-customer route**, with uncertainty clustered at the original Homberger **parent-instance** level (A and B variants and multiple routes within a parent belong to the same cluster).
- Report the number of holdout parents, variants, total vehicle routes, charging-exposed routes, and unreliable-B0 routes.
- Use parent-cluster bootstrap or an appropriately justified hierarchical procedure. With only 48 holdout parent clusters, state bootstrap assumptions and avoid treating the many scenarios as independent benchmark units.
- Compare route-success probability, route target attainment (with specified interval rule), expected full-route completion, relative completion penalty or saving, and actual wall time separately. Use matched route-level paired differences and include CIs; for percent changes report denominator and handling of zeros.
- Report **STaR vs B4** as the primary comparison, **STaR vs B3** as the competitive comparison. If multiple hypotheses are tested, clearly distinguish confirmatory and exploratory findings and adjust/qualify multiplicity.
- Provide both route-weighted and parent-balanced estimates; report family A/B differences. Assess sensitivity to near-0.95 classification uncertainty, not just binary attainment counts.
- Do not claim a speed advantage if measured wall runtime is worse. Do not claim STaR dominates B3 merely due to using fewer MC scenarios. If B4 is faster and similar on some families, show that. Preserve negative and null results.
- Report how much of each observed gain derives from changing charge quantities versus charging-stop topology; make the mechanism measurable from saved plans, not inferred from fingerprints.

Predeclared publication interpretation gates:

**Strong result:** Independent holdout supports a meaningful positive STaR–B4 reliability difference, the additional completion cost is favorable or reasonable, and STaR remains competitive with B3; explain simulation savings and measured runtime faithfully.

**Narrow result:** STaR improves on B4 but not B3, or only under selected families/budgets; frame the paper as a targeted hybrid charging-topology repair method with conditional benefits.

**Negative/null result:** STaR fails to beat B4 or is dominated by B3; present the actual outcome and limitations, not a fabricated strong paper. Do not retune using the holdout. A new altered algorithm requires a separately labeled future study and an untouched new external benchmark for genuinely confirmatory evaluation.

## 7. PUBLICATION FIGURES — PNG ONLY

Produce genuine, high-quality scientific figures from raw validated numerical records. **PNG only for figures** (no SVG/PDF/JPEG). Use 400 DPI, colorblind-compatible colors, coherent manuscript-size fonts, clear legends and native benchmark time units. Every axis, curve, caption and numeric annotation must be supported by actual experiment data. If data are insufficient for a requested figure, mark it explicitly absent; never output a placeholder or silently substitute fabricated numbers.

Produce at least eight final substantive figures where data permit, for example:

1. `fig17_holdout_reliability_stars_vs_b4_b3.png`: paired route-reliability comparison with equality line and independent validation.
2. `fig18_holdout_target_attainment.png`: target attainment by method with explicit route denominator, point-vs-CI distinction and family facets.
3. `fig19_reliability_completion_frontier.png`: paired reliability-versus-full-completion Pareto comparison at the same input routes.
4. `fig20_search_scenarios_vs_reliability.png`: STaR/B3 scenario efficiency across frozen budgets, with parent-level uncertainty.
5. `fig21_runtime_vs_reliability.png`: actual wall-clock time, not just MC count; disclose if STaR is slower.
6. `fig22_stochastic_repair_by_family_variant.png`: family/variant breakdown, particularly R2 and RC2.
7. `fig23_partial_vs_topology_repair.png`: charging-plan mechanism: B4 versus STaR and observed station edits.
8. `fig24_ablation_and_budget_sensitivity.png`: preregistered budget or component ablation without post-holdout tuning.
9. `fig25_individual_route_case_study.png`: one transparently selected example with depot/customer timing and charging decisions; avoid cherry-picking (predefined selection rule).
10. `fig26_validation_uncertainty.png`: numerical reliability and CI proximity to 0.95, including ambiguous routes.

Each figure must have source-data provenance, script path and manuscript-ready caption in `docs/PHASE3_FIGURE_INDEX.md`. Automatically audit files for valid PNG signature, usable dimensions, required DPI metadata, and that no empty placeholder text is present. Include representative figures in the report, but provide all actual PNG files.

## 8. PAPER-READY TABLES — FULL NUMERICAL AUDIT

Generate `.csv`, `.tex` and `.md` tables with consistent units, correct LaTeX escaping and meaningful precision. Essential tables include:

1. Dataset/frozen split and eligible route counts.
2. Corrected STaR versus B0–B4 overall holdout results (success, CI attainment, full completion, search scenarios, time).
3. Paired STaR–B4 primary effect with parent-cluster CIs and per-parent sensitivity.
4. Paired STaR–B3 competitiveness and sample-efficiency/time distinction.
5. Results by family and variant, with sample sizes.
6. Budget curves / scenario counts / wall-time comparisons, with exact budget definitions.
7. Partial-charge-only versus topology-edit mechanism measurements.
8. Negative cases, failure reasons, and unresolved reliability targets.
9. Robustness stress tests (clearly labeled synthetic).
10. Reproducibility, test results, hash audit and implementation version.

Generate tables from authoritative validation records, never from hand-entered report summaries. Make every table reproducible with one command.

## 9. DELIVERABLES AND MANUSCRIPT PACKAGE

Required code/document paths (adapt names only if needed for the repository's existing architecture):

```text
configs/phase3_frozen.yaml
scripts/audit_phase3_preflight.py
scripts/run_phase3_holdout.py
scripts/revalidate_phase3_plans.py
scripts/analyze_phase3_results.py
scripts/build_phase3_figures.py
scripts/build_phase3_tables.py
scripts/audit_phase3_results.py
docs/PHASE3_PREFLIGHT.md
docs/PHASE3_PRE_REGISTERED_ANALYSIS.md
docs/PHASE3_FIGURE_INDEX.md
docs/PHASE3_FINAL_REPORT.md
docs/PHASE3_PAPER_OUTLINE.md
docs/PHASE3_MANUSCRIPT_DRAFT.md
docs/PHASE3_REPRODUCIBILITY.md
results/phase3/manifests/freeze.json
results/phase3/raw/...
results/phase3/plans/...
results/phase3/processed/...
results/phase3/figures/*.png
results/phase3/tables/*.csv
results/phase3/tables/*.tex
results/phase3/reports/...
```

The manuscript draft should contain: title and abstract options that **do not overstate superiority**; introduction and literature positioning; mathematical problem and assumptions; fixed-customer-sequence constraints; algorithm and safe-rejection proof limitations; B3/B4 algorithm descriptions; preregistered evaluation and independent MC validation; quantitative results; formal parent-level statistics; ablations and R2/RC2 failure discussion; threats to validity (synthetic station waits, independence, fixed customer orders, benchmark construction); limitations and conclusion. Use only bibliographic references with verifiable details; avoid made-up citations. Use figures and tables by path/caption.

Ensure reproducing the results does not require one developer's absolute personal directory. Keep original `dataset/` and all Phase 1/2/2.5 historical results unchanged. Save large raw artifacts in an auditable, compressed format and document how to obtain them; commit code, configuration, manifests and reasonable-sized summaries. Record the new versioned code tag and what was or was not pushed.

## 10. FINAL ACCEPTANCE GATES

- **P3-G0 Preflight correctness:** all implementation tests and source/model/plan audits pass; no unresolved high-severity errors; Phase 2.5 results independently reconciled.
- **P3-G1 Freeze integrity:** actual commit SHA, configs, primary contrasts, scenario seeds, analysis scripts and checksums frozen **before** holdout outcome inspection.
- **P3-G2 Holdout execution:** all eligible holdout exposed routes processed for the primary methods and cap; missing cases and exceptions fully documented.
- **P3-G3 Independent evaluation:** every selected plan reconstructible, independently valid and evaluated on the final separate scenario stream; no cache leakage or outcome-driven modifications.
- **P3-G4 Statistical integrity:** correct primary STaR–B4, competitive STaR–B3 and parent-cluster inference, with negative results retained.
- **P3-G5 Publication package:** real 400-DPI PNG figures, reproducible CSV/LaTeX tables, documented negative cases, rigorous report and honest manuscript draft.
- **P3-G6 Reproducibility:** audit script checks hashes, experiment completeness, selected-plan replay, plot/table origins and exact commands; package matches tagged code.

**STOP ONLY WHEN THE GATES HAVE BEEN VERIFIED, or a genuine external blocker has been documented with all independent tasks completed.** A passing `pytest` run or a set of charts alone is not completion.

## 11. FINAL AGENT RESPONSE

At the end report: (a) frozen commit/tag, (b) exact holdout instance and exposed-route counts, (c) **real** primary STaR vs B4 effect and confidence interval, (d) B3 competitiveness including simulation count versus actual wall time, (e) target attainment and completion costs, (f) family/variant failures, (g) tests, plan-validation and reproduction counts, (h) the PNG and table file paths, (i) overall verdict strong/narrow/negative, and (j) any missing/failed requirements. Explicitly state whether the final paper can claim a meaningful new method and whether the evidence is strictly confirmatory or qualified.

**BEGIN WITH PHASE 2.5 RECONCILIATION AND PRE-FREEZE CORRECTNESS. THEN FREEZE. THEN PERFORM THE HOLDOUT. DO NOT STOP UNTIL PHASE 3 IS FULLY COMPLETED OR A SPECIFIC EXTERNAL BLOCKER PREVENTS IT.**
