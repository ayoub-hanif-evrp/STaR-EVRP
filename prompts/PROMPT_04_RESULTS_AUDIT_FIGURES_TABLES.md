# PROMPT 04 — STaR-EVRP: Independent Results Audit, Publication Figures, Tables, and Writing-Agent Handoff

> **Audience:** Autonomous coding agent with access to the existing local `STaR-EVRP` repository, original benchmark dataset, and tracked Phase 3 result files.
>
> **This is a RESULTS-ONLY production phase. Do not write the paper or modify the optimization methods.**
>
> **Mandatory execution rule:** Do not stop at planning, coding, partial analysis, a few figures, or an untested script. Implement, run, test, visually inspect, correct, audit, and deliver every requirement in this specification. Work autonomously. If an actual environment blocker prevents a particular item, document the blocker and still finish every unaffected requirement. Never fabricate computations or output placeholders.

## A. Goal, research context, and immutable boundary

The project **STaR-EVRP (Slack-Targeted Stochastic Charging Repair)** optimizes charging-stop topology and charging quantities while holding each vehicle's customer order and customer-to-vehicle assignment fixed. The primary uncertainty is synthetic independent lognormal waiting times at charging stations. Success means **jointly** satisfying all customer latest service-start times **and** the depot-return deadline. The reliability target is 0.95 at the **individual route** level. Route completion is the unconditional entire depot-return time, including late scenarios; native benchmark time units are **not automatically minutes**. Station operating hours are switched off for compatibility with the original CON model. The result is not a fleet-level chance guarantee or evidence of real queue calibration.

The confirmatory Phase 3 holdout was **already opened and evaluated exactly once** under the registered protocol. The locked executable is Git commit `c657aa69d55178c85b4759475933b36d1bcc2181`, tag `star-phase3-freeze-v1`; the results publication commit observed during review was `149d9f4d8f616d78ce0c295696515f1bbc342967`. **Do not silently change methods, source solution construction, experimental populations, stochastic assumptions, optimization budgets, random seeds, code from the frozen executable, or existing Phase 3 raw/results.** This phase is a reproducible **audit and editorial re-expression of existing saved outcomes**, not a second confirmatory trial. It can run deterministic integrity checks and independently re-compute existing saved statistics; it must not use holdout outcomes for optimization tuning, methodological selection, additional search, or new confirmatory claims.

The sole **preregistered confirmatory comparison** is the paired, **route-weighted** mean difference in independently evaluated route success probability **STaR minus B4**, at `c64` (64 unique candidate plans per initial charging-exposed route). The 95% interval is the **family-stratified, parent-cluster bootstrap** (48 parents, eight per each of six families; two A/B variants and all routes held together), 9,999 bootstrap replications, seed `312406`. Parent-balanced sensitivity is separate. All other intervals and contrasts are exploratory/descriptive pointwise comparisons, not simultaneous confirmatory discoveries. The one-sided 95% Wilson lower confidence bound >=0.95 is the **individual-route attainment classification**; do not confuse with an optimization sample point estimate, a two-sided Wilson interval, or mathematical feasibility proof.

**No manuscript drafting, no new literature review, no conference selection, no new abstract, no README rewrite unless needed solely to document how to obtain figures/tables.** Another agent handles scientific writing. Deliver rigorous, immediately reusable scientific figures and tables with accurate captions, analysis notes, source lineage and a clean handoff.

### Required source-of-truth reading (before coding)

1. `docs/PHASE3_FINAL_REPORT.md`
2. `docs/PHASE3_PRE_REGISTERED_ANALYSIS.md`
3. `docs/PHASE3_FIGURE_INDEX.md`
4. `docs/PHASE3_REPRODUCIBILITY.md`
5. `docs/PHASE3_PREFLIGHT.md`
6. `docs/PHASE25_FINAL_REPORT.md`
7. `configs/phase3_frozen.yaml`
8. `results/phase3/manifests/freeze.json`, `preflight.json`, `smoke.json`, `started.json`
9. `results/phase3/reports/{execution,replay,audit}.json`
10. Existing `results/phase3/{processed,tables,figures}/` and the exact compressed source records in `results/phase3/raw/` and `results/phase3/plans/`
11. `src/star_evrp/{phase3,phase3_analysis,competitive_search,route_evaluator,statistics,scenario_tapes,charge_plan,timing}.py`
12. `results/phase25/{manifest.json,analysis_manifest.json}` for historical/contextual cross-checks only.

Read all current filenames rather than relying blindly on this prompt if later commits reorganized **documentation**. Record the real HEAD SHA, frozen commit and tracked source hashes. Run a clean status check. Never overwrite untracked user files.

### Known Phase 3 aggregates (AUDIT CHECKPOINTS, not values to paste into final tables)

From previously inspected `results/phase3/tables/overall.csv`, the `c64` comparison includes 96 holdout instances from 48 parents, 6,864 total CON routes, **2,321** initially charging-exposed routes, and 4,543 no-charge routes. The main `lower_bound_attained` counts were **B0 1,686; B1 2,052; B2 2,183; B3 2,193; B4 2,161; STaR 2,211; STaR_no_partial 2,096**, each out of 2,321. Mean reliability for B0/B1/B2/B3/B4/STaR/no-partial was about 0.80965/0.95294/0.95213/0.96996/0.96072/0.97314/0.94194. The preregistered STaR–B4 effect is approximately **+0.01242 probability points**, parent-bootstrap interval approximately **[0.00863, 0.01650]**, i.e. **+1.24 percentage points [0.86, 1.65]**. Mean completion difference versus B4 is roughly **−33.15 native time units**. STaR–B3 mean reliability difference is approximately **+0.00319** and average stochastic search draws 13,024 versus 19,911, but STaR search wall runtime is 29.69 versus 27.51 milliseconds. These reference numbers are sanity-check targets only: **derive all Phase 4 tables/figures by independently loading and recomputing from saved outcome records**. Stop and report if they do not reconcile within specified numerical tolerance; do NOT edit frozen records to make them match.

There are 4 experiment profiles: `c64`, `c24`, `s8192`, `c64_seed2`. The full tracked package reports 37,136 saved plan/method/profile combinations, 1,248 hashed raw-and-plan compressed batches, ten existing Phase 3 400-DPI PNGs and eleven current table families. `results/phase3/con_bundles.zip` restores the special `raw/con` directory on a fresh Windows Git clone (`python -m zipfile -e results/phase3/con_bundles.zip results/phase3`). Extract only when necessary; keep contents identical to hashes.

## B. Deliverable structure and strict isolation

Create a new, clearly separate, versioned derived-output tree without changing Phase 3 data:

```
results/phase4/
    figures/main/            # publication figures, PNG only
    figures/supplementary/   # supplementary scientific figures, PNG only
    tables/main/             # matching CSV, .tex and .md bundles
    tables/supplementary/
    data/                    # machine-readable derived audited aggregates
    audit/                   # immutable input hashes, checks, discrepancies
    handoff/                 # compact manifest, captions, usage and sources
    logs/
docs/PHASE4_FINAL_REPORT.md
docs/PHASE4_RESULTS_HANDOFF.md
docs/PHASE4_CAPTIONS_AND_NOTES.md
src/star_evrp/phase4_results.py
scripts/run_phase4_results.py
tests/test_phase4_results.py
```

Use a reproducible script or small modular group of functions; if the real repository structure suggests a clearer layout, document the exact layout. This is **derived analytical/plotting code only**. Do not edit `src/star_evrp/competitive_search.py`, `phase3.py`, physics/simulation code, seed generator, dataset, freeze config, `results/phase3/**`, or the frozen manuscript. Do not change final source/handoff counts to hide failed or missing records. Preserve original historical figures and tables. No separate PDF, SVG, JPG or JPEG figures; requested scientific figure outputs are **PNG only**. The table sources may and should be CSV, LaTeX `.tex`, and Markdown `.md`.

Build a single CLI, e.g.

```
python -B scripts/run_phase4_results.py audit
python -B scripts/run_phase4_results.py build
python -B scripts/run_phase4_results.py validate
python -B scripts/run_phase4_results.py package
python -B scripts/run_phase4_results.py all
```

Support a configurable `--project-root` and `--output` to permit clean replays without overwriting results. Fail loudly on incomplete or invalid input. Do not require the frozen original checkout to be HEAD for read-only auditing of source bundles, but verify them against their frozen manifest and report code provenance honestly. Do not run fresh optimization. Compute the final Phase 4 hashes and include a script version/HEAD SHA.

## C. Independent data/lineage audit — mandatory first gate P4-G0

**Do not merely copy `overall.csv`, `paired.csv`, or published text.** Write an independent reader of compressed Phase 3 `raw/<profile>` and `plans/<profile>` records. You may reuse reliable low-level data structures, but do not call the same summary-producing routine and claim that is independent replication. Implement an explicit crosswalk from the saved record schema to canonical per-original-route observations. Verify:

- Exact frozen manifest and input hashes; 96 holdout instances and 48 parents with both A/B variants; six families with eight holdout parents each. No overlap with the 12 development parents, no result leakage or split mutation.
- All reported CON routes accounted for, with station-exposed route criterion determined **before** repair, not by selected plan topology. Confirm 2,321 exposed, 4,543 no-charge, 6,864 total; retain all B0-unreliable or nonattaining routes without selective removal.
- Unique key for every `(profile, parent, variant, original_route_id, method)`; no duplicates, missing methods, incomplete batches, overwritten results, or mismatched selected-plan file. Every raw record should map to the correct saved ordered charging plan via hash. All methods have the same route denominator in the profile where compared.
- The primary profile has seven methods, while supplementary profiles have B3/B4/STaR only, as frozen. Do not join different profiles or optimizer seeds accidentally.
- Use `successes/n` or saved model validation reliability from the independent **holdout** split, not optimization reliability; validate `n=10_000`, probability in [0,1], Wilson one-sided 95% attainment and two-sided 95% Wilson target-straddling separately. Check sampled customer and depot failures, full-route unconditional completion, native units, and any station-hour flags.
- Verify selected plans' source link, stopping depot, customer order/customer coverage and B4 station-order restrictions by reusing *read-only* validation where feasible. Ensure that archived scalar/reference checks and replay/audit logs agree. Do not claim to have rerun all 37,136 validations if only sampled.
- Recompute all method-level means/counts from raw route rows, and preserve all original-route paired differences for STaR–B4 and STaR–B3, including success, target attainment, unconditional completion, draw count, candidate evaluations, wall time and CPU time. Check scenario counts are incremental and correctly labeled (not equal to wall-clock savings).
- Recompute parent-cluster bootstrap using the **preregistered primary design**: family strata, 48 original parents, parent-bundle resampling of both A/B variants and all routes, 9,999 draws, seed 312406. Recompute the route-weighted primary mean and interval and the parent-equal sensitivity. Make sure `pp` = `100*(probability difference)` when labeling percentage points; never call a 0.0124 probability difference “0.0124%”. Pair same original routes and preserve the same numerator/denominator. Explicitly distinguish the sensitivity estimand.
- Compare the independently reconstructed aggregates against `results/phase3/tables/{overall,paired,population,family_variant,mechanism,robustness,budget}.csv`, and the Phase 3 final report. Use explicit numerical tolerances and document genuine rounding and data-encoding differences.
- Carefully audit the `mechanism` strata: selected-plan topology_changed versus same_topology based on exact ordered station-gap/ID sequence. The association is **descriptive and post-selection**, not a causal estimate of the independent contribution of topology. Verify the weighted stratum effects recombine to the full STaR–B4 mean. Do not make causal statements or claim simple sum decomposes independent interventions.
- Independently read station-file SHA-256 hashes from the frozen manifest, group identical files, and accurately describe the number of distinct station-attribute tables versus number of routing problems. Prior repository inspection found four distinct station CSV contents across 120 A/B problems; verify again. This limits claims of generalization to unseen station-attribute networks.
- Verify raw-and-derived provenance including source filenames, bytes/sha256, data schema version, code revision, and exact math/aggregation function. Produce `results/phase4/audit/lineage.json` and `audit_summary.json`. Track whether any necessary source records are unavailable and exactly what cannot be verified.

**Interpretation sanity checks:** 628 B0 routes have a *point-estimated* reliability below 0.95; this is not the same as the 635 B0 routes that fail the *one-sided lower-bound attainment* criterion (2,321–1,686). Do not conflate these. Zero-charge routes are accounted for in the full-population table but excluded from the charging-exposed primary estimand. The primary 95% cluster interval on a mean reliability difference is not a joint 95% guarantee for each route. Do not present unadjusted secondary bootstrap intervals as confirmatory simultaneously significant tests.

**P4-G0 acceptance:** No missing or duplicate primary observations; all main effects and denominators reconcile; mathematical and statistical labels are correct. If audit fails, preserve original data, write explicit discrepancy report, and prohibit publication-ready labeling for affected exhibits until resolved.

## D. Scientific comparator and outcome integrity audit — gate P4-G1

Inspect frozen code and the saved metadata, not only the final report, and create a compact reviewer-facing truth table for all methods:

- B0 unrepaired original CON;
- B1 deterministic mean-wait surrogate;
- B2 uniform per-visit lognormal quantile surrogate (explicitly label its independence/allocation assumption);
- B3 iterative scenario-based search, using 512 optimization scenarios per scored plan;
- B4 restricted to quantities with original ordered station topology;
- STaR extends to charging topology modifications, targeted criticality ranking and necessary-condition/prefix screens;
- STaR_no_partial charging-quantity ablation with explicitly frozen semantics.

Do not mislabel B1/B2 as consuming no computation simply because they use zero optimizer Monte Carlo draws; report their wall/CPU and deterministic checks. Verify scenario totals, full search time and validations are measured over comparable pairs. Clarify that the 5-second wall guard is cooperative rather than a hard preemption bound. Actual observed per-route wall time is a descriptive machine-dependent metric under six-worker contention. The `s8192` budget is a **scenario cap** with a different candidate-plan cap, so curves must label both dimensions; do not treat `c24`, `c64`, and `s8192` as a clean monotone one-dimensional scenario sweep.

**Critical comparator caveat:** In existing Phase 3 budget data, B4 evaluates about 20 unique plans per route on average under the `c64` maximum of 64, while STaR evaluates about 63. This may reflect genuine fixed-station neighborhood exhaustion and/or implementation design, not a measured equal *number* of evaluated candidates. Quantify with saved records the distribution of consumed candidate evaluations by method, proportion reaching cap, neighborhood exhaustion and work counters. Explicitly explain that matched **maximum budget** does not mean matched **actual work**, nor does this experiment prove superiority to the best possible quantity-only optimizer. Do not change B4 now or reinterpret the untouched holdout.

**P4-G1 acceptance:** Honest method/budget footnotes and counter accounting in every figure/table where needed; positive and negative outcomes preserved; STaR vs B3 not described as a wall-clock speed win.

## E. Publication-grade final figures — gate P4-G2

Inspect existing ten Phase 3 PNGs and their creation functions. Improve genuinely weak plot designs and regenerate **derived figures only** under `results/phase4/figures`; do not edit the frozen originals. Every figure must be built from **audited route/parent-level saved records**, not traced from text, placeholders, manually typed summary values, or generated stock art.

**Technical style:** PNG only, 400-DPI embedded resolution, appropriate physical dimensions for eventual single-column (~85 mm) and double-column (~175–180 mm) conference layouts. Recommended minimum text after reduction ~7.5–8 pt; tick labels non-overlapping; line weights legible at final size; no illegible annotations, clipped labels, misleading axis truncations or rainbow palettes. Use a consistent colorblind-friendly color system and different shapes/line styles for grayscale. White or transparent backgrounds only when readability is preserved. No decorative titles that duplicate captions. No uncited illustrative routes: case studies must use frozen preselected route or an explicitly disclosed descriptive selection rule (not outcome cherry-picking). Use descriptive panel letters when helpful. Correct axes and native time units; `percentage points` for differences versus `%` for probabilities. Error bars need explicit parent-bootstrap or Wilson meaning. Label route counts and parent counts where essential. Never use route-level point-cloud uncertainty as if every point is an independent benchmark replication. Save every figure with a sidecar `.json` or `.csv` data manifest and plotting source hash.

Produce **seven to nine concise MAIN paper figures**, selected for scientific explanatory value, plus supplementary diagnostic figures when valuable. Do not generate ten redundant graphics merely to match the previous count. At minimum cover:

1. **Primary result / paired STaR–B4 reliability:** 48 parent effects and/or route distributions with the preregistered pooled estimate + family-stratified parent-cluster CI. A forest-like panel with family/parent estimates and a global contrast may be more readable than a dense all-route scatter; include an intuitive paired view if it remains legible. State primary denominator 2,321 and estimand.
2. **Method comparison and attainment:** Show B0–B4/STaR and no-partial reliability and 95% lower-bound attainment. Do not imply the mean reliability of a method is the proportion of routes satisfying 95%. Provide the exact number of routes in denominators.
3. **Reliability-versus-completion tradeoff:** Paired STaR–B4 and STaR–B3 deltas with quadrants/zero lines (unconditional full completion), and a clear accounting of trade-offs. This is a *paired route cloud*, not a statistical confidence interval unless bootstrapped at parent level.
4. **Monte Carlo work versus quality:** Distinguish simulation draws and plan caps for c24/c64/s8192/seed2. Avoid connecting incompatible profiles as an interpolated continuous performance frontier. Where appropriate, plot distinct labeled points, optional grouped markers, and valid pointwise parent-cluster interval bars.
5. **Actual wall-clock runtime versus quality:** Explicitly show STaR is *slower* than B3 at c64 despite drawing fewer scenarios; distinguish B4's faster runtime; show CPU as a table if it adds clarity, not as a misleading second axis.
6. **Family / A–B heatmap or small multiples:** Include route denominators and particularly show the hard R2 and RC2 cases. Make color scale comparable across panels and avoid suggesting sample sizes are equal.
7. **Partial charging / topology mechanism:** Exact saved plans and paired metrics for B4 versus STaR, together with no-partial ablation. The topology_changed stratification is associative; label it clearly and show negative cases too.
8. **Robustness and uncertainty:** Separate synthetic 25% waiting scale, 25% sigma scaling, and rho=0.35 copula; all are **fixed-plan stresses without reoptimization**. A separate Wilson-interval near-threshold visualization may fit supplementary materials if page space is tight.
9. **Predeclared illustrative hard route:** Only if readable and informative: `R2_10_2/A/route 0`, the preregistered fixed example. Show precise charging plan/schedule differences and/or the distribution of unconditional route completion; do not pick a new successful case opportunistically.

Figures may combine these intelligently. Keep the primary figures visually uncluttered, and move exhaustive diagnostic plots to supplementary figures rather than compressing all information into one unreadable panel. Build a Markdown index documenting **figure filename → short scientific message → exact source rows/tables → caption → restrictions**. No placeholder/no-data figures; if inputs are missing, audit fails explicitly.

**P4-G2 acceptance:** at least seven meaningful main PNGs, enough supplementary PNGs for key limitations, all 400 DPI, all data-backed, visual inspection of every figure at approximately final paper width, no clipped text, no duplicate content disguised as new evidence, correct statistical encoding.

## F. Publication-ready scientific tables — gate P4-G3

Produce a compact paper table set in `results/phase4/tables/main/`, each with **CSV + LaTeX + Markdown**, using actual audited source records and a consistent display policy for precision, grouping and units. Include concise column names, `n`, uncertainty meaning and descriptions of whether smaller/larger is better. Required MAIN tables:

**T1 Dataset and experimental populations.** 48 holdout parents, 96 A/B problems, 6,864 total CON routes, 2,321 exposed, 4,543 no charge, and family/variant breakdown if space permits. Distinguish 628 B0 point-below-target routes from Wilson nonattainment. Clearly note four distinct station-attribute tables if audit confirms.

**T2 Primary method comparison.** All seven frozen methods on same exposed denominator: mean independent reliability, point-target counts if useful, one-sided lower-bound attainment `x/2321` and percent, mean unconditional full completion, mean optimization Monte Carlo draws, mean actual measured search wall ms; optional CPU and per-method evaluated candidate counts, but don't crowd a single table. Distinguish B1/B2 no MC draws from zero work.

**T3 Paired contrasts / inference.** Registered STaR–B4 as the sole confirmatory effect with mean probability-point and percentage-point delta and 95% family-stratified parent-bootstrap interval. STaR–B3 and no-partial as descriptively exploratory. Provide paired completion deltas, attainment delta and scenarios/runtime in a companion if necessary. Labels: signed STaR minus competitor, positive better for reliability, negative better for completion/time.

**T4 Budget/sensitivity.** The exact c24, c64, s8192 and c64_seed2 profiles, both caps, method, reliability, attainment, work/time, and a brief note that seed2 repeats optimizer noise rather than adding independent benchmark parents. Distinguish matched caps from actual work.

**T5 Family differences and hard cases.** Keep main to six families or 12 family × variant rows; full expanded results in supplementary. Focus R2/RC2, with method denominators and route-level nonattainment. Avoid falsely equal-weighting families while primary estimand is route weighted.

**T6 Mechanism / ablation / robustness.** Could be split among main and supplementary. Quantify partial-charge ablation, topology-change strata, stress-test reliability and attainment for B0/B3/B4/STaR. Explicitly label robustness as fixed-plan, synthetic, no reoptimization.

Supplementary tables: full parent-level effect list, all family/variant counts, run configuration and hardware/dependencies, uncertainty category counts, negative route examples, exact selected charging-stop/energy case detail and any audit warnings. Do not attempt to put tens of thousands of result rows in a paper-sized table. Use `booktabs` optionally if available; for huge supplementary tables `longtable`. Provide safe LaTeX escaping and consistent numerical formatting. Avoid vertical rules, excessive decimal places, long metadata strings and unexplained abbreviations. For each LaTeX file, include either self-contained tabular/table fragment or clearly document required packages, so the writing agent can `\input{...}` without debugging.

**P4-G3 acceptance:** All main/supplementary table values reconcile with frozen raw records, all primary statistical estimands correct, every table has all three formats, LaTeX compiles in a minimal document if local TeX tooling exists (otherwise validate syntax programmatically and disclose no compile check).

## G. Additional descriptive checks only — gate P4-G4

Because the holdout has been viewed, these are **post-hoc descriptive audits**, not a new confirmatory analysis. Compute only from already stored outcomes, with transparent footnotes:

1. Quantify `STaR > B4`, `STaR = B4`, and `STaR < B4` at the level of independent **estimated** route reliability and completion, with robust handling of exact ties and Monte Carlo precision. Include both positive and negative outcomes; avoid declaring per-route true improvement from sampling noise.
2. Break down reasons for STaR failure and lower-bound uncertainty separately (customer-only, depot-only, both, empirical >=.95 but Wilson lower <.95). All 110 STaR nonattaining exposed routes (2321–2211) must be properly accounted for; check that family/variant subtotals sum.
3. Quantify B4 candidate neighborhood exhaustion versus STaR, including distributions (not just mean candidate counts), and whether run caps were reached. Make no claims about optimal quantity allocation beyond this implemented B4.
4. Distinguish differences in Monte Carlo draw count from true computational savings, including screening/prefix overhead, deterministic checks, and actual CPU/wall cost. If you calculate “percent saved”, declare the denominator (usually B3), not a raw difference without context.
5. Check finite validation sampling at the .95 threshold: show one-sided lower-bound attained, point-only attained and two-sided Wilson straddling; be careful that the route-level 95% lower limits do not jointly guarantee all route classifications.
6. Reconcile robustness tables and station-table hashes; make no empirical queue calibration or new-network robustness claims.
7. Include the original pre-registered R2-A case even if visually unattractive. Additional illustrative cases may be supplementary **only if explicitly labeled post hoc** with selection criteria.

No additional training/search, no new random-stress configurations, no new claim of improved algorithm performance. Any figure/table that reports a new descriptive outcome must be labeled exploratory.

## H. Automated validation, manual visual inspection and release audit — P4-G5

Implement a comprehensive `tests/test_phase4_results.py` with synthetic fixtures and, where available, frozen-result integration tests. At minimum test:

1. Correct parent A/B grouping and six-family stratification;
2. Duplicate and missing `(profile,parent,variant,route,method)` records fail;
3. Population conservation: all routes = exposed + zero-charge;
4. Wrong source plan hashes fail;
5. Correct one-sided Wilson attainment, and separation from point estimation;
6. Correct mean of *paired differences* instead of difference of unmatched means;
7. Route-weighted versus parent-balanced estimands are distinct and correctly labeled;
8. Family-stratified cluster bootstrap deterministic for fixed seed, same-input same-output;
9. Probability-point to percentage-point conversion, unit tests for axis/title/caption terminology;
10. Primary preregistered effect exact to tolerance; competing secondary effects correctly classed exploratory;
11. Abbreviations and numerator/denominator reconciliation in every method comparison;
12. B4 quantity-only topology preserved in archived plans;
13. Mechanism group contributions sum to original paired effect;
14. Missing raw input or unsupported profile blocks publication export;
15. Table CSV and TeX values match canonical derived intermediate data;
16. PNG headers, DPI metadata = 400, pixel dimensions, nonzero information content, colorbar/legends when present and no placeholder titles/metadata;
17. Re-running `all` yields the same canonical CSV/derived data and PNG **content hashes** (or documents legitimate unavoidable figure raster metadata variability and verifies numerical content); and
18. Not a single original Phase 3 frozen/raw/config/manuscript file changed before versus after Phase 4.

Run all Phase 4 tests **and** the existing full pytest suite if environment permits. Run the independent audit first and fail on discrepancies. Build images and visually inspect every PNG at natural and reduced final paper widths. If an image is unreadable, regenerate it; no uninspected plot should be described as paper ready. Check clipped text, misleading axes, missing legend, excessive tiny labels, confusing panel order and unexpectedly empty charts. Confirm that every plot's numerical data matches final tables for comparable metrics. Verify actual PNG resolution using image-header/pHYs metadata, not simply the `savefig(dpi=400)` argument. No unnecessary raster rescaling or PDF/SVG exports.

Build a `results/phase4/audit/final_quality_gate.json` recording every gate PASS/FAIL, every generated file SHA-256, validation method, tests, original-frozen-file hash status, known limitations and any unavailable check. No silent warnings. Include dates/software/hardware context only as actually measured; don't reuse Phase 3 timings as if Phase 4 had benchmarked them anew.

## I. Paper-writing-agent handoff — P4-G6

Create `results/phase4/handoff/` with these final artifacts:

- `README_RESULTS_PACKAGE.md`: 1–2 page human-readable guide, source datasets, frozen study design, how to read tables/figures, reproduction command, citation pointers within repo and warning against cross-profile mixing;
- `EXHIBIT_INDEX.csv` (plus `.md`): every main/supplementary figure/table filename, exhibit ID, short message, tested source path, c64 or secondary profile, source hash, caption source, `n` and required footnote;
- `FIGURE_CAPTIONS.md`: precise standalone captions for every selected main PNG, specifying population, comparator, uncertainty method, units, budget, study stage, observational/descriptive status, and limitations. Not a manuscript;
- `TABLE_NOTES.md`: short headnotes, table footnotes and how to report the primary confirmatory effect versus exploratory results;
- `CLAIMS_MATRIX.csv` (plus `.md`): Claim | supporting figure/table | numerical estimate | uncertainty | confirmatory or exploratory | what must NOT be claimed. Include B4 restriction/actual candidate-count caveat and B3 slower wall time;
- `NUMBERS_TO_CITE.csv`: canonical display-ready key numbers with units, denominator, source record/derived table, precision rule and method/profile;
- `LIMITATIONS_FOR_WRITER.md`: concise factual caveats: four shared station attribute tables (if reconfirmed), synthetic independent queues, fixed offline CON customer orders, route-level vs fleet reliability, 10k MC uncertainty, B4 neighborhood limitations, CPU/wall timing, secondary multiple comparisons, no proof of global EVRPTW optimality;
- `MANIFEST.json`: full SHA-256 file list, frozen input references, generation command, code version and gate results.

**Optional:** create `results/phase4/STaR_EVRP_RESULTS_HANDOFF.zip` containing just the final main/supplementary PNG figures, CSV/TeX/MD tables, captions, claim matrix and provenance manifest. Exclude raw original benchmark data and giant compressed Phase 3 experiment batches from the ZIP; link to the repository's audited source tree instead. Test ZIP extraction/listing. The writing agent needs ready-to-insert exhibits, not gigabytes of logs.

The final `docs/PHASE4_FINAL_REPORT.md` should be a concise empirical quality/audit report, NOT a draft paper. Include:

- precise immutable input lineage, dataset and matched population counts;
- checked primary STaR–B4 estimate/CI and explicit B3 trade-off;
- table of all main exhibits with filenames and one-line purpose;
- unexpected discrepancies, whether fixed in derived code or unresolved, and scientific consequences;
- real tests run/pass count, raw record counts, figure DPI validation and visual inspection results;
- gate-by-gate P4-G0 through P4-G6 status;
- exact reproduction commands and handoff package path.

## J. Completion requirement and final response

**Do not stop** until the raw-data audit is complete, all required Phase 4 code exists, all tests and full source-data passes have been run, figures are visually inspected and corrected, tables are consistently exported, handoff files and manifests are created, and all P4 gates are assessed. Do not deliver only code, just a file index, example figures, or a progress report. Resolve missing paths and minor package issues autonomously. If a genuine blocker means some gate cannot be completed, report it precisely; do not substitute fabricated output and do not mark PASS. Never modify the frozen experimental methods or attempt to improve holdout scores. If an audit reveals a scientifically material inconsistency, stop **publication labeling for affected outputs**, preserve all evidence, and give a discrepancy analysis while completing unaffected tasks.

**Final agent reply:** state true PASS/FAIL for P4-G0 through P4-G6; give checked headline numerical findings; count final main and supplementary PNGs, all table bundles, and tests; provide direct local paths for `docs/PHASE4_FINAL_REPORT.md`, `docs/PHASE4_RESULTS_HANDOFF.md`, the final `results/phase4/figures/main/`, `results/phase4/tables/main/`, and handoff ZIP if created. Name limitations honestly. Provide the actual Git commit used for Phase 4 derived code; do not claim the frozen executable was changed or re-frozen.

**Begin immediately. Execute the entire specification autonomously.**
