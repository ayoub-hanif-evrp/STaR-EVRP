# PROMPT 07 — Conference publication figures, tables, and evidence handoff

**Project:** STaR-EVRP — Slack-Targeted Stochastic Charging Repair for fixed electric vehicle routes under stochastic station waiting times  
**Scope:** publication preparation only; no new research experiments or changes to the frozen algorithm.  
**Expected output:** five main figures, three compact tables, source-traceable numerical inputs, caption/note files, verified vector and 400-DPI raster exports, and a clean writer handoff.

## 0. Mission and non-negotiable constraints

The research is finished. Phases 1–6 established the original method, the registered holdout result, the complete 120-instance benchmark, ablations, mathematical checks, additional scientific controls, and limitations. Do not start a new optimization or stochastic evaluation campaign. Do not change STaR, the dataset, random tapes, saved plans, metrics, original protocols, raw records, archived exhibits, or freeze tag. Do not tune anything to improve a plot. Do not write or revise the manuscript. Do not introduce any additional proposed algorithm. The only permitted new computations are loading/reconstructing existing plans, deterministic route checks, read-only extraction and aggregation of archived outcomes, uncertainty calculations using archived outcomes under their original inference rules, and figure/table generation and verification.

The purpose is to make a coherent, compact 10-page conference paper possible. The five figures must answer five distinct questions: what is the physical problem, how does STaR solve it, what is the principal paired evidence, which source routes benefit or fail, and what is the simulation-work trade-off? The three tables establish experimental conditions, the main comparisons, and component contributions. More exhibits are not an objective. Create exactly five canonical paper figures and three canonical paper table bundles. Supplemental source tables, machine-readable sidecars and proofs are not additional main figures or tables.

Use the 96-instance holdout as the primary population in main results (48 parent clusters, 2,321 originally charging-exposed routes), not a mixture of pooled and holdout estimates. State the complete benchmark includes 120 instances, 60 parents, 8,606 original routes, and 2,891 exposed routes; development contains 24 instances/570 exposed. All-120 results remain available from Phase 5 and are descriptive, not a new independent validation. The separate Phase 6 controlled timing panel of 118 routes is explicitly identified as exploratory and must never be merged with the 2,321-route primary cohort.

There is ONE proposed algorithm: STaR. The three principal baselines are the original constructive solution, mean-wait repair and quantile-based repair. Fixed-station repair (FSPC) and scenario search (SLS) are additional scientific controls, not competing new proposed methods; retain them in Table 2 and their pertinent main figures because the registered primary comparator and the simulation-effort contrast depend on them. Do not suppress unfavorable or tied results. AS1 and FT-SAA are exploratory Phase 6 supplementary studies, not parts of STaR; do not show them as algorithm components or main table rows. Keep their complete existing supplementary evidence and provide a short mandatory disclosure in the writer notes, including the inconclusive FT-SAA reliability result. No paper claim of global optimality, universal superiority, speedup, novel literature priority, real queues, fleet guarantees, or causal effects from post-selected strata.

## 1. Read-only preflight and evidence contract

Before implementation:

1. Inspect current Git HEAD and working tree. Expected last reviewed HEAD is `d17616177b61cb98e11c1cd5408d7c981fae2b21`; do not reset newer legitimate work. Frozen optimizer tag `star-phase3-freeze-v1` must still resolve to `c657aa69d55178c85b4759475933b36d1bcc2181`. Phase 5 result commit `bf6a4d86422350275a043c2424b7dd86d3b20b27`; Phase 6 result commit `3909994488e2a4df901bb83307bfa4e185c1872d`. Record observed HEAD, tag, inputs, library versions, fonts, operating system, and source hashes. Preserve unrelated local changes. Use a new additive output directory.
2. Read `README.md`, `docs/PHASE3_PRE_REGISTERED_ANALYSIS.md`, `docs/PHASE3_FINAL_REPORT.md`, `docs/PHASE4_FINAL_REPORT.md`, `docs/PHASE5_FINAL_REPORT.md`, `docs/PHASE5_ANALYSIS_PROTOCOL.md`, `docs/PHASE5_RESULTS_HANDOFF.md`, `docs/PHASE6_FINAL_REPORT.md`, `docs/PHASE6_ANALYSIS_PROTOCOL.md`, `docs/PHASE6_DIAGNOSTIC_REPORT.md`, `docs/PHASE6_MATHEMATICAL_AUDIT.md`, `docs/PHASE6_RESULTS_HANDOFF.md`, and the Phase 5/6 claim matrices, glossary, numbers-to-cite and manifest files. Read `configs/phase3_frozen.yaml`, `configs/phase5.yaml`, relevant Phase 6 config, original freeze manifest, and final gates. Check the actual files and schemas instead of assuming field names.
3. Locate authoritative sources below. Use full precision from existing machine-readable records and recompute only summaries from them. The rounded report/table examples in this prompt are cross-checks, not hard-coded plotting data. If an expectation differs, investigate definitions, keys, cohort, tape, and units; document discrepancy and block release if unresolved. Do not silently overwrite a source, round intermediate values, or copy values from a previous PNG.

| Evidence | Primary inputs |
|---|---|
| Original benchmark coordinates and route plans | dataset under `dataset/EVRPTW_ChargingStations_Dataset`, original Phase 3 CON ZIP (`results/phase3/con_bundles.zip`), frozen c64 selected plans and validation records, Phase 5 archive readers |
| Six-method holdout comparison | `results/phase5/data/route_results.csv`, `results/phase5/data/summary.json`, `results/phase5/tables/supplementary/S01_complete_benchmark.csv`, Phase 3 registered audit |
| Paired contrasts | `results/phase5/data/paired_effects.csv` (holdout, c64, reliability; fractions), Phase 4 archived parent effects, `results/phase6/data/paired_directions.csv` (holdout, R_pp; percentage points) |
| Source route complexity | `results/phase6/data/mechanism_strata.csv`, `route_features.csv`, `paired_routes.csv`, `attainment_transitions.csv`, `parent_influence.csv` in same directory |
| Timing panel | `results/phase6/data/timing_summary.csv`, `timing_route_aggregates.csv`, `timing_paired_effects.csv`, `timing_paired_routes.csv`, `timing_route_results.csv`, Phase 6 timing manifest; `results/phase6/tables/T06-05_controlled_runtime.csv` |
| Ablations | `results/phase5/data/route_results.csv`, `paired_effects.csv`, `summary.json`, `tables/main/T04_ablation_quality.csv`, `tables/main/T05_ablation_work.csv` under Phase 5 |
| Algorithm flow | `src/star_evrp/competitive_search.py`, `route_evaluator.py`, `timing.py`, `budget.py`, `search_common.py`, `charge_plan.py`, `deterministic_simulator.py`, frozen protocol and Phase 6 mathematical audit |

The original CON ZIP can be read directly using existing archive helpers; avoid Windows reserved `con` directory extraction. Join by exact instance/family/parent/variant/route ID and method/profile, not row order or filename similarity. Confirm complete keys, no duplicated matched pairs, fixed customer order, same validation tape, exact route denominators, and 10,000 final scenarios. Reuse existing Phase 4–6 readers and bootstrap implementations where practical. Parent A/B variants and all routes within a parent are dependent; do not use independent route-level bootstrap or infer across 120 independent environments. Reconcile the registered primary STaR minus FSPC mean against archived full precision `0.012420292977165015` and interval `[0.008630955453232267, 0.016503459913289817]` in reliability fractions (multiply by 100 for pp). It is the only confirmatory endpoint. Mark other intervals exploratory, pointwise, unadjusted, conditional on saved validation estimates.

## 2. Publication design system

Create a common styling module used by every figure. The following palette comes from the requested publication strategy; use accessible marker/line encodings in addition to color:

| Role | Color |
|---|---|
| STaR and repaired route | teal `#0D9488` |
| Original route and control methods | slate `#64748B` |
| Charging stations, nonattainment, adverse effects | amber `#D97706` |
| Selected benchmark route / spatial emphasis | blue `#2563EB` |
| Depot, text and axes | navy `#1E293B` |
| Background | white, with subtle neutral grid only when useful |

Use dark labels with strong contrast; teal/amber fills do not substitute for labels. Distinguish original and repaired lines by solid/dashed or markers, and controls by different shapes when necessary. Customers always circles, stations squares, depot diamond. Never use decorative gradients, shadows, 3D, rainbow palettes, excessive gridlines, dual axes, or unexplained color scales. No screenshots of a plot, AI-generated imagery, or street maps. All map coordinates are synthetic Euclidean dataset coordinates. Use genuine editable vector paths/text for diagram and plots. Legend only where necessary, position outside data when possible; do not overlap data or annotations. Align panels and axes. Use figure-panel labels `(a)`, `(b)`, etc., not long redundant titles inside plots. Use a single font family (e.g. DejaVu Sans or another actually installed, license-compatible, paper-appropriate family) throughout, and render math in consistent typography. Do not assume conference template fonts are known.

Target 178 mm double-column width by default, 75–120 mm height as appropriate; Figure 1 can be up to 120 mm and Figure 2 can be shorter with a horizontal flow. Use exact physical sizes (no uncontrolled `bbox_inches='tight'` resize); support optional configurable target width 85 mm only where it remains legible. At actual print size target 8–9 pt labels, 9–10 pt panel headings, minimum 7 pt for exceptional annotations, line widths roughly 0.8–1.3 pt, visually distinguishable markers. Check contrast and grayscale at final placement size. No global axis clipping to amplify differences. Differences use explicit zero reference. Absolute rates can use a clearly labeled focused point-plot range with ticks including all intervals and explicit range, not a truncated bar chart. Counts and rates always show denominators. Keep all error bars visible and explain each interval type. Use percentages for reliability levels, percentage points for differences; use native units for distances, energy and full completion unless verified physical conversion exists. No invented units or physical map coordinates.

Export each canonical figure as `*.pdf` (vector, embedded fonts), `*.svg` (editable), and `*.png` at true 400 DPI. Use reproducible vector metadata, deterministic SVG IDs and fixed figure size; do not upscale raster to claim DPI. At 178 mm width, 400-DPI raster width is approximately 2803 px (allow one-pixel rounding). No transparent background unless explicitly required; white print background. Generate sidecar JSON with exact plotted values, units, data selections, uncertainty, source hashes, plotting version and physical size. Also generate full-precision `data/FigXX_*.csv` inputs including all underlying displayed points, not just summary values. For Fig02 save its logical node/edge specification and source-line references. Maintain consistent filenames across formats. Final caption and table notes must be standalone, short, and intelligible without relying on this prompt.

### Naming contract

Keep repository keys stable; display readable names as the supplied strategy requests. A mapping table in writer notes retains acronyms for the user's established convention; if space calls for acronyms in a table, define them once in the caption/notes and use them consistently. Preferred display labels:

- CON / B0 — Original route (no repair).
- MWR / B1 — Mean-wait repair.
- QBR / B2 — Quantile repair.
- FSPC / B4 — Fixed-station repair (partial-charge amounts only).
- SLS / B3 — Scenario search (scenario-based local search).
- STaR — Slack-Targeted Stochastic Charging Repair.
- STaR-NPC, STaR-NSP, STaR-NAS, STaR-NPP — display as component removed in Table 3, not as additional branded algorithms.
- `c64` — 64-candidate budget in prose/exhibits. Internal keys permitted in sidecars, not visible labels.

AS1 and FT-SAA only in supplementary disclosure and existing archive references. Do not rename the frozen keys, source code, or historical files.

## 3. Figure 1 — actual spatial charging repair (flagship)

**Filename:** `Fig01_spatial_charging_repair`

Make a new scientifically faithful three-panel spatial illustration from real saved plans. The existing proof/case plots are not a substitute. This figure is essential and should make sense before reading the model.

### 3.1 Select the route using a documented rule

Use original holdout, frozen c64 CON and STaR, matched exact case and route ID. Before reading individual candidate maps, document the fixed selection rule: (i) topology changes (ordered station IDs and insertion gaps, not merely amounts); (ii) original Wilson nonattainment and STaR Wilson attainment, positive observed reliability change; (iii) keep the customer order identical and all deterministic energy/time checks valid; (iv) sort eligible routes by original customer count ascending (for visual readability), then case ID, then original route ID using a stable order. Select the first. Record eligible counts and chosen keys; no manual best-looking cherry-picking after rendering. If no eligible route exists, relax restoration to positive observed gain with topology change, then topology change alone; record exactly which fallback was required and do not hide the outcome. If the selected route is too visually dense, use label/inset design rather than outcome-based replacements. This is deliberately an outcome-selected illustrative success if rule (ii) is met, not a typical or representative route. Do not call it random or average. The previously registered R2 case remains separately archived and cannot be replaced as a registered case by this illustrative selection.

### 3.2 Reconstruct exact route geometry

Load actual benchmark customer/station/depot coordinates from the dataset using the existing loaders. Recover original and selected plan stop sequence and quantities (explicit actual charged energy from deterministic trace, not default `None` or full-charge placeholder). Validate with frozen simulator. Verify every customer visited in identical order, same depot/route ID, no other routes changed for this example, no synthetic nodes, and no missing/reordered stops. Include zero-quantity visits if present: waiting applies even if charge is zero. Preserve repeated station visits and station order; if a stop is revisited label visit number with an offset, not a fictitious coordinate. Record plan digest, instance file hash, source plan/validation provenance. If an existing archived trace is insufficient, deterministic zero-wait replay is allowed, not stochastic resampling. Use archived 10,000-scenario success counts and unconditional completion means for reliability/completion annotations.

### 3.3 Panel design

- **(a) Whole benchmark instance.** Plot all 1,000 actual customers (small, pale neutral circles), actual charging stations (small amber squares, subdued where appropriate), depot (navy diamond), and the selected original route overlaid in blue. Show the zoom extent or a clearly labeled indication of where panels b/c lie. Use equal spatial aspect, axis labels `x` and `y` in benchmark coordinates, reasonable ticks. No GIS tiles or geocoding. Include exact instance identifier and route ID in caption. Distinguish background customers from route customers without hiding the full instance.
- **(b) Original charging plan.** Zoom to the selected route. Plot ordered straight Euclidean legs, customers (number by visit order only if legible; otherwise first/last and critical neighbors), depot, visited station squares and optionally faint nearby alternatives. Annotate station IDs, actual per-visit charge amounts, and relevant topology changes. Use dashed slate original path with direction markers if necessary. Show reliability and unconditional completion from archive; clearly state reliability is estimated, not a deterministic guarantee. Add Wilson attainment indicator if space permits.
- **(c) STaR repaired plan.** Same zoom limits and equal aspect as (b), shared axis range/ticks, same customer markers and order, solid teal path; highlight actual added/removed/replaced/relocated visit(s) with concise labels and distinct markers. Do not imply a one-to-one replacement if the topology edit is actually insertion/deletion. Show actual charge amounts and reliability/completion. Place labels with leader lines rather than changing node locations. Provide one shared compact legend and annotation block for both panels if required.

Optional only if legible and actually supported: a small inset showing zero-wait battery level or slack near the changed visit, using true trace and native units; label it explicitly as deterministic zero-wait trace, not realized stochastic trajectory. Do not crowd the three maps. Do not let a bonus inset displace necessary labels. No artificial coordinates or paths, no route smoothing. Use one shared scale bar/coordinate range only if useful; avoid real-world km labels.

Save `data/Fig01_route_selection.csv` (all eligible candidates and ordering, or a full audit file with eligibility flags), `data/Fig01_route_stops.csv` (plan, sequence index, node ID/type, x, y, charge amount, arrival/departure battery and times if used), `data/Fig01_instance_nodes.csv`, `data/Fig01_metrics.csv`, and selection JSON. Assert plotted nodes and ordered segments match the reconstructed plans. Caption: outcome-selected holdout example; fixed customer sequence; before/after estimated reliability on same archived validation tape, completion includes late scenarios, coordinate/energy/time units native.

## 4. Figure 2 — STaR optimization framework

**Filename:** `Fig02_star_framework`

Create a compact horizontal vector algorithm diagram, not a result chart. Explain only the frozen STaR method. Read actual functions and compare diagram against execution order; no AS1, FT-SAA, learned score, global rerouting or dynamic recourse. The diagram should be understood at print size in under a minute, ideally with 6–8 grouped boxes and a clearly drawn incumbent loop.

Required algorithm logic, using the actual source as authority:

1. Input feasible constructive plan, fixed customer order, station laws, target and budget. Initialize incumbent, deterministic trace, initial stochastic score on the full optimization tape (512 draws in primary profile); shared route-ordinal common random numbers. All proposals preserve customer sequence.
2. Rank current charging visits by ascending marginal upper bound (isolated-delay tolerance and station waiting distribution); prioritize nearby customer gaps. Do not draw a fake risk score using additional features never implemented.
3. Interleave charging-quantity moves (minimal/speed/full and quantity/transfer adjustments) with remove/replace/relocate/insert topology proposals and allowed allocations. Candidate identities deduplicated; generation/trial/elapsed guards checked.
4. Deterministic energy and zero-wait timing feasibility check; reject invalid or duplicate candidates, continue to next proposal; station hours off in primary model.
5. Analytical screen only if incumbent is already empirically target-attaining: if min marginal reliability bound is below target (frozen tolerance), reject. Otherwise pass; when incumbent misses target, bypass screen. Label bound as on true modeled reliability, not lossless for finite MC score.
6. Progressive fixed-tape evaluation: 128-row prefix, optimistic success upper bound and completion lower bound based on zero-wait completion; if optimistic lexicographic score cannot strictly improve incumbent, prune. Otherwise extend same tape to 512 (not a fresh independent batch). Formula may be in small callout: `R_U=(m+S-k)/S`, `C_L=(C_k+(S-k)C_0)/S`; define symbols in caption/notes. Keep numerical-tolerance qualification in notes. Distinguish screening vs prefix pruning visually; no claim of universal path equivalence under binding budgets.
7. Compare complete empirical candidate score to incumbent: prefer target attainment; if both attain, minimize unconditional mean completion then maximize reliability; otherwise maximize reliability then minimize completion. Strict improvement updates incumbent and restarts neighborhood (first improvement). Otherwise next candidate. Return incumbent when no improvement available or budget/generation guard stops search; loop from updated incumbent to ranking. Show reject/retry loop with simple routing, not lines across boxes. Guard is cooperative not strict real-time deadline.
8. Optional small outside-search validation box: selected plan evaluated with independent 10,000-scenario tape; no feedback arrow from validation to search. This is evaluation protocol, not an optimization step.

Use small labels `feasible?`, `cannot attain?`, `cannot improve?`, `improves?` only if accurate; label branches yes/no, include bypass. If compressing logic into a screening panel, retain the exact incumbent gating condition. Use source-based flow specification in JSON and test diagram nodes/edges for required conditions (human semantic review in addition to automated checks). Caption distinguishes true chance-bound and finite-tape pruning. This figure must never claim STaR is an exact stochastic solver or that it guarantees the target. A vector diagram produced via Matplotlib patches, SVG or Graphviz is acceptable if fonts, size and vector exports are controlled; do not use generated image art.

## 5. Figure 3 — paired reliability evidence

**Filename:** `Fig03_paired_reliability`

Use holdout c64, 2,321 matched exposed routes, 48 family-stratified parent blocks. Preferred two-panel design:

(a) Horizontal point-interval plot of `STaR − Fixed-station repair` and `STaR − Scenario search` in pp, with clearly marked zero reference, distinct filled/outlined markers for confirmatory vs exploratory. Route-weighted means and 95% parent-cluster percentile intervals, not parent-equal means. The registered estimate is +1.2420293 pp [0.8630955, 1.6503460]. Scenario search is +0.3187979 pp [0.1333841, 0.4927989]. Derive these from `results/phase5/data/paired_effects.csv` (`cohort=holdout`, `profile=c64`, `metric=reliability`, comparisons FSPC/SLS) converting fractions to pp exactly once. If showing individual parent effects, derive them from the archived parent-effects table or exact paired route records, retain actual parent identity/denominator, plot all 48 lightly jittered in a separate aligned strip or behind points with readable legend. Never crop extreme parent effects to make pooled intervals appear larger; if range makes the primary estimate unreadable use a distinct labeled subpanel for parent points or omit them from the main figure and retain in sidecar. Do not depict the mean of parent means as route-weighted primary. Parent-equal sensitivity +1.1160 pp [0.7902,1.4687] may appear in notes, not a competing main marker. Avoid a huge-scale CON improvement alongside small primary contrast; Table 2 gives all methods.

(b) A compact 100% direction bar or three aligned labeled blocks for STaR vs fixed-station repair: higher observed success count 160, equal 2,050, lower 111. Define ties by equal archived successes out of 10,000, not rounded percentages or equality of true probabilities. Display counts and percentages (6.89%, 88.32%, 4.78%; rounding may sum 99.99%). No claim that STaR improves all routes. Optional SLS direction row (164 / 2,042 / 115) only if equally clear; retain all direction counts in sidecar regardless. Read `results/phase6/data/paired_directions.csv` `cohort=holdout`, `metric=R_pp` and reconcile directly against paired success records. Sign direction STaR minus comparator positive favors STaR.

Caption explicitly identifies confirmatory primary vs exploratory SLS, 95% family-stratified parent cluster bootstrap (9,999 resamples; A/B retained), and exact paired sample. Include actual mean trials STaR 62.67 vs fixed-station 20.18 at common maximum 64 in note; not equal consumed compute. Existing holdout SLS work/elapsed trade-off retained in Table 2 and notes.

## 6. Figure 4 — source charging complexity and remaining difficulty

**Filename:** `Fig04_charging_complexity`

Use exclusively holdout, original CON station-visit count before repair, not selected STaR visit count, not distinct station IDs. Group exactly 1, 2, and 3+ visits. Every exposed route belongs to one group; no-charge excluded from these denominators. `results/phase6/data/mechanism_strata.csv` filter `cohort=holdout`, `comparison=FSPC`, `dimension=source_visit_bin`. Cross-check against `route_features.csv` and paired archived data. `mean`, `lo95`, `hi95`, `contribution` in this Phase 6 CSV are ALREADY in percentage points: do not multiply by 100 again.

(a) Point-interval plot for STaR minus fixed-station repair mean reliability effect (pp) by original visit bin, with zero line and group n labels. Use parent-cluster exploratory intervals and parent counts (47, 22, 16 nonempty parent blocks; overlapping parent membership across bins is allowed). Expected full precision checks:

| Original visits | n | Mean pp | 95% low | 95% high | Net contribution to overall pp |
|---|---:|---:|---:|---:|---:|
| 1 | 1587 | 0.1806175173 | -0.0011838452 | 0.3918956513 | 0.1234984920 |
| 2 | 159 | 0.1844654088 | 0.0237689334 | 0.3727428504 | 0.0126367945 |
| 3+ | 575 | 4.4639652174 | 3.2936459936 | 5.7197634721 | 1.1058940112 |

(b) Zero-baseline dot or bar plot for residual Wilson nonattainment rate after STaR, aligned by same visit bins: 4/1587 (~0.25%), 4/159 (~2.52%), 102/575 (~17.74%). Show both count and denominator; sum 110 failures, 2,321 total. Do not mix with all-120 149 failures. No invented binomial error bars treating routes as independent; if uncertainty bars for rates are desired, use the same parent-cluster resampling of archived route-level flags and label exploratory, otherwise show descriptive rates only.

Include a concise annotation: 3+ visit routes are 575/2321 (~24.8%) of exposed routes and account for ~89.0% of **net signed reliability improvement** versus fixed-station repair. Derive the latter as subgroup contribution / overall signed mean, not share of positive gains or a causal fraction. Sum all group contributions to registered pooled effect within full-precision tolerance. This is evidence of association and concentrated improvements; do not claim complexity causes failure or topology changes alone cause the effect. Mention source minimum slack and R2/RC2 results in the writer notes rather than cluttering this figure. All intervals exploratory.

## 7. Figure 5 — quality versus simulation effort

**Filename:** `Fig05_quality_simulation_effort`

Use the separate fixed Phase 6 timing panel (118 routes, 60 parents, 23 development and 95 holdout routes), 20/50/100 ms nominal cooperative runtime guards, three serial repeats per method/guard/route, 2,124 total runs. This is not the full benchmark or a strict equal-runtime comparison. Compare only STaR and scenario search. Source: `results/phase6/data/timing_summary.csv` `cohort=all120` (label this 118-route panel, not "all 120 instances" in the figure!), `timing_route_aggregates.csv`, `timing_paired_effects.csv`, `timing_paired_routes.csv`, and manifest. Aggregate repeats by route using Phase 6 protocol (quality and work means, wall time median per route before paired analysis). Do not treat repeats as independent observations. Use actual scenario counts, not candidate budget times samples.

(a) Scatter quality-work plot, x = mean incremental search draws per route (ticks in thousands or comma formatted), y = mean independent-validation reliability (%). Two distinct method marker styles plus guard label 20/50/100 ms, no connecting curves or continuous Pareto frontier. Use six points; emphasize 50 ms with outlined markers or labels, not selectively omit others. Expected checks:

| Guard | SLS mean R (%) | STaR mean R (%) | SLS draws | STaR draws |
|---:|---:|---:|---:|---:|
| 20 | 98.7919209 | 99.1763842 | 21919.0960 | 12922.2147 |
| 50 | 99.8337571 | 99.7002542 | 33699.4350 | 18695.5932 |
| 100 | 99.8839831 | 99.7060169 | 41373.6497 | 23140.1582 |

Use a clearly labeled focused reliability axis if necessary (points not bars). Show appropriate reliability uncertainty: best default is (b) a small aligned paired-effect interval panel for STaR minus scenario search (pp) at each guard, with zero reference and archived exploratory family-by-partition parent-cluster intervals from `timing_paired_effects.csv` (`metric=R_pp`, `cohort=all120`). These are paired difference intervals, not error bars for either individual method's absolute mean. If adding absolute mean error bars to (a), compute true marginal intervals from archived route aggregates using the original 9,999 parent-block procedure stratified by family and partition, including the repeat aggregation; label them as marginal and distinguish from paired differences. Do not reuse difference intervals as absolute intervals. Prefer the paired panel when space is limited. Do not infer significance from overlap of marginal intervals.

At 50 ms, STaR − SLS reliability -0.1335028 pp [-0.5100339, 0.0874082]; mean paired route-median wall difference +0.2331 ms [-1.0180,1.4609]; STaR saves 15,003.84 search draws on average, ~44.52% relative to SLS. Annotate `44.52% fewer search draws at 50 ms` from exact ratio, not percentage of rounded chart labels. Cooperative guards exceeded in 122/354 STaR and 117/354 SLS repeats at 50 ms, maximum overshoots 22.18/19.96 ms. State no established reliability or elapsed-time advantage at 50 ms; none of the guard-specific reliability difference intervals excludes zero (verify). At 20 ms actual paired mean wall difference is positive with interval excluding zero; do not claim equality or speedup across all guards. Separate archived c64 result (34.59% fewer draws but slower wall time) in Table 2 notes. Distinguish controlled runtime study from causal prefix ablation; draw savings are not exclusively caused by prefix pruning. Prefix ablation in Table 3 provides separate evidence. Never label nominal guards as guaranteed deadlines, or compare times across archival/new cohorts as a speedup.

Caption includes the panel and repeat design, common nominal guard, uncertainty meaning, work exclusion of validation, observed overshoot, and no proven speedup. Figure 5 is first to move to supplement if paper space is tight; retain its numbers in notes.

## 8. Table 1 — experimental configuration

**Filename:** `Tab01_experimental_configuration`

Compact two-column `Parameter | Configuration`, grouped logically by dataset, physics, search, validation/inference. Combine related items to avoid a page-long table. Use native units. Verify from frozen config and archive. Required entries (may combine):

- Extended Homberger benchmark, 1,000 customers per instance, 120 instances (60 A/B parent pairs); 24 development / 96 holdout, 48 holdout parents.
- Complete route coverage 8,606 total / 2,891 exposed; primary holdout 6,864 routes / 2,321 exposed; 4,543 no-charge holdout routes unchanged and excluded from exposed metrics. Confirm 333 station nodes per instance if including it; do not imply 120 different station environments (four unique station attribute tables reused in both partitions).
- Fixed customer assignment/order; battery Q=700, energy rate h=1, native units. Deterministic Euclidean travel, linear heterogeneous charging rates. Synthetic independent per-visit lognormal waits (station-specific laws); station operating hours disabled, no endogenous queues/recourse.
- Route-level target 95%; c64 maximum 64 distinct plan trials including incumbent, 131,072 incremental scenario ceiling and 5 s cooperative guard. At 64×512, ceiling cannot bind; include note if space. 512 per fully scored stochastic plan, 128 prefix for STaR; three nearest eligible alternatives. Actual consumed work differs.
- Independent final validation 10,000 scenarios per selected plan, shared per-route common random numbers across methods and separate from optimization. One-sided 95% Wilson LB >= 0.95 attainment; no fleet-level or simultaneous guarantee. Parent-cluster bootstrap 9,999 resamples with family strata for holdout; only original STaR−FSPC reliability contrast confirmatory. Preserve seed values and precise environment in supplementary traceability rather than crowding the table.

Use compact layout; put secondary constraints in table notes where necessary, without hiding model scope. Expected 0.35–0.45 page at print scale.

## 9. Table 2 — main comparative performance

**Filename:** `Tab02_method_comparison`

Six rows: Original route, Mean-wait repair, Quantile repair, Fixed-station repair, Scenario search, STaR. The first three are the original benchmarks; two controls are scientific comparisons. Use full names, or the established acronyms with explicit expansion in note if space requires. Highlight STaR name in bold without falsely emphasizing every numeric entry as best. Prefer clean `booktabs` lines with optional subtle separator between three baselines and additional controls; no vertical borders or unnecessary color. Six columns: method, mean R (%), attained (count out of 2,321), full completion (native units), incremental search draws, wall time (ms). Clear direction arrows or notes (higher R/attainment, lower completion/draws/time). Do not use a single "best" score. The original unmodified CON is not a search method; report observed recorded 0 search draws and 0.22 ms setup/evaluator time with footnote that it does no optimization, rather than suggesting comparable search time. If display convention is dash for non-applicable optimization time, preserve the observed 0.22 ms in the note and machine-readable CSV. MWR/QBR have zero MC search draws, not missing data. Keep full-precision numeric export.

Cross-check against original holdout records and `S01_complete_benchmark.csv`:

| Method | Mean R (%) | Attained | Completion | Mean draws | Mean wall ms |
|---|---:|---:|---:|---:|---:|
| CON | 80.97 | 1686 | 3391.25 | 0 | 0.22 |
| MWR | 95.29 | 2052 | 3133.83 | 0 | 27.39 |
| QBR | 95.21 | 2183 | 3135.71 | 0 | 27.45 |
| FSPC | 96.07 | 2161 | 3168.98 | 4257 | 8.38 |
| SLS | 97.00 | 2193 | 3137.43 | 19911 | 27.51 |
| STaR | 97.31 | 2211 | 3135.83 | 13024 | 29.69 |

Use integer attainment, two decimals for R/completion/wall, rounded integer mean draws for readability; keep underlying precision in CSV/sidecar. Distinguish reliability point estimates from Wilson lower-bound attainment. Completion averages every scenario including failed trajectories. Search draws exclude independent validation. Timing from archived same Phase 3 c64 cohort (not a Phase 6 rerun). Mandatory note: actual trials FSPC 20.18, STaR 62.67 despite same 64 maximum; cannot claim matched work or optimal fixed-topology allocation. STaR versus SLS +0.32 pp exploratory, 34.59% fewer draws, slower mean elapsed 29.69 vs 27.51 ms. MWR mean completion ~2.01 native units shorter than STaR; QBR completion close. Avoid any suggestion of strict dominance. Do not add AS1/FT-SAA rows, not the same population.

## 10. Table 3 — component ablation

**Filename:** `Tab03_component_ablation`

Holdout only; 2,321 exposed routes. Column headings `Component removed | Mean R (%) | Attained | Search draws | Reliability loss (pp)`; full STaR first followed by four component removals. Use readable names rather than branded variants. Draws from same per-route c64 count definition; time excluded because archived controls and new ablations belong to different measurement cohorts, even if same nominal hardware. Loss = full STaR minus ablated reliability, computed using full-precision matched means or `paired_effects.csv` reliability fraction ×100; positive means loss when removing component. Three decimals for loss so small effects are not erased by rounding. A value of 0.000 for NPP reflects exactly identical recorded reliability. Preserve all other full-precision data and exploratory intervals in sidecar or note.

| Component removed | R (%) | Attained | Draws | Loss (pp) |
|---|---:|---:|---:|---:|
| None — full STaR | 97.31 | 2211 | 13024 | — |
| Partial charging | 94.19 | 2096 | 8400 | 3.120 |
| Slack prioritization | 97.01 | 2197 | 13080 | 0.308 |
| Analytical screening | 97.31 | 2207 | 13569 | 0.007 |
| Progressive evaluation | 97.31 | 2211 | 18927 | 0.000 |

Cross-check full-minus variants unrounded pp: NPC 3.1202972857; NSP 0.3077638949; NAS 0.0071693236; NPP exactly zero. The partial ablation removes amount-only moves and partial allocation on new topology edits, with original plan as incumbent; do not describe it as forcing every original stop to fully charge. NSP changes only criticality order; NAS disables analytical rejection but retains ranking/prefix; NPP skips prefix evaluation/pruning and scores admitted candidates fully. Single-component effects not additive and exploratory. Full STaR saves approximately 5,903 draws per holdout route compared with NPP while recorded reliability, attainment and completion are identical; verify per-route equality on archived records, not rounded mean equality. Different budget consumption can alter search paths in general. Note slack prioritization modest, development sign reversed; do not hide. Keep archived comparisons in Phase 5. No new ablation experiments.

## 11. Deliverables and repository organization

Add a small focused publication module and single reproducible CLI (e.g. `src/star_evrp/conference_exhibits.py`, `scripts/build_conference_exhibits.py`; separate validation module if useful). Read-only inputs; configurable `--output` and `--width-mm`; default target `results/conference`. Separate `build`, `audit`, `package` subcommands or equally clear interface. Avoid dependencies beyond existing scientific stack unless necessary for true vector exports or TeX compile; document additions without modifying frozen dependency files. Add focused tests (`tests/test_conference_exhibits.py`) and additive configuration only if needed. Do not reorganize historical folders or remove science artifacts.

```
results/conference/
  figures/
    Fig01_spatial_charging_repair.{png,pdf,svg,json}
    Fig02_star_framework.{png,pdf,svg,json}
    Fig03_paired_reliability.{png,pdf,svg,json}
    Fig04_charging_complexity.{png,pdf,svg,json}
    Fig05_quality_simulation_effort.{png,pdf,svg,json}
  tables/
    Tab01_experimental_configuration.{tex,csv,md}
    Tab02_method_comparison.{tex,csv,md}
    Tab03_component_ablation.{tex,csv,md}
  data/                      # full-precision displayed data and exact selections
  audit/                     # tests, hashes, formats, visual/TeX proof checks, reproducibility
  FIGURE_CAPTIONS.md
  TABLE_NOTES.md
  SOURCE_TRACEABILITY.md
  METHOD_GLOSSARY.md
  EXHIBIT_INDEX.csv
  CLAIMS_AND_LIMITATIONS.md
  PAPER_OUTLINE.md           # exhibit-placement map only, no manuscript prose
  README_RESULTS_PACKAGE.md
  MANIFEST.json
  STaR_EVRP_CONFERENCE_EXHIBITS.zip
```

Use exact stems. Add `docs/CONFERENCE_EXHIBITS_REPORT.md` with final decision, figure/table purposes, source provenance, tests, warnings and instructions. Update root README minimally with one link to the conference package if useful; do not overwrite prior results navigation. Do not write abstract, introduction, related work, results/discussion prose, or the paper itself. `PAPER_OUTLINE.md` is a short placement map for writer: Fig01 problem/model, Fig02 method, Tab01 setup, Tab02+Fig03 main results, Fig04 mechanism, Tab03+Fig05 computational/ablation analysis. If space is constrained move Fig05 to supplement first; retain all numbers and limitations. Keep four essential figures. Proposed 10 pages including references is a planning assumption, actual template unspecified; no guarantee of pagination. Provide ready-to-paste standalone LaTeX tabular fragments with `booktabs`, optionally `threeparttable` only if available; use standard tabular with compact columns and clean note outside. Do not use tiny resizebox as default. Compile at 178 mm text width using actual compiler. Optional 85 mm alternate table formatting only if legible. Package all five figures, three tables, notes, precise inputs and relevant verification evidence. No bulky copies of frozen archives; link them by repository path and digest. ZIP members sorted, no absolute paths, no transient proof directories or self-hash recursion. Add SHA-256 manifest with source and output relative paths. Do not claim ZIP hash from its own manifest without a separate envelope.

### Writer handoff disclosure (mandatory)

In `CLAIMS_AND_LIMITATIONS.md`, map each claim to exact table/figure/archived source and cohort. Include:
- Original Phase 3 registered STaR−FSPC +1.24 pp [0.86,1.65] on 48 holdout parents, actual unequal trial counts, not proof of causal topology benefit or superiority over optimal fixed-topology solver.
- Original STaR−SLS +0.32 pp [0.13,0.49] exploratory, 34.59% fewer search draws but slower elapsed, and controlled Phase 6 panel 44.52% fewer draws at 50 ms with inconclusive reliability/time difference and guard overshoot.
- Complete 120-instance results available from Phase 5, 97.06% mean STaR reliability and 2,742/2,891 attainment, descriptive combined; do not substitute for primary holdout.
- Phase 6 AS1 113-route restricted one-visit panel: AS1−STaR −0.018 pp [-0.059,0.022], completion −14.04 native units; no reliability improvement established; hybrid not implemented. Phase 6 FT-SAA 118-route panel: STaR−FT-SAA −0.384 pp [-1.183,0.050], STaR shorter completion, incomplete multi-visit solver certification (five complete MILP certifications of 22 multi-visit cases; read report for exact statuses). This qualifies any topology-superiority claim. Preserve supplementary results and refer writer to Phase 6 handoff; no selective exclusion.
- Route-level mechanism associations, not causal; 3+ visits account for concentration of net improvement and remaining failures; 109/110 holdout nonattainments R2/RC2. Station laws synthetic, only four station-table contents, no unseen infrastructure, no station windows or fleet congestion, fixed sequences and linear charging. No external literature solver dominance or claim that combination is unprecedented. The attached presentation strategy's literature mentions are not verified bibliographic references; do not invent citations. Writer will verify literature separately.
- Analytical screen valid as true reliability necessary condition under stated model, not guaranteed lossless for finite empirical score; prefix optimistic score safe for same tape/incumbent subject to numerical tolerance, not blanket search-path equivalence under binding budgets. NPC bundled removal; slack result modest and development sign reverses. Any runtime comparison must use recorded cohort and guard caveats.

## 12. Quality assurance and acceptance gates

No fake PASS. Every check must actually run and record the evidence, or report blocked with reason. Do not describe missing outputs as completed. Record actual commands, exit statuses, failures and resolutions. All derived numerical sources must be automatically compared to exact archived records. Use meaningful assertions, not tests that simply reproduce literals in this prompt.

**C7-G0 — Protected evidence.** Confirm frozen tag and all protected dataset/source/Phase 1–6 artifact hashes remain unchanged. Recheck prior audit manifests or use existing protected-input verifier; don't blindly trust current report. Record Git baseline and final diff; only additive conference source/tests/docs/results plus minimal navigation and prompt changes. No archived optimizer invocation, no new MC or solver runs. No `git reset --hard`, broad `git clean`, or deletion of untracked user work. If disposable scratch copies need removal, use explicit allowlist, check tracked-file status, resolved paths, symlinks/reparse points, record removed files; respect permissions. Keep final proof/check evidence tracked or included in release as appropriate.

**C7-G1 — Data integrity.** Test keys/cohort, 2,321 route pairs/48 parents, exact archived primary, direction sums, all visit bins and 110 nonattainments, three timing guards and 118 matched route means per guard/method, 2,124 repeat rows, 96/24 split, full 120 counts, all table 2/3 values, and no silent use of mixed populations. Test unit conversion (fraction vs already pp), source vs selected visit counts, loss sign, actual exact NPP equality. Reconstruct bootstrap inputs from saved rows and reconcile archived intervals; when reusing archive intervals, validate against exact source rows and original estimator. If optional marginal intervals computed, reproduce them from parent strata and independent code/spot checks. Cross-check direction counts by success integers. No independent route bootstrap.

**C7-G2 — Spatial and logic accuracy.** Validate selected example, rule, saved plans, customer order, actual station quantities, source coordinates, matching zoom limits/aspect, stop and segment geometry, real metric values, traceability; independent reviewer/test from source rather than trusting same plotting arrays. Verify Fig02 control flow and semantics against frozen source and mathematical audit, particularly initial incumbent, analytical gate, prefix extension, score ordering, first-improvement restart, stop conditions, no validation feedback. Record a semantic checklist with exact file/function/line references.

**C7-G3 — Figures.** All 15 required render files (5×3) and five sidecars exist and are nonempty. Verify PNG signature, dimensions, 400-DPI metadata (allow pHYs rounding), no missing glyphs, valid PDF page sizes and true vector paths/text, SVG parses and editable vectors. Open/render actual PNGs and PDFs at native size and reduced ~675 px or print width, and grayscale. Inspect each individually: clipping, panel letters, overlapping text, tiny labels, line/marker contrast, tick precision, denominator, units, uncertainty/zero lines, Fig01 before/after scale, Fig02 no crossing ambiguous edges, Fig05 guard/interval labels. Produce actual proof sheet or per-figure review record with hashes, reviewer notes, image sizes and corrections; do not claim visual inspection if tools cannot open them. Automated bounds checks supplement, not replace, human/agent viewing. Avoid overscaled table or figure fonts. Correct issues and re-render.

**C7-G4 — Tables.** Three CSV, three Markdown and three TeX match; verify all values/names/caption definitions from exact machine-readable inputs; TeX table compiles with installed Tectonic or LaTeX at 178 mm, no overfull boxes or missing characters; inspect rendered proof. Use accurate math escape and arrows, no raw underscores, correct decimal precision and alignment. If compiler unavailable, log blocker and try an installed equivalent; do not label pass without real compile.

**C7-G5 — Reproducibility.** Run focused tests and full repository tests (previous full suite 92 passed). Build all exhibits twice from identical archived inputs to distinct fresh scratch output dirs; compare exact numeric CSV/JSON/TeX/caption bytes, and deterministic PNG/SVG/PDF bytes where metadata fixed. If PDF tool embeds unavoidable volatile metadata, normalize only generated derivative metadata or compare canonical rendered/vector content and explicitly report residual nondeterminism, not a false byte-identical claim. Inspect logs and sidecar hashes. Verify build and audit commands from fresh output and correct error on missing input. No new optimization needed. Archive concise proof of actual run.

**C7-G6 — Writer release.** Check 5 canonical figures, 3 table bundles, notes, mapping, source traceability and disclosures all included; verify ZIP integrity and member paths/hashes after extraction to safe scratch; no historical modifications; README points to actual files. Commit and push only scoped completed work where permissions allow; record exact commit SHA in final response, not self-referential in hashed manifest. If push unavailable, explicitly report it. No more phases or new performance experiments.

## 13. Execution order and final report

1. Preflight, evidence inventory, selection/aggregation plan, input hashes.
2. Build common visual/style and source readers, precise data exports.
3. Implement Fig01 and Fig02 with source-level semantic review; then Fig03–05.
4. Generate tables from exact archived inputs, captions/notes/glossary/placement map.
5. Run numeric validation, test suite, vector and print proof review, TeX compile. Fix only new presentation code/format issues; keep records of corrections.
6. Repeat clean build, verify source preservation, package, scoped commit and push.

Final reply must include: actual final HEAD/commit, status of each C7 gate, exact file paths for five figures and three tables, route selection key and verified before/after values, source denominators and primary checks, actual test count, formats and DPI, actual compile/visual/rebuild checks, ZIP path and SHA-256, any unresolved issues. State explicitly that the frozen method and experiments were not altered and no new performance experiments were run. Describe any design choices made without a conference template. If anything fails, preserve evidence and mark incomplete rather than inventing a successful output. Deliver the finished publication artifacts, not merely a plan or mockup.

**Begin now.**
