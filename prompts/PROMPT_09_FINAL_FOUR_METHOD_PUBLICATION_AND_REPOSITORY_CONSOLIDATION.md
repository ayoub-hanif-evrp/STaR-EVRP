# PROMPT 09 — Final four-method publication package and repository consolidation

## 1. Mission and authority

Act as the final scientific-visualization engineer and repository maintainer for STaR-EVRP. Execute this task in the existing repository, not merely as a proposal.

- Repository: `https://github.com/ayoub-hanif-evrp/STaR-EVRP`
- Last reviewed revision: `1ad987a328679263e5d8ba40330ffe1a11409db1` (Phase 8 refinement, 2026-11-25). Inspect current HEAD before making changes; preserve any intervening user work.
- Frozen research implementation: `star-phase3-freeze-v1` / `c657aa69d55178c85b4759475933b36d1bcc2181`.
- Existing publication package: `results/conference/`.
- Intended paper: compact 10-page conference paper. Actual venue template is not supplied; do not claim final pagination.

The user has made three binding decisions that **supersede Prompts 7 and 8**:

1. The only methods in the active publication comparison figures and tables are CON, MWR, QBR and STaR. STaR is our sole proposed method. The four STaR component ablations are permitted in the component study, not marketed as independent methods.
2. Every delivered figure contains at most TWO visual panels. Do not generate any methodology figure or algorithm workflow, operator illustrations or schematic: the author will make the methodology illustration personally later. Deliver exactly FOUR main figures and THREE main tables, no additional generated figures or tables for the manuscript.
3. Consolidate the repository into a small, understandable active research/publication workspace. Remove obsolete tracked phase folders, duplicate derived outputs, obsolete scripts/docs/configs/prompts, empty markers, local scratch and caches **where safe**. Preserve the ability to recover and reproduce the full historical scientific study. Do not simply create another permanent phase folder full of duplicate outputs.

**Do not write the manuscript. Do not optimize routes, run new experiments, change STaR, tune parameters, introduce methods, or generate new validation scenarios.** Deterministic checking of existing data and aggregation of archived results are allowed. The user wants final publication materials, not more research phases.

## 2. Scientific contract: non-negotiable

Use the 96-instance original holdout, 48 parent blocks and 2,321 charging-exposed routes for every main quantitative results exhibit. The 120-instance benchmark includes 24 development instances; report its coverage and preserve its results, but never call it a new holdout. Counts: 120 instances/60 parents, 8,606 original routes, 2,891 exposed; holdout 6,864 original routes, 2,321 exposed, 4,543 unchanged no-charge; development 1,742 original routes, 570 exposed. Do not mix populations or search profiles to obtain more attractive figures.

Use frozen primary c64: maximum 64 distinct trials (including starting plan), 131,072 incremental search draws, 5 s cooperative guard, 512 scenarios for a full stochastic score, 128-scenario prefix for STaR, 3 nearby eligible stations; search seed 20261122, separate 10,000-draw final validation seed 20261123. Battery capacity 700, energy consumption 1, fixed customer assignments/order, deterministic travel and energy, linear heterogeneous charging, independent synthetic lognormal visit waits, station hours disabled. No endogenous congestion, fleet-wide guarantee or dynamic recourse. Four station-attribute tables reused across development and holdout. Keep native units. Completion means unconditional full return including late scenarios. Attainment requires the individual one-sided 95% Wilson lower confidence bound >= 0.95; not simply estimated reliability >= 95%. Search draws exclude final validation. Use matched route keys and parent-cluster inference; 9,999 family-stratified bootstrap replicates, seed 312406, keeping A/B and all routes of a parent together. The archived primary c64 scenario ceiling cannot bind (64 x 512 maximum).

The sole registered contrast remains STaR minus FSPC +1.24 pp [0.86, 1.65] on the original holdout. This cannot be replaced by a more favorable result after the holdout is opened. The three displayed benchmark contrasts are exploratory. The actual work differs (62.67 vs 20.18 trials for STaR and FSPC). Keep all previous results and caveats recoverable. In a separate text-only writer disclosure, retain the FSPC result and SLS trade-off (+0.32 pp, exploratory, 34.59% fewer search draws but 29.69 vs 27.51 ms); Phase 6 equal nominal guard comparisons and AS1/FT-SAA limitations. No assertion of superiority over optimal fixed topology, general runtime advantage, noninferiority, or causal subgroup mechanisms. Do not put these four extra methods in the new figure legends, plotted series, or table rows. This is a presentation decision, not a scientific exclusion or deletion. The writing agent must cite/discuss the registered contrast and materially qualifying comparisons in prose and link the full archive. Do not conceal negative findings.

## 3. Preflight and dependency audit BEFORE deleting anything

1. Record current branch, HEAD, remote, status, staged/unstaged/untracked/ignored inventory and file bytes. Verify the immutable freeze and latest Phase 5/6/8 release checksums. Do not overwrite unrelated changes. Inspect the actual existing PNGs, not just metadata.
2. Read the current README, `docs/CONFERENCE_EXHIBITS_REFINEMENT_REPORT.md`, Phase 3 preregistration, Phase 5 and 6 final reports, mathematical audit, the current conference generators, source-traceability and audit records. Identify actual entry points, imports, data references, config dependencies, tests and documentation links. The last reviewed repository has `results/{baselines,conference,figures,manifests,phase2,phase25,phase3,phase4,phase5,phase6,processed,raw,reports,tables}`, numerous phase-specific docs/configs/scripts and historical prompts. Some of these ARE required by current readers, so do not blindly delete them.
3. Establish an immutable, recoverable archival reference to the entire pre-consolidation research release. Prefer a descriptive archival Git tag such as `star-research-archive-v1` on the actual reviewed pre-cleanup commit, pushed and verified on the remote if authorized. Never move an existing tag. Retain the existing freeze tag. Record exact commit IDs and tree hashes. If a new tag cannot be published, verify that the existing archival commit is permanently reachable from the current remote history and document the recovery path; if durable recovery is uncertain, keep the affected scientific files rather than delete them. Do not rewrite Git history, force-push, prune reachable objects or remove the archive to save space.
4. Historical tracked evidence is recoverable only after checking actual remote reference/commit reachability, representative archive members and manifest hashes. Unique untracked/ignored research files are not protected by Git history: inspect them, distinguish disposable files from unique evidence, and preserve unique files with a verified safe backup before any removal. Do not commit unrelated personal files, secrets, environment files or unknown data. Record blocked or ambiguous paths. For example, the nine differing notebook checkpoint files previously retained must not be treated as harmless duplicates without checking their contents and provenance.
5. Make a deletion/migration ledger: path, type, tracked status, byte size, reason, dependencies, archival reference or equivalent surviving path, verification, action. Before recursive deletion, resolve paths under the repo root; check symlinks/junctions/reparse points, tracked children and unexpected contents. Never delete `.git`, external targets, the original dataset, or unique scientific evidence without verified recovery. Use normal permissions; do not escalate destructively to bypass denial.
6. Build the new publication package in a temporary separate directory. Only replace the authoritative active package when the full build, test and visual review pass. Capture original package hashes and leave it recoverable through the archival reference.

## 4. Canonical final publication design

Use exactly these four figure stems, renumbered from 01 to 04. These numbers are provisional for the writer, who will insert their own methodology figure later. No empty methodology placeholder, no fifth image, no standalone operator sketch. Remove the old active methodology figure and all its exports/sidecars and generator paths that are no longer needed; it is recoverable from the archive. Remove prior supplementary illustrations from the active publication package, including the adverse comparison against FSPC; preserve those images and source data in historical Git. Keep the negative-case evidence in the text disclosure, with exact archival links.

### Fig01_spatial_charging_repair — exactly two matched route maps

- Panel (a) CON, panel (b) STaR. Use the actual archived `C1_10_3/A/106` route (customers 851 then 731) previously selected by documented outcome-based rule. It is concise and visually explains the repair. Do not silently switch to another handpicked route. If archived data integrity fails, stop and document rather than fabricate.
- Actual Euclidean coordinates, identical x/y limits, equal aspect, identical ticks and node positions, fixed customer order, arrows for travel direction, consistent symbols (customer circle, station square, depot diamond). Original line dashed/slate, repaired solid/teal. Include only the necessary depot, customers and visited stations; optional unvisited stations may be shown as very faint background only if useful and not cluttered. No full instance map, battery chart, inset, tiny operator diagrams, third panel or hidden nested subplot.
- Use actual station IDs and charge values (old 1253 after customer 2, 447.46 units; new 1248 before customer 1, 69.08 units). Label observed reliability 30.63% vs 100.00% (3,063 and 10,000 successes out of 10,000); compact annotation, not big metric cards. Completion 1,826.22 vs 1,394.79 native units can be caption-only. The observed 100% is not theoretical certainty. State outcome-selected illustration, not representative evidence. Preserve actual saved plan IDs, coordinates and source hashes. Existing battery/physical ledger may remain as compact source data or text notes, not a new figure.
- Use side-by-side maps with shared legend (or direct labels), adequate margins, no enormous whitespace. Aim 178 mm width and ~65–85 mm height when practical. Do not distort equal aspect to force height.

### Fig02_comparative_reliability — two simple panels

- Panel (a): mean route reliability of CON, MWR, QBR, STaR. Use simple zero-based bars (or clearly labeled point estimates on a full 0–100% scale), one color per method with STaR visually emphasized. Label mean values to two decimals. No 3D, pies, gauges, dual axis or exaggerated scale. The reference target may be drawn at 95%, with caption clarifying it is an individual target, not a guarantee or criterion for the group mean.
- Panel (b): paired route-weighted STaR minus each benchmark reliability in percentage points, horizontal dot-and-whisker forest plot with a zero reference and pointwise 95% family-stratified parent-cluster intervals. Display CON, MWR, QBR only. All three exploratory; use a single axis and preserve actual scale. Do not add a second axis/inset to magnify MWR/QBR. Put precise estimate/interval in a readable aligned annotation or caption, not text over markers.
- Source `results/phase5/data/paired_effects.csv`, filter `cohort=holdout`, `profile=c64`, `metric=reliability`, `comparison` in CON/MWR/QBR. Convert fractions to percentage points exactly once. Expected checks (round only at presentation): CON +16.35 pp [14.57, 18.12]; MWR +2.02 [1.60, 2.43]; QBR +2.10 [1.36, 2.91]. Verify from unrounded data. Panel (a) expected mean reliability 80.97, 95.29, 95.21, 97.31%. Same 2,321 matched routes. No FSPC/SLS/AS1/FT-SAA series, names or panels.
- This figure is an exploratory comparison of the three selected benchmarks, not a new primary confirmatory result. Registered contrast remains in writer disclosure.

### Fig03_charging_complexity — exactly two aligned panels

- Group by number of **original CON charging visits**: 1, 2, 3+. Expected n=1,587, 159, 575. Same original-route bins in both panels. Use original not repaired visit counts.
- Panel (a): STaR minus CON mean route reliability gain (pp), with archived exploratory parent-cluster intervals for each bin. Read `results/phase6/data/mechanism_strata.csv` (`cohort=holdout`, `comparison=CON`, `dimension=source_visit_bin`) and cross-check with original route feature and paired success counts. The old FSPC-based +0.18/+0.18/+4.46 pp and 89% contribution DO NOT apply to this contrast; remove them, do not relabel them. If new contribution is not necessary, omit it. Use honest exploratory language. Do not make causal claims.
- Panel (b): remaining STaR Wilson nonattainment rate (0.25%, 2.52%, 17.74%) with counts 4/1,587, 4/159, 102/575. Label denominators once, preserve visible near-zero bars, use a zero baseline and a straightforward axis. No meaningless endpoint squares on bars, no arbitrary error bars. These are observed descriptive counts. Parent groups may span bins.
- Use common ordering and aligned category labels, enough room for interval marks and denominators. Caption notes 102/110 remaining nonattainments are in 3+ bin; no claim that changing topology caused the subgroup pattern.

### Fig04_progressive_evaluation — ONE simple plot

- Full STaR versus the component variant without progressive prefix evaluation (STaR-NPP), only these two rows, same 2,321 holdout routes. Prefer two horizontal zero-based bars, labeled with mean incremental Monte Carlo search draws: approx. 13,024 and 18,927, respectively. Use full precision for arithmetic and annotate approx. 5,903 draws saved / 31.2% reduction relative to NPP (verify exact percentage from underlying records; do not use a rounded denominator if exact available). Label units explicitly. Do not compare to SLS or use the 118-route timing panel here.
- Check exact per-route successes, Wilson attainment and unconditional mean return against archived matched records; document identical recorded outcomes for this contrast. Add concise caption (not another panel) that this result establishes observed simulation-work savings, not elapsed speedup or equivalence under arbitrary binding budgets. The proof concerns the same incumbent and fixed tape, not future search path under changed budgets. Do not claim that analytical screening is lossless for finite Monte Carlo scores.
- Do not add redundant plots, a second quality panel, performance cards, multiple guards or a Pareto curve. This is a clean component-level illustration, not a new algorithm comparison.

## 5. Exactly three tables

Use compact readable booktabs LaTeX, matching CSV and Markdown exports, with all numeric cells generated from exact source data. Use canonical method acronyms CON, MWR, QBR, STaR consistently (expand once in glossary/caption). No other comparator names in figure/table content. Do not alter registered outcomes or round values before computing differences.

### Tab01_experimental_configuration

Concise setup: benchmark, 1,000 customers/instance, 120 instances and 60 parents, development 24/12 parents, holdout 96/48, total and holdout route/exposure counts, fixed route model, battery and consumption, waits/charging, reliability target, max plan trials, full/prefix sample size, validation size, bootstrap protocol. Include station hours disabled and native units; include budget detail in note if needed. Avoid giant paragraphs, needless parameters and duplicated text.

### Tab02_method_comparison

Exactly four rows, ordered CON, MWR, QBR, STaR. Suggested columns: Method, Mean R (%), Attained (n or %), Full return (native), Search draws, Wall (ms). If table width permits include actual trials; otherwise report trials in accompanying notes. Prefer count and percentage in a single compact cell if legible. The original route has no repair; 0 search draws, wall 0.22 ms is observed setup/evaluator time, not an optimization runtime. MWR/QBR have 0 stochastic search draws because they use surrogate scores, not zero computational cost. The 10,000 validation scenarios are separate for all methods. Retain completion and measured wall times as real trade-offs. Do not highlight STaR as best on all metrics. Expected display anchors:

| Method | Mean R (%) | Attained | Full return | Mean trials | Search draws | Wall (ms) |
|---|---:|---:|---:|---:|---:|---:|
| CON | 80.97 | 1686/2321 | 3391.25 | 1.00 | 0 | 0.22 |
| MWR | 95.29 | 2052/2321 | 3133.83 | 62.11 | 0 | 27.39 |
| QBR | 95.21 | 2183/2321 | 3135.71 | 62.12 | 0 | 27.45 |
| STaR | 97.31 | 2211/2321 | 3135.83 | 62.67 | 13024 | 29.69 |

These are checks, not hard-coded plot data. Reconcile exact records against Phase 5 holdout and original c64 archive. The actual trial averages, MWR's shorter completion and STaR wall time must not be obscured. Do not mix new ablation timing cohorts with original c64 timings.

### Tab03_component_ablation

Exactly five rows: full STaR, without partial charging (NPC), without slack prioritization (NSP), without analytical screening (NAS), without progressive prefix (NPP). These are component removals, not additional proposed methods. Use clear row labels. Columns reliability, attained count, search draws, draw difference (ablation minus full), reliability loss (full minus ablation in pp). Drop redundant difference columns if necessary to fit, but preserve them in the exact data and note. Expected holdout anchors:

| Removal | R (%) | Attained | Draws | Loss (pp) |
|---|---:|---:|---:|---:|
| None | 97.31 | 2211 | 13024 | — |
| Partial charging | 94.19 | 2096 | 8400 | 3.120 |
| Slack prioritization | 97.01 | 2197 | 13080 | 0.308 |
| Analytical screening | 97.31 | 2207 | 13569 | 0.007 |
| Progressive prefix | 97.31 | 2211 | 18927 | 0.000 |

Compute differences from exact unrounded route data. NPC bundles quantity moves and allocation of new topologies; NSP order only; NAS removes rejection, preserves priority and prefix; NPP fully scores admitted plans. Effects exploratory/nonadditive. Note slack prioritization reverses sign on development. Do not include cross-cohort runtime comparisons. The small NAS difference must remain visible at sufficient precision.

## 6. Visual style: restraint over complexity

- Use a common white background, conventional scientific axes, modest panel letters and restrained titles, typography such as DejaVu Sans or a venue-compatible standard font. Avoid infographic cards, massive headings, colored backgrounds, thick borders, long on-plot narratives, excessive annotations, decorative icons, redundant legends, giant empty margins and excessive gridlines. Let captions carry explanatory text.
- Semantic method colors: CON slate gray, MWR muted blue, QBR muted purple or distinct neutral, STaR teal. Station amber; use line/marker differences in addition to colors. Same colors wherever methods appear. Ensure grayscale legibility and sufficient contrast, no misleading color semantics. Use amber sparingly for adverse events. No rainbow palette.
- Target 178 mm full-width and ~65–85 mm height for two-panel figures when feasible; choose natural compact proportions. Single-panel plot may be shorter or a single column if still readable. Check actual font sizes at intended physical width (aim labels 8–10 pt, modest panel headings, no labels below 7 pt unless justified). Maintain exact spatial aspect in Fig01. No forced shrink to fit. Final template not available.
- Export every figure to 400-DPI PNG, vector PDF with embedded fonts, editable SVG with live text and paths. Keep consistent sizes across formats. No AI-generated imagery or invented route data. Do not distribute standalone font files; preserve appropriate license and legally permitted embedded/subsetted fonts if needed for rendering.
- Count actual plot axes/panels, including nested and inset plots. Fig01=2, Fig02=2, Fig03=2, Fig04=1. A legend is not a panel. Reject any artifact that violates this cap. No methodology visual anywhere in the new canonical package.
- Render every actual PNG, PDF and SVG at native and reduced publication size, in color and grayscale; visually inspect the images, not merely metadata. Correct collisions, cropping, awkward alignment, excess whitespace, inconsistent ticks, legends and text. Retain concise proof record with hashes. Compile tables at 178 mm, inspect PDF proofs and resolve overfull/missing glyphs. Do not leave temporary proof images or renderer installs in the active repository.

## 7. Consolidate the active repository (not just another scratch cleanup)

The previous phases accumulated many duplicate and historical outputs. They are useful scientific history but do not all need to remain checked out in the current branch. The desired final organization is approximately:

```text
README.md
.gitattributes / .gitignore
pyproject.toml / requirements.txt
dataset/                 # original benchmark and metadata, unchanged
src/star_evrp/           # frozen core and genuinely required support + publication builder
configs/                 # necessary frozen/configuration inputs
scripts/                 # supported reproduction/build/check entry points
tests/                   # applicable tests for retained workflows
 docs/                   # concise model/method, reproducibility, archive and final release notes
results/
  conference/
    figures/             # exactly 4 stems, 3 formats + source sidecars
    tables/              # exactly 3 stems, 3 formats
    data/                # compact exact publication inputs and source traceability
    audit/               # minimal current release audit, no accumulated phase subfolders
    FIGURE_CAPTIONS.md
    TABLE_NOTES.md
    METHOD_GLOSSARY.md
    CLAIMS_AND_LIMITATIONS.md
    ARCHIVAL_EVIDENCE.md  # text-only mandatory disclosures with pinned references
    EXHIBIT_INDEX.csv
    SOURCE_TRACEABILITY.md
    MANIFEST.json
    README_RESULTS_PACKAGE.md
    STaR_EVRP_CONFERENCE_EXHIBITS.zip
```

The layout is a target, not permission to break imports or discard scientific evidence. Preserve necessary root metadata and the original dataset. Retain the frozen optimizer and required support code; do not edit or remove frozen core to make the tree look smaller. Keep minimal required configs, tests, entry points and scientific documentation. Use a clear `docs/ARCHIVE_AND_REPRODUCTION.md` with exact immutable links, tag/commit and commands to recover the full Phase 1–8 tree in a separate worktree, e.g. `git fetch --tags` and `git worktree add --detach ../STaR-EVRP-research-archive <verified-commit-or-tag>`. Reference original Phase 3 freeze for exact reruns. Include exact Phase 5/6 package locations at pinned archive revision and archived report/manifests. Do not copy multiple full ZIPs into the active tree merely to replace the same bulky folders.

### 7.1 Make a self-contained active exhibit build

The existing generator reads the large Phase 3/5/6 trees. Before removing them, extract a compact immutable **publication input snapshot** into `results/conference/data/inputs/` or a similarly clear location (not multiple duplicates). Include actual coordinates and saved ordered route plans for Fig01; full-precision matched holdout route keys and outcomes needed to derive Fig02–04 and Table 2–3; population/setup fields; original-visit grouping; archive interval records; full-120 descriptive coverage and metrics for writer context; relevant source hashes and exact archive paths. Preserve original seeds, cohort keys, method labels, sample counts, provenance and parent IDs. Do not include the extra methods in the active publication-facing inputs unless indispensable for a separately documented integrity check. Their full records remain in the archive. No synthetic replacement or manually typed result constants.

Build snapshot from original immutable source records while available. Independently reconcile row counts, route joins, plan identity, exact values and intervals against the full archive. Record snapshot manifest, extraction code or documented command, source file/member SHA-256 and archival commit. Update active generator to consume these retained inputs directly, not rely on deleted paths or internet downloads for routine build. If full historical reanalysis is needed, provide a separate archive-worktree workflow rather than bundling multiple phases in the active tree. If a dependency cannot be extracted/reconciled safely, retain the minimal original file or folder and explain why. Do not reduce provenance to rounded tables alone. No new stochastic runs.

### 7.2 What may be deleted from the active checkout after verification

- Historical `results/phase2`, `phase25`, `phase3`, `phase4`, `phase5`, `phase6` and older `results/baselines`, `raw`, `processed`, `reports`, `figures`, `tables`, `manifests` folders **only** after (a) immutable remote archive verified, (b) dependencies migrated or retained, (c) reproduction from clean active snapshot succeeds, and (d) full historical rerun instructions and evidence remain accessible. Delete obsolete tracked paths using normal Git commits; never delete their history. No need to keep all historical phase folders in current main just because they were previously generated.
- Historical phase reports, development prompts, obsolete proof/release docs, obsolete scripts/configs and phase-specific analysis modules/tests that solely target archived workflows may be moved out of active checkout if archived and demonstrably no longer required. Keep a compact final research summary, rigorous math/model documentation, original baseline/benchmark provenance, preregistration pointer, source-traceability and limitations. Retain or extract genuinely applicable tests; do not hide failures by dropping tests for functionality still present. Record every intentionally archived test and reason, and verify that the historical suite can still be recovered from the archival commit. Preserve frozen source files and dependencies needed for the supported method. If old implementation files are part of the frozen core or used by tests, keep them.
- Remove previous canonical methodology diagram, operator art, SLS/FSPC main plots/tables, AS1/FT-SAA visuals, old supplementary images, stale conference ZIP/sidecars/indices (replace with new canonical exports), redundant old conference proofs/audit working copies, temporary compilation products, build directories, caches, `.pyc`, empty obsolete directories and exact duplicates after checking. All old scientific variants remain accessible in archive.
- Keep original dataset and license/citation metadata; do not deduplicate different station tables or variant files based merely on names. Do not delete unique untracked checkpoints without verified backup and justification. Never remove user-owned files unrelated to this task. Retain ambiguous paths and disclose.

### 7.3 Measure the real cleanup

Report before/after active tracked file count and payload size, deleted tracked file count/bytes, retained necessary paths and reasons, ignored/untracked cleanup separately, temporary scratch created during this task separately, and historical Git object storage separately. Do not present removal of self-generated scratch as persistent repository savings. Do not promise remote storage reduction from a normal deletion commit: historical objects remain recoverable. Avoid a new permanent `phase9/` output tree. Keep one current final report and compact audit; no pile of redundant proof images, giant duplicate raw data, or redundant manifests. The new prompt may remain as the one active publication instruction if useful; archive old prompts with historical workflow.

## 8. Rebuild, tests and packaging

1. From an isolated clean checkout/worktree of the candidate final active tree, build the exhibits from the retained inputs only. Ensure no missing old-phase path, no dependence on old local folders, no network requirement for ordinary reproduction. Independently check exact numerical results, four-method allowlist, five ablation rows, four figure stems, 2/2/2/1 panels, no methodology figure, no extra method series, correct source hashes and all captions/notes/indexes. Search active export contents, legends, source-sidecar metadata and tables for unintended obsolete labels; extra method names are allowed in text-only archival disclosures and scientific history, not the new figure/table contents.
2. Run applicable frozen core and publication tests in the retained tree. Add focused tests for archive snapshot reconciliation, panel count, method whitelist, preserved outcomes, missing-input failure, generated file counts and clean rebuild. Run original full historical test suite in a separate archival worktree if feasible (report any blocker, do not claim success without logs); no new optimization campaign. A lower active test count due to properly archived workflows is not a quality improvement by itself. Never suppress failures or remove relevant tests to get green. Record actual counts and exit codes.
3. Build twice in fresh directories, compare deterministic exact data and exports/hashes; document unavoidable metadata differences. Verify archive references can be resolved, historical manifests still match in the archival tree, and original frozen code/dataset files retained on main are byte-identical. Check no broken active imports, script entry points, markdown links, manifests or package dependencies. Validate retained input snapshot hashes. Remove scratch only after audit.
4. Update README so a new researcher understands immediately: one method, three displayed benchmarks, how to build/use current exhibits, how to recover full research evidence. Explain 96 holdout versus 120 overall. Keep docs and results easy to navigate. Write concise final report and cleanup ledger, not paper sections. Keep explicit text-only `ARCHIVAL_EVIDENCE.md` with registered FSPC result, SLS cost/quality and timing findings, AS1/FT-SAA restricted/uncertain comparisons, adverse example and links to exact archived sources; do not accidentally transform this document into an extra comparative figure/table. The writer must not present the four displayed methods as the only methods ever tested.
5. Update captions, table notes, glossary, traceability, exhibit index and manifest to match the **new** four figures and three tables. Include actual file formats, dimensions, cohort, methods and hash. Remove stale links to deleted active phase paths; replace with immutable archive links. Include exact data needed to regenerate exhibits (within reasonable size) and a minimal README, current audit and mandatory disclosures. Keep all package contents synchronized with active canonical files. Create one final `results/conference/STaR_EVRP_CONFERENCE_EXHIBITS.zip` containing no obsolete methodology image, no historical comparative figures/tables and no duplicate old release ZIP. Verify safe extraction, member list, CRC and hashes; prevent self-inclusion and unsafe paths. Do not bundle caches, private paths or standalone fonts.
6. Before release, verify `git diff` against pre-cleanup commit, check deletion ledger, and ensure no optimizer or original dataset change. If authorized, commit and push without force, with a clear message (separate archival tag/checkpoint, consolidation and final build commits if useful). Verify remote HEAD and archive recovery. If a push is blocked, report exact local commit and blocker; do not claim published. Do not overwrite unrelated changes.

## 9. Acceptance gates — all must pass or be explicitly blocked

| Gate | Required evidence |
|---|---|
| G0 — Baseline and archive | Exact starting revision, immutable verified archive/recovery, preflight inventory |
| G1 — Scientific preservation | Frozen code and dataset hashes, complete original evidence recoverable, snapshot reconciled, disclosures retained |
| G2 — Scope | Four method rows in Table 2, four ablations plus full STaR in Table 3, exactly four figures, no methodology artwork or extra comparator figures/tables |
| G3 — Accuracy | All exact archived numbers, populations, estimates, intervals, source route maps and per-route NPP equality verified |
| G4 — Design | 2/2/2/1 panels, all actual PNG/PDF/SVG inspected at physical and reduced size, consistent style, no collisions, table proofs compile |
| G5 — Real consolidation | Safe tracked historical-folder removal or explicit reasons retained; meaningful before/after payload metrics, no broken dependencies/links, no unique evidence destroyed |
| G6 — Reproducibility | Clean standalone active builds match, missing input rejected, applicable tests pass, archival recovery verified |
| G7 — Release | Current manifest/ZIP/index/captions/notes, safe extraction verified, archive references accessible, remote commit confirmed if authorized |

## 10. Final response to the project owner

Give the actual starting/final revisions and archival reference; state exactly what was deleted, what was preserved and why; report before/after active checkout size and counts, separate scratch cleanup, all four figure and three table paths, actual tests/rebuild/compilation/visual audit, final ZIP link and any limitations. Explicitly confirm there is NO generated methodology figure, NO FSPC/SLS/AS1/FT-SAA series or rows in publication exhibits, NO new optimization or changed scientific results. List any blocked removal or unverified requirement honestly. Stop once the new package and safe repository consolidation are complete. No manuscript, no more phases or experiments.
