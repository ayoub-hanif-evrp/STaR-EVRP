# PROMPT 08 — Final conference exhibits refinement and repository cleanup

## 1. Mission

Act as a senior scientific visualization specialist, operations research researcher, and research repository maintainer. Work directly in the STaR-EVRP repository:

- Repository: `https://github.com/ayoub-hanif-evrp/STaR-EVRP`
- Existing conference package: `results/conference/`
- Starting reference: commit `f243297cd60206b7ab75dcd52d38faf8bee73d5e` (November 25, 2026), which published the five conference figures and three tables. Inspect the actual current HEAD first; if newer work exists, preserve it and reconcile the instructions with the current state.
- Frozen optimizer: `star-phase3-freeze-v1`, commit `c657aa69d55178c85b4759475933b36d1bcc2181`.

Finalize the scientific exhibits for a strict **10-page conference paper**, and clean the project of demonstrably obsolete files and folders. Execute the work, not merely propose a plan. The final repository must be cleaner, easier to navigate, reproducible, and ready for a separate manuscript-writing agent.

**DO NOT WRITE THE PAPER.** Do not draft a manuscript, abstract, introduction, related work, conclusion, or paper sections. Existing captions, table notes, exhibit placement notes, README documentation, and technical audit reports may be updated. No manuscript creation is part of this task.

## 2. Non-negotiable scientific constraints

- Keep frozen STaR as the only proposed algorithm. No new search algorithm, hybrid, optimizer tuning, benchmark campaign, solver campaign, or post-hoc change to the registered endpoint.
- Preserve all frozen experimental results, original datasets, selected plans, validation outcomes, manifests, hashes, experiment splits, relevant source code, tests, and provenance. Do not modify historical evidence to make the plots look better.
- Derive all quantitative exhibits from actual archived records. Deterministic reconstruction of existing route traces, arithmetic checks, and replay of previously specified audit checks are allowed; do not run a new stochastic evaluation campaign or optimize new routes.
- Use the original 96-instance holdout (48 parents; 2,321 charging-exposed routes) as the principal comparison population. The full 120-instance benchmark includes development data and is descriptive. The 118-route timing panel is separate and exploratory.
- Keep the registered STaR minus fixed-station repair reliability contrast as the sole confirmatory result: +1.24 percentage points, 95% parent-cluster interval [0.86, 1.65]. Equal maximum candidate budgets do not imply equal consumed work (62.67 vs 20.18 mean trials).
- Preserve the scenario-search comparison (+0.32 pp, exploratory; 34.59% fewer search draws at the original budget, but 29.69 vs 27.51 ms elapsed). Do not claim a general speedup or formal noninferiority.
- Reliability means the modeled probability of satisfying every customer service-start deadline and the depot deadline. Completion is unconditional full depot-return time, including late trajectories. Attainment means an individual one-sided 95% Wilson lower bound of at least 0.95, not a guarantee for every route or the fleet.
- Preserve disclosures: fixed customer order, deterministic travel and energy use, linear charging, synthetic lognormal station waits, disabled station hours, four station-attribute tables shared across partitions, no endogenous congestion or recourse, and no proof of global superiority.
- Treat the complexity strata, ablations, timing panel, and Phase 6 analytical/fixed-topology results as exploratory. Do not interpret subgroup associations as causal.
- Do not hide negative results or remove scientific records because a result is unfavorable to STaR.

## 3. Preflight: inspect before modifying

1. Record current branch, HEAD, working-tree status, tracked/untracked inventory, file sizes, and available build/test environment. Do not overwrite unrelated user changes.
2. Read the current README, `docs/CONFERENCE_EXHIBITS_REPORT.md`, `docs/PHASE5_FINAL_REPORT.md`, `docs/PHASE6_FINAL_REPORT.md`, conference captions, table notes, claims, traceability, manifest, audit files, and exhibit-generating code.
3. Inspect the existing five PNGs and their vector versions, three table bundles, figure-source CSV/JSON files, and generation scripts. Inspect the actual images, not just metadata.
4. Establish a protected-path inventory and SHA-256 baseline covering the historical scientific evidence. In particular, check the existing preservation manifest (the previous release checked 5,297 protected paths). Add any new dependencies discovered at current HEAD.
5. Identify dependencies by inspecting imports, scripts, config paths, manifests, archive members, README/docs links, tests, and Git references. Use this inventory later for cleanup; never infer that a file is useless from age alone.
6. Keep a clean build output outside the existing authoritative results until checks pass. Record the starting revision and the environment so the final release can be reproduced.

## 4. Publication architecture

Keep exactly **five main figures and three main tables**. Any additional illustrations belong in a clearly labeled supplementary directory. Assume the ten-page limit includes references unless a supplied venue template says otherwise. Design main figures for the existing 178 mm full-width layout; also verify reduced-scale legibility. Do not claim that final pagination has been verified without the actual conference template.

Use these existing main exhibit stems, unless an unavoidable migration is documented:

| Exhibit | Purpose |
|---|---|
| Fig01_spatial_charging_repair | Actual benchmark geography, matched charging plans, battery evolution |
| Fig02_star_framework | Visual explanation of the frozen search and charging operators |
| Fig03_paired_reliability | Primary effect and observed paired directions |
| Fig04_charging_complexity | Structural benefits and residual nonattainment |
| Fig05_quality_simulation_effort | Separate controlled timing-panel evidence |
| Tab01_experimental_configuration | Compact experimental setup |
| Tab02_method_comparison | Six-method holdout comparison |
| Tab03_component_ablation | Four component removals and full STaR |

If eventual page layout is tight, Figure 5 is the first candidate for supplementary placement. Its essential numerical disclosure must still remain available in the writer notes. Do not add a sixth main figure or a fourth main table.

## 5. Figure 1 — spatial charging repair and battery state

### Main route

Keep the current outcome-selected holdout example `C1_10_3/A`, route 106, with ordered customers 851 then 731. This route was selected by the documented Phase 7 rule; do not silently replace it. The original visit to station 1253 occurs after the last customer, and the repaired visit to station 1248 is before the first customer. Reconcile against actual saved route plans and coordinates, rather than relying solely on this prose.

Retain the three spatial panels: entire instance, original route, repaired route. Use equal aspect ratios, identical detail limits, visible direction arrows, consistent customer/station/depot symbols, and concise annotations identifying the removed and added station and charging quantities.

The expected archived values are:

| Metric | Original route | STaR |
|---|---:|---:|
| Successes / 10,000 | 3,063 | 10,000 |
| Estimated reliability | 30.63% | 100.00% |
| Energy charged (native units) | 447.460174... | 69.078315... |
| Mean full return (native units) | 1,826.215858... | 1,394.793291... |

Use source precision and appropriate display rounding. Label the 100% as **observed/estimated reliability**, not guaranteed true reliability. Explicitly identify this example as outcome-selected, not representative of the benchmark.

### Battery profile — required

Reconstruct the actual deterministic battery state from both saved plans using the frozen physics and validator. Add a compact fourth panel or lower strip if legible; otherwise put the full profile in a supplementary exhibit and retain a concise physical explanation in Figure 1.

- Plot battery energy versus cumulative traveled distance in native units. Each plan has its own distance axis progression because charging detours differ; do not falsely align distances or imply identical physical paths.
- Start at the model's initial battery capacity, show consumption along legs, arrival and departure energy at stations, vertical charging increments, and final residual energy. Annotate customer visits and charging events without crowding.
- Show the capacity and zero-energy reference, and check numerical tolerance against the frozen validator. Do not invent an additional safety reserve.
- Use the same physical units and scales for both plans. Include a note that customer order is identical, not the charging sequence or geometric route.
- Verify that the trace matches the archived plan and deterministic energy accounting. Compare total energy added and consumed, station positions, and final battery. Preserve full-precision source CSVs.
- Explain the large charge reduction using the actual physics. Do not attribute it entirely to lower waiting times; charging duration, travel distance, station rates, and readiness floors may all contribute.

Where useful, add a compact supplementary timing/slack profile from deterministic zero-wait traces or archived stochastic summaries. Clearly label the distinction; do not fabricate a new scenario or stochastic trajectory.

## 6. Supplementary complex route example — required

Create `Sup01_complex_route_repair` in a supplementary directory. The simple two-customer example is helpful pedagogically but does not demonstrate the multi-visit routes that account for most of the reliability gain.

Select a real holdout route with at least three original charging visits, preferably from R2 or RC2. Define a deterministic selection rule before rendering: prefer a route that improves reliability, changes topology, and attains the target after repair; within the eligible set use a deterministic ordering (for example, median eligible customer count with parent/variant/route ID tie-breaks). If that set is empty, document a pre-specified fallback hierarchy. An outcome-dependent rule must be explicitly labeled outcome-selected and exploratory. Do not describe the example as representative or use it as evidence of average performance.

Generate matched before/after spatial maps, actual charging visits and quantities, observed reliability, full return, and a battery profile if readable. Use consistent scales, direction markers, station numbering or event sequence annotations. If the route is visually dense, use a clearly marked spatial zoom and a charging-event table rather than hiding visits.

Additionally prepare a compact failed or deteriorated route diagnostic as an optional supplementary exhibit if the existing records support it. The archived worst route-level differences can be severe; investigate the selected example from stored data without new optimization. Distinguish observed facts from hypotheses about the search mechanism. Do not cherry-pick successful examples as proof of universal improvement.

Store the exact source route IDs, selection criteria, candidate counts, plan digests, node coordinates, event records, and metric lineage. Provide PNG/PDF/SVG, caption, and source data for supplementary figures that are released.

## 7. Figure 2 — STaR optimization framework

Redesign the current text-heavy flowchart as a concise, scientifically precise visual explanation. Replace “Start from CON” with “Start from original route”. Use one branded algorithm name: STaR.

Retain the actual frozen workflow:

1. Start from a feasible ordered original plan and score it on the shared 512-draw search tape.
2. Rank charging visits by marginal isolated-wait risk and prioritize nearby customer gaps.
3. Interleave quantity adjustments/transfers and topology edits; generate candidate charge allocations.
4. Reject duplicates and energy/zero-wait timing infeasibility as implemented; preserve actual budget accounting.
5. Apply analytical screening only when its incumbent condition holds. The screen bounds true fixed-plan reliability; empirical reliability on a finite tape may exceed that bound.
6. Evaluate a 128-draw prefix, apply the optimistic fixed-tape score bound, and extend surviving candidates to 512 draws.
7. Compare complete scores using the true implemented lexicographic order: target attainment first; above target minimize full completion with reliability tie-break; below target maximize reliability with completion tie-break.
8. Strict improvement updates the incumbent and restarts the neighborhood. Rejected/non-improving candidates advance to the next proposal while guards permit. Stop on exhausted proposals or guards, return incumbent, then perform independent final validation.

Add mini-schematics of actual move types: station replacement, relocation across customer gaps, insertion, removal, charge quantity adjustment, and energy transfer/partial allocation. Visually preserve customer order and distinguish station identity from position. Do not draw an operator that is not in the frozen code. The diagrams must be editable vector primitives and may be conceptual, explicitly distinguished from empirical route plots.

Use fewer words per box; put detailed conditions in the caption/notes. Ensure arrows unambiguously communicate bypass, retry, restart, and termination. Verify the diagram against the frozen code with source-line traceability. Do not present the analytical single-visit optimizer or fixed-topology MILP as components of STaR.

## 8. Figure 3 — paired reliability

Make only necessary improvements to the existing strong figure.

- Keep the registered fixed-station repair contrast prominent: +1.24 pp [0.86, 1.65]. Keep the scenario-search contrast +0.32 pp [0.13, 0.49] clearly exploratory.
- Name panel (b) explicitly as observed directions **versus fixed-station repair**, with 160 higher, 2,050 equal, and 111 lower on the 2,321-route holdout. Ties mean equal observed successes out of 10,000, not proved equality of true probabilities.
- Retain all uncertainty intervals and a zero-reference line; use percentage points (pp) and define the unit in the caption.
- Tighten excess whitespace only if it improves legibility. Do not add a redundant bar chart or change statistical estimands.
- Explain in the caption that the intervals use the archived family-stratified parent-cluster bootstrap and that the primary comparison shares a maximum budget, not equal consumed work. The main table or its notes must disclose the actual trial counts.

## 9. Figure 4 — charging complexity

Retain the paired two-panel design and the holdout-only strata. Check the following against the authoritative CSV:

| Original station visits | Routes | STaR minus fixed-station repair (pp) | Exploratory 95% interval (pp) | STaR nonattainment |
|---|---:|---:|---|---:|
| 1 | 1,587 | +0.18 | approximately [-0.001, 0.392] | 4 |
| 2 | 159 | +0.18 | approximately [0.024, 0.373] | 4 |
| 3+ | 575 | +4.46 | approximately [3.294, 5.720] | 102 |

The 3+ group is 24.8% of exposed holdout routes, contributes about 89.0% of the **net signed** overall improvement over fixed-station repair, and accounts for 102 of 110 residual STaR nonattainments. Preserve the subgroup parent counts and denominators. Do not mix in the 120-instance pooled estimate of 90.7% or its +4.88 pp subgroup effect.

Add concise numerical point labels where legible. Use a heading such as “Routes not attaining the target” instead of opaque jargon; define the Wilson criterion in the caption. Avoid rounding a slightly negative lower interval endpoint to a misleading strictly positive value. Include the zero line and distinguish observed associations from causal explanations.

## 10. Figure 5 — quality versus simulation effort

Keep the existing separate 118-route panel (23 development, 95 holdout; 60 parents; three serial repeats per route/method/guard, 2,124 runs total). Explicitly name the 20, 50, and 100 ms values as **cooperative runtime guards**, not hard deadlines. Keep the work-quality scatter and paired reliability intervals; do not join discrete budget observations into an implied continuous frontier.

At the 50 ms guard, expected archived results are about 18,696 versus 33,699 search draws (44.52% fewer with STaR), STaR minus scenario search reliability -0.134 pp with interval [-0.510, +0.087], and paired mean of route-median wall differences +0.233 ms with interval [-1.018, +1.461]. Both intervals include zero. Disclose overshoots (122/354 STaR repeats, 117/354 scenario-search repeats) and the absence of demonstrated wall-time superiority. Use source precision; do not claim equivalence.

Make the figure understandable without abbreviations, label the separate population on the figure or subtitle, distinguish methods and guards with markers in addition to color, and keep it suitable for optional supplementary placement.

## 11. Tables — concise and consistent

### Table 1: experimental configuration

Keep essential configuration only: 120 instances, 1,000 customers per instance, 24 development/96 holdout instances, parent counts, 6,864 holdout routes including 2,321 charging-exposed routes, Q=700, h=1, Euclidean travel, linear heterogeneous charging, independent synthetic lognormal waits, fixed customer order, disabled station hours, 95% reliability target, 64 unique candidate maximum, 512 search scenarios per fully evaluated stochastic candidate, 10,000 independent validation draws, one-sided Wilson attainment, and 9,999 parent-cluster bootstrap draws. Record additional budgets and native units in compact rows or notes. Verify against frozen protocol, not this summary alone.

### Table 2: main method comparison

Keep only the six main methods, in this order:

| Method | Mean reliability (%) | Attained | Full return | Search draws | Wall (ms) |
|---|---:|---:|---:|---:|---:|
| Original route | 80.97 | 1,686 | 3,391.25 | 0 | 0.22 |
| Mean-wait repair | 95.29 | 2,052 | 3,133.83 | 0 | 27.39 |
| Quantile repair | 95.21 | 2,183 | 3,135.71 | 0 | 27.45 |
| Fixed-station repair | 96.07 | 2,161 | 3,168.98 | 4,257 | 8.38 |
| Scenario search | 97.00 | 2,193 | 3,137.43 | 19,911 | 27.51 |
| STaR | 97.31 | 2,211 | 3,135.83 | 13,024 | 29.69 |

Recompute display rounding from full-precision archived values. Add actual mean unique candidate trials for all applicable methods if the table fits; otherwise provide the complete counts in the accompanying table notes and prominently disclose the 62.67 vs 20.18 comparison. Do not confuse a candidate trial with a scenario evaluation. The original unoptimized plan is not a comparable repair-search runtime; zero stochastic draws for deterministic methods are genuine, not missing values. If using bold for best results, define whether it applies among all rows or only active repair methods, preserve ties, and do not misleadingly emphasize a trivial zero/no-search baseline. Keep both full return and elapsed time, even where STaR does not win.

### Table 3: component ablation

Keep the full STaR row and four removed components, with descriptive names. Expected holdout results:

| Component removed | Mean reliability (%) | Attained | Search draws | Reliability loss (pp) |
|---|---:|---:|---:|---:|
| None (full STaR) | 97.31 | 2,211 | 13,024 | — |
| Partial charging | 94.19 | 2,096 | 8,400 | 3.120 |
| Slack prioritization | 97.01 | 2,197 | 13,080 | 0.308 |
| Analytical screening | 97.31 | 2,207 | 13,569 | 0.007 |
| Progressive evaluation | 97.31 | 2,211 | 18,927 | 0.000 |

Where space permits, include a signed difference in search draws relative to full STaR, or report the differences in the note. Use paired unrounded archive data for confidence intervals, if added; keep them exploratory, pointwise and unadjusted. The no-progressive-evaluation ablation has identical recorded reliability, attainment and full return, while full STaR saves approximately 5,903 search draws per holdout route. Do not claim elapsed savings from cross-cohort timing. Note that partial charging removal bundles quantity moves and partial allocation for new topology edits. Slack prioritization has a modest holdout improvement but reverses sign in development.

All table formats must agree: full-precision CSV, readable Markdown and compilable LaTeX. Include units, denominators, metric directions, definitions and necessary caveats in concise notes. Do not add AS1 or FT-SAA to the primary comparison table; keep their exploratory results and limitations accessible in the supplement/writer notes.

## 12. Terminology and visual design system

Only STaR should be a branded method acronym in the main exhibits. Use standard mathematical symbols only where defined. Internal keys, filenames and historical records can retain their original identifiers.

| Internal label | Public-facing label |
|---|---|
| CON | Original route |
| MWR | Mean-wait repair |
| QBR | Quantile repair |
| FSPC | Fixed-station repair |
| SLS | Scenario search |
| NPC | Without partial charging |
| NSP | Without slack prioritization |
| NAS | Without analytical screening |
| NPP | Without progressive evaluation |
| AS1 | Analytical single-visit optimizer (supplement only) |
| FT-SAA | Fixed-topology optimizer (supplement only) |
| c64 | 64-candidate budget |
| LB/nonattainment | Reliability target attainment / routes not attaining the target, with definition |

Retain the established navy/slate/teal/amber visual language where effective: STaR teal `#0D9488`, baselines slate `#64748B`, charging stations amber `#D97706`, labels/depot navy `#1E293B`, optional spatial highlight blue `#2563EB`. Distinguish categories with shapes, line styles, labels or patterns as well as color. Use restrained grids, white backgrounds, consistent typography, aligned panels, readable legends, modest panel headings, and no decorative gradients or 3D effects. Avoid unnecessary numerical precision on figure faces; use exact values in source data.

Export every final main and supplementary figure as 400 DPI PNG, vector PDF with embedded fonts and extractable labels, and editable SVG. Prefer native vector paths and text over rasterized plot elements. Check legibility at actual full width, at reduced width, and in grayscale. Inspect actual rendered pages, not merely automated format metadata.

## 13. Project cleanup — required, conservative and evidence-preserving

Perform a real cleanup after dependency inventory and before final packaging. The goal is to **delete old useless files and folders**, not to remove the scientific record or rewrite history.

### 13.1 Inventory and classification

Create an inventory of cleanup candidates, with exact path, size, tracked/untracked status, last known purpose, dependency/references found, classification, reason, and proposed action. Classify into:

- **Protected:** necessary for experiments, archived evidence, provenance, current or historical reproduction, public links, tests, legal attribution, or conference generation. Keep unchanged unless explicitly authorized.
- **Active:** current source, scripts, tests, configurations, documentation, conference figures and data, and their dependencies. Keep.
- **Obsolete and safely removable:** disposable build intermediates, caches, scratch outputs, abandoned empty directories, duplicate generated files with a verified canonical copy, stale local exports or temporary workspaces with no remaining references. Delete after checks.
- **Uncertain:** old code, historical figures, reports, prompts, data, or folders whose significance/dependencies cannot be established. Keep and record why; do not guess.

### 13.2 What to remove

Inspect for, and remove when proven unnecessary: `__pycache__`, `.pytest_cache`, temporary interpreter/plot caches, build scratch, temporary PDF rendering or table compilation files, abandoned proof directories, stale untracked repeat/rebuild directories, accidental export duplicates, empty placeholder directories, orphaned temporary logs, and redundant generated assets that have a verified authoritative equivalent and are not manifest-bound or linked. Remove tracked obsolete files using explicit path-level Git operations only after verifying they are not protected. Update `.gitignore` narrowly to prevent recurrence; do not ignore authoritative results or raw inputs.

These are candidate classes, not blanket permission to remove every directory that matches a name. A rebuild or proof directory may contain unique audit evidence; check before deletion. A ZIP may be the only complete baseline archive; do not delete it because extracted files exist. Do not remove any file merely because a newer figure exists.

### 13.3 Explicitly protect

- Original benchmark dataset, metadata, license and citation files.
- `star-phase3-freeze-v1` tag and all history; do not rebase, force-push, rewrite tags or purge Git objects.
- Phase 1–6 authoritative outcomes, their raw/compressed records, plan archives, original CON bundles, validation summaries, splits, configuration, analysis protocols, manifests, audit evidence, scientific reports, and historical figures/tables referenced by them.
- Source modules, scripts and tests required by any supported reproduction workflow, even if they are not used by the conference build.
- Prior prompts or notes that establish experiment provenance and selection rules. Preserve historical records; only delete an unreferenced exact duplicate if its canonical source is verified and no protected checksum references it.
- Existing current conference package and its generator, except for the intentional reviewed replacements described in this prompt. Preserve the previous conference release via its Git commit and record the replacement lineage.
- User work, uncommitted changes, credentials, environment files and any external/sibling directory. Do not modify or delete user files outside the project. Never use broad destructive commands such as `git clean -fdx`, blanket `rm -rf results`, or uncontrolled recursive deletion.

### 13.4 Execute and verify cleanup

Use explicit verified paths; do not follow symlinks outside the repository. Review the deletion list against protected paths, manifests, imports, scripts, test references, README links and archive references before execution. Delete demonstrably obsolete files/folders in the current working tree. Keep ambiguous historical artifacts. If a protected file is a potential cleanup candidate, list it for future human review rather than removing it.

After deletion, record before/after tracked and untracked file counts and measured size reduction (separate checkout size from Git history size). Report every deletion or provide a machine-readable inventory with exact paths, reasons and sizes. Confirm no broken links or missing build inputs, run the protected-path SHA-256 verification, and verify current and relevant historical workflows still resolve their inputs. If deletion breaks any required check, restore the affected file from its verified source, document the rollback, and rerun affected checks. Do not claim disk-space savings from Git history unless measured; deleting tracked files from HEAD does not remove their history.

Update README navigation to foreground the conference package and group historical evidence clearly without duplicating or moving protected data. Preserve accurate reproduction commands and historical links. Do not physically move archival trees just for aesthetic organization if it would break manifests or reproduction.

## 14. File organization and traceability

Use the existing `results/conference/` directory and build infrastructure rather than creating competing packages. Suggested extension:

```text
results/conference/
  figures/                       # five main stems, PNG/PDF/SVG
  tables/                        # three main stems, CSV/MD/TEX
  supplementary/                 # complex route and extra physical diagnostics
  data/                          # exact main and supplementary source CSV/JSON
  audit/                         # preservation, numerical, render, compile, test checks
  FIGURE_CAPTIONS.md
  TABLE_NOTES.md
  METHOD_GLOSSARY.md
  SOURCE_TRACEABILITY.md
  CLAIMS_AND_LIMITATIONS.md
  EXHIBIT_INDEX.csv
  MANIFEST.json
  README_RESULTS_PACKAGE.md
  PAPER_OUTLINE.md               # exhibit placement only; no manuscript drafting
  STaR_EVRP_CONFERENCE_EXHIBITS.zip
```

Update the existing generator, audit code and focused tests as necessary; do not manually edit rendered exports without updating their reproducible generation path. Each exhibit must have the exact source path, record key/route ID, cohort, computation/rounding rule, relevant digest, caption, physical size, and output filenames. Include supplementary assets in manifest/index and ZIP; verify the archive can be extracted safely. Use existing package conventions and document any deliberate structural change.

Create a short technical release report, e.g. `docs/CONFERENCE_EXHIBITS_REFINEMENT_REPORT.md`, and a machine-readable cleanup inventory under the existing audit directory, plus a concise cleanup summary. The report should describe modifications, preserved evidence, deleted files, checks performed, limitations and any optional remaining work. This is technical documentation, not manuscript writing.

## 15. Acceptance gates

Do not declare completion until every applicable gate passes or is explicitly marked blocked with reason and evidence.

| Gate | Required evidence |
|---|---|
| G0 — Preflight | Current HEAD, clean/safely handled working tree, dependency inventory, protected hashes, recorded environment |
| G1 — Spatial and physical correctness | Actual route IDs and node data; unchanged customer sequence; exact visit/charge records; reconstructed energy traces match frozen validator; honest example selection |
| G2 — Scientific reconciliation | Six main methods and four ablations; holdout totals, intervals, directions, subgroup counts and timing panel match source records; no new claims or experiments |
| G3 — Visual quality | All actual PNG and vector exports inspected at full and reduced sizes and grayscale; no clipping, collisions, unreadable labels or misleading axes |
| G4 — Table quality | All three LaTeX fragments compiled at intended width using the available proof harness; CSV/MD/TEX numerical agreement and readable output |
| G5 — Cleanup safety | Explicit deletion inventory, protected hash reconciliation, no missing required dependencies or broken relevant links, measured cleanup, no history rewriting |
| G6 — Tests and repeatability | Run focused and full test suite; build twice in clean directories and compare deterministic outputs/hashes (disclose unavoidable metadata differences); reject missing required input |
| G7 — Handoff integrity | Final captions/notes/index/manifest, source traceability, verified ZIP extraction and file hashes, accurate README, technical report |

Use the existing scripts and commands where possible, including `scripts/build_conference_exhibits.py`, the focused conference tests, and `python -B -m pytest -p no:cacheprovider -q`. Inspect the current CLI before invoking arguments. The previous release recorded seven focused and 99 full-suite tests; these are historical numbers, not a target to report without actually running the updated tests. Preserve original audit evidence and clearly separate this refinement's fresh logs. Do not falsify tests, visual reviews, byte-identical rebuilds, or compiler outcomes. If the venue template is absent, state that final paper pagination is not tested.

## 16. Final deliverables and reporting

Deliver the five revised main figures, three revised main tables, at least one actual complex-route supplementary figure, actual battery traces for the main example (integrated or supplementary), and supplementary physical/timing details where supported. Provide all agreed formats and exact source files, captions, notes, manifests, reproducible generator changes, verified package, and technical release report.

Finish with a concise factual summary of:

- Starting and final Git revisions (if committed), what was modified and which files were deleted.
- Main/supplementary exhibits and links or paths to the complete package.
- Numerical and scientific evidence preserved, plus any newly derived descriptive diagnostics and their limitations.
- Cleanup totals and measured size change, protected-hash result, and items retained because their status was uncertain.
- Actual test results, compilation, visual review, deterministic rebuild and archive checks; any failures, blockers or unverified items.
- Any decisions made without explicit guidance, such as supplementary route selection or battery panel placement.

If authorized and Git write access is available, use a clear non-destructive commit for the refinement and cleanup (separate commits are preferable if useful for review). Do not push over remote changes or bypass protections. If writing/pushing is unavailable, state the limitation and deliver the local changes or patch; never claim a remote update that did not occur.

**Stop when the conference exhibit package and repository cleanup are complete. No paper writing. No new optimization methods. No new benchmark campaigns.**
