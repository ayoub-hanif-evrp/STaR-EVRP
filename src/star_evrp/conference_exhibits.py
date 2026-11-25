"""Three publication tables and Prompt-09 package documents."""

from __future__ import annotations

from star_evrp.conference_data import ARCHIVE_COMMIT, ARCHIVE_TAG, DISPLAY, FROZEN, METHODS, gather
from star_evrp.conference_figures import STEMS, draw
from star_evrp.phase4_release import LATEX, markdown
from star_evrp.phase4_results import require
from star_evrp.phase6_archive import write_bytes, write_csv, write_json

TABLE_STEMS = (
    "Tab01_experimental_configuration",
    "Tab02_method_comparison",
    "Tab03_component_ablation",
)


def text(path, content):
    write_bytes(path, (content.rstrip() + "\n").encode("utf-8"))


def captions(data):
    example = data["example"]
    loc = example["selection"]["chosen"]
    con, star = example["metrics"]
    stations = [r["node"] for r in example["stops"] if r["type"] == "station"]
    paired = {r["comparison"]: r for r in data["paired"]}
    bins = data["complexity"]
    npp = data["npp"]
    fmt = lambda r: f'{r["mean_pp"]:+.2f} [{r["lo95_pp"]:+.2f}, {r["hi95_pp"]:+.2f}]'
    return {
        STEMS[0]: (
            f'Outcome-selected holdout illustration {loc["parent"]}/{loc["variant"]}, route {loc["route"]} '
            f'(customers {example["selection"]["customer_order"][0]} then {example["selection"]["customer_order"][1]}). '
            f'Panel (a) CON visits station {stations[0]} after the last customer; panel (b) STaR inserts station '
            f'{stations[1]} before the first customer. Observed reliability {100*con["reliability"]:.2f}% '
            f'({con["successes"]:,}/{con["scenarios"]:,}) versus {100*star["reliability"]:.2f}% '
            f'({star["successes"]:,}/{star["scenarios"]:,}) on the same archived validation tape. '
            f'Mean full return {con["completion"]:,.2f} versus {star["completion"]:,.2f} (native units; caption only). '
            "Maps share equal aspect and identical limits. The observed 100% is an empirical estimate, not certainty. "
            "This is an illustration, not representative evidence."
        ),
        STEMS[1]: (
            "Exploratory comparison on 2,321 exposed holdout routes from 48 parents. Panel (a) shows mean route "
            "reliability for CON, MWR, QBR and STaR with a 95% individual Wilson-attainment reference line "
            "(not a group-mean guarantee). Panel (b) shows paired route-weighted STaR minus each benchmark in "
            f'percentage points with pointwise 95% family-stratified parent-cluster intervals: CON {fmt(paired["CON"])}; '
            f'MWR {fmt(paired["MWR"])}; QBR {fmt(paired["QBR"])}. All three contrasts are exploratory. '
            "The registered confirmatory contrast is disclosed only in ARCHIVAL_EVIDENCE.md."
        ),
        STEMS[2]: (
            "Holdout routes grouped by original CON charging visits (1, 2, 3+; n="
            f'{bins[0]["n"]:,}, {bins[1]["n"]:,}, {bins[2]["n"]:,}). Panel (a) shows exploratory STaR−CON mean '
            "reliability gains (pp) with parent-cluster intervals. Panel (b) shows remaining STaR Wilson "
            f'nonattainment rates {bins[0]["nonattainment_pct"]:.2f}%, {bins[1]["nonattainment_pct"]:.2f}%, '
            f'{bins[2]["nonattainment_pct"]:.2f}% with denominators '
            f'{bins[0]["nonattained"]}/{bins[0]["n"]:,}, {bins[1]["nonattained"]}/{bins[1]["n"]:,}, '
            f'{bins[2]["nonattained"]}/{bins[2]["n"]:,}. Routes with 3+ visits account for '
            f'{bins[2]["nonattained"]} of 110 remaining nonattainments. Associations are descriptive; '
            "no causal claim about topology."
        ),
        STEMS[3]: (
            "Component illustration on the same 2,321 holdout routes. Horizontal bars compare mean incremental "
            f'Monte Carlo search draws for full STaR ({npp["full_draws"]:,.0f}) and STaR without progressive '
            f'prefix evaluation ({npp["npp_draws"]:,.0f}). Progressive evaluation saved approximately '
            f'{npp["saved_draws"]:,.0f} draws ({npp["reduction_pct"]:.1f}% relative to NPP). Per-route reliability, '
            "attainment and completion are identical for STaR and STaR−NPP in the archived records. "
            "This establishes observed simulation-work savings, not elapsed wall-time speedup or equivalence "
            "under arbitrary binding budgets."
        ),
    }


def table_specs(data):
    cfg = data["config"]
    partitions = cfg["partitions"]
    hold = next(r for r in partitions if r["partition"] == "holdout")
    dev = next(r for r in partitions if r["partition"] == "development")
    caps = cfg["work_limits"]
    overview = [
        ["Benchmark",
         f'Extended Homberger, {cfg["customers_per_instance"]:,} customers/instance; '
         f'{cfg["instances"]} instances from {cfg["parents"]} A/B parents.'],
        ["Split and coverage",
         f'{dev["instances"]} development / {hold["instances"]} holdout instances '
         f'({dev["parents"]} / {hold["parents"]} parents). '
         f'{cfg["all_routes"]:,} routes / {cfg["exposed"]:,} exposed overall; '
         f'holdout {hold["all_routes"]:,} / {hold["exposed"]:,} '
         f'({hold["zero_charge"]:,} unchanged no-charge).'],
        ["Route and energy",
         f'Fixed customers/order; Q = {cfg["battery_capacity"]}; h = {cfg["energy_consumption"]:g}; '
         "Euclidean travel; linear heterogeneous charging; native units."],
        ["Waits and stations",
         f'Independent synthetic lognormal visit waits; {cfg["distinct_station_tables"]} reused station tables; '
         "station hours disabled."],
        ["Search and target",
         f'{100 * cfg["target"]:g}% individual reliability target; max {caps["max_candidate_evals"]} distinct trials '
         f'(including start); {caps["max_scenario_evals"]:,} search-draw ceiling; '
         f'{caps["wall_seconds"]} s cooperative guard.'],
        ["Evaluation",
         f'{cfg["search_draws"]} full stochastic draws; {cfg["prefix_draws"]}-draw STaR prefix; '
         f'up to {cfg["nearby_count"]} nearby stations; {cfg["validation_draws"]:,} independent validation draws.'],
        ["Inference",
         f'One-sided 95% Wilson attainment; {cfg["bootstrap_replicates"]:,} family-stratified parent bootstrap '
         f'resamples (seed {cfg["bootstrap_seed"]}).'],
    ]
    h2 = ["Method", "Mean R (%)", "Attained", "Full return", "Trials", "Search draws", "Wall (ms)"]
    h3 = ["Component removed", "Mean R (%)", "Attained", "Search draws", "Draw difference", "Reliability loss (pp)"]
    comparison = [
        [r["label"] if r["method"] != "STaR" else "STaR",
         r["reliability_pct"], r["attained"], r["completion"], r["trials"], r["draws"], r["wall_ms"]]
        for r in data["comparison"]
    ]
    # Display method acronyms in Tab02
    comparison = [
        [r["method"], r["reliability_pct"], r["attained"], r["completion"], r["trials"], r["draws"], r["wall_ms"]]
        for r in data["comparison"]
    ]
    ablation = [
        [r["component"], r["reliability_pct"], r["attained"], r["draws"], r["draw_delta"], r["loss_pp"]]
        for r in data["ablation"]
    ]
    show2 = [
        [m, f"{R:.2f}", f"{n}/{2321}", f"{c:,.2f}", f"{trials:.2f}", f"{draws:,.0f}", f"{wall:.2f}"]
        for m, R, n, c, trials, draws, wall in comparison
    ]
    show3 = [
        [
            label,
            f"{R:.2f}",
            f"{n}/{2321}",
            f"{draws:,.0f}",
            "—" if change is None else f"{change:+,.0f}",
            "—" if loss is None else f"{loss:.3f}",
        ]
        for label, R, n, draws, change, loss in ablation
    ]
    return tuple(zip(
        TABLE_STEMS,
        (
            (["Parameter", "Configuration"], overview, overview),
            (h2, comparison, show2),
            (h3, ablation, show3),
        ),
        strict=True,
    ))


def table_latex(stem, headers, rows):
    configuration = stem == TABLE_STEMS[0]
    layout = r"@{}p{34mm}p{138mm}@{}" if configuration else "@{}l" + "r" * (len(headers) - 1) + "@{}"
    bold = {"STaR", "None (full STaR)"}
    lines = [
        r"\begingroup", r"\small", r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{1.12}", r"\noindent",
        rf"\begin{{tabular}}{{{layout}}}", r"\toprule",
        " & ".join(r"\textbf{" + h.translate(LATEX) + "}" for h in headers) + r" \\",
        r"\midrule",
    ]
    for index, row in enumerate(rows):
        terms = [v.translate(LATEX).replace("—", r"\textemdash{}") for v in row]
        if row[0] in bold:
            terms[0] = r"\textbf{" + terms[0] + "}"
        if stem == TABLE_STEMS[1] and index == 3:
            lines.append(r"\addlinespace[2pt]")
        if stem == TABLE_STEMS[1] and index == 0:
            terms[-1] += r"\textsuperscript{a}"
        if configuration:
            terms = [r"{\raggedright " + term + r"\par}" for term in terms]
        lines.append(" & ".join(terms) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\endgroup"]
    return "\n".join(lines) + "\n"


def tables(out, data):
    for stem, (headers, exact, rounded) in table_specs(data):
        path = out / "tables" / stem
        write_csv(path.with_suffix(".csv"), [dict(zip(headers, r, strict=True)) for r in exact], headers)
        text(path.with_suffix(".tex"), table_latex(stem, headers, rounded))
        text(path.with_suffix(".md"), markdown(headers, rounded))
        write_json(
            out / "data" / f"{stem}_display.json",
            dict(headers=headers, exact=exact, rendered=rounded, source_sha256=data["sources"]),
        )


def archival_evidence(out, data):
    d = data["disclosure"]
    reg = d["registered_primary"]
    sls = d["sls_exploratory"]
    as1 = d["phase6_as1"]
    ft = d["phase6_ft_saa"]
    trials = d["trial_workload"]
    text(out / "ARCHIVAL_EVIDENCE.md", f"""# Archival evidence (text-only disclosures)

These comparisons are **not** plotted or tabulated in the active four-method publication package.
They remain part of the scientific record and must be cited in prose with links to the archive.

Archive tag `{ARCHIVE_TAG}` · commit `{ARCHIVE_COMMIT}` · freeze `{FROZEN}` (`star-phase3-freeze-v1`).

## Registered confirmatory contrast (STaR − FSPC)

- Holdout, profile c64, reliability: **{reg["display"]}** on {reg["n"]:,} exposed routes / {reg["parents"]} parents.
- Exact: {reg["mean_pp"]:+.6f} pp [{reg["lo95_pp"]:+.6f}, {reg["hi95_pp"]:+.6f}].
- Status: {reg["status"]}.
- Actual mean trials: {trials["display"]} (common maximum 64).
- Source: `{reg["source"]}` · `{reg["archive_tag_ref"]}`.

## Exploratory scenario search (STaR − SLS)

- Holdout reliability contrast: **{sls["display"]}** (exact {sls["mean_pp"]:+.6f} pp [{sls["lo95_pp"]:+.6f}, {sls["hi95_pp"]:+.6f}]).
- Search draws: STaR {sls["search_draws"]["star"]:,.0f} vs SLS {sls["search_draws"]["sls"]:,.0f}
  ({sls["search_draws"]["relative_reduction_pct"]:.2f}% fewer for STaR).
- Wall time: {sls["wall_display"]} ms (STaR vs SLS).
- Source: `{sls["source"]}` · `{sls["archive_tag_ref"]}`.

## Phase 6 restricted / uncertain comparisons

### AS1 (113-route one-visit panel)

- Contrast: {as1["contrast"]}.
- Reliability: {as1["mean_pp"]:+.4f} pp [{as1["lo95_pp"]:+.4f}, {as1["hi95_pp"]:+.4f}] (crosses zero).
- Completion difference: {as1["completion_mean"]:+.4f} native units.
- Note: {as1["note"]}.
- Source: `{as1["source"]}` · `{as1["archive_tag_ref"]}`.

### FT-SAA (118-route fixed-topology panel)

- Contrast: {ft["contrast"]}.
- Reliability: {ft["mean_pp"]:+.4f} pp [{ft["lo95_pp"]:+.4f}, {ft["hi95_pp"]:+.4f}].
- Completion difference: {ft["completion_mean"]:+.4f} native units.
- Note: {ft["note"]}.
- Source: `{ft["source"]}` · `{ft["archive_tag_ref"]}`.

## Scope reminders

Do not assert superiority over optimal fixed topology, a general runtime advantage, noninferiority, or causal
subgroup mechanisms. Do not present CON/MWR/QBR/STaR as the only methods ever tested. Recover full Phase 1–8
trees via `docs/ARCHIVE_AND_REPRODUCTION.md`.
""")


def handoff(root, out, data, figure_caps):
    cfg = data["config"]
    cmp = {r["method"]: r for r in data["comparison"]}
    ab = {r["method"]: r for r in data["ablation"]}
    npp = data["npp"]
    paired = {r["comparison"]: r for r in data["paired"]}
    fmt = lambda r: f'{r["mean_pp"]:+.2f} [{r["lo95_pp"]:+.2f}, {r["hi95_pp"]:+.2f}]'
    notes = [
        "Frozen benchmark and registered holdout settings. No-charge holdout routes are excluded from exposed "
        "metrics. Attainment means the one-sided 95% Wilson lower bound reaches 0.95. Station hours disabled; "
        "native units. The sole confirmatory endpoint remains STaR−FSPC (see ARCHIVAL_EVIDENCE.md).",
        f'Four methods on 2,321 exposed holdout routes. R is mean reliability (%). Attained is count/2,321. '
        f'Full return uses native time units including late trajectories. Search draws exclude validation. '
        f'ᵃ CON wall {cmp["CON"]["wall_ms"]:.2f} ms is observed setup/evaluator time, not optimization. '
        f'MWR/QBR report 0 stochastic search draws because they use surrogate scores. '
        f'STaR trials {cmp["STaR"]["trials"]:.2f}; MWR completion is shorter than STaR by '
        f'{cmp["STaR"]["completion"] - cmp["MWR"]["completion"]:.2f} native units. CSV retains full precision.',
        f'Five component rows (full STaR plus four removals). Loss is full minus ablation (pp). Draw difference '
        f'is ablation minus full. Progressive prefix saved ≈{npp["saved_draws"]:,.0f} draws '
        f'({npp["reduction_pct"]:.1f}%) with identical per-route outcomes. Effects are exploratory and nonadditive; '
        f'slack prioritization reverses sign on development. NPC bundles quantity moves and new-topology allocation.',
    ]
    text(out / "FIGURE_CAPTIONS.md", "# Figure captions\n\n" + "\n\n".join(
        f"## {k}\n\n{v}" for k, v in figure_caps.items()
    ))
    text(out / "TABLE_NOTES.md", "# Table notes\n\n" + "\n\n".join(
        f"## {k}\n\n{v}" for k, v in zip(TABLE_STEMS, notes, strict=True)
    ))
    entries = []
    cohorts = (
        "Selected holdout route C1_10_3/A/106",
        "2,321 holdout routes / 48 parents",
        "2,321 holdout routes by original CON visits",
        "2,321 holdout routes (STaR vs STaR−NPP)",
    )
    for i, stem in enumerate(STEMS):
        entries.append(dict(
            id=stem, kind="figure", path=f"figures/{stem}.pdf",
            formats="PDF, SVG, PNG; JSON sidecar", cohort=cohorts[i], notes="FIGURE_CAPTIONS.md",
            panels=str((2, 2, 2, 1)[i]),
        ))
    for i, stem in enumerate(TABLE_STEMS):
        entries.append(dict(
            id=stem, kind="table", path=f"tables/{stem}.tex",
            formats="TeX, CSV, Markdown",
            cohort="Full benchmark design" if i == 0 else "2,321 holdout routes",
            notes="TABLE_NOTES.md", panels="NA",
        ))
    write_csv(out / "EXHIBIT_INDEX.csv", entries)

    text(out / "METHOD_GLOSSARY.md", """# Method glossary

| Acronym | Label | Role |
| --- | --- | --- |
| CON | Original route | Principal baseline (unchanged constructive plan) |
| MWR | Mean-wait repair | Principal baseline (mean-wait surrogate) |
| QBR | Quantile repair | Principal baseline (per-visit quantile surrogate) |
| STaR | Slack-Targeted Stochastic Charging Repair | Sole proposed method |

Component removals (Table 3 only; not marketed as independent methods):

| Code | Removal |
| --- | --- |
| NPC | Partial charging (quantity moves and partial allocation on new topologies) |
| NSP | Slack prioritization (order only) |
| NAS | Analytical screening (rejection removed; ranking and prefix retained) |
| NPP | Progressive prefix evaluation (full scoring of admitted plans) |

Archived methods disclosed only in `ARCHIVAL_EVIDENCE.md`: FSPC, SLS, AS1, FT-SAA. Archive key `c64` is the 64-plan budget.
""")

    text(out / "CLAIMS_AND_LIMITATIONS.md", f"""# Claims and limitations for the writer

## Active publication exhibits (four methods)

- **Tab02 / Fig02.** Holdout means: CON {cmp['CON']['reliability_pct']:.2f}%, MWR {cmp['MWR']['reliability_pct']:.2f}%,
  QBR {cmp['QBR']['reliability_pct']:.2f}%, STaR {cmp['STaR']['reliability_pct']:.2f}%.
  Paired exploratory contrasts: CON {fmt(paired['CON'])}; MWR {fmt(paired['MWR'])}; QBR {fmt(paired['QBR'])}.
- **Fig03.** Visit-bin associations for STaR−CON; remaining nonattainment concentrated in 3+ visits ({data['complexity'][-1]['nonattained']}/110).
- **Tab03 / Fig04.** Component study. Progressive evaluation saves ≈{npp['saved_draws']:,.0f} draws ({npp['reduction_pct']:.1f}%)
  with identical archived route outcomes. Partial charging loss {ab['STaR-NPC']['loss_pp']:.3f} pp.

## Mandatory archival disclosures (text only)

See `ARCHIVAL_EVIDENCE.md` for the registered STaR−FSPC result, SLS trade-off, and Phase 6 AS1/FT-SAA limitations.
Do not place FSPC/SLS/AS1/FT-SAA in new figure legends, plotted series, or table rows.

## Scope

Synthetic station laws; four reused station tables; fixed customer order; linear charging; station hours disabled;
no endogenous congestion, fleet-wide guarantee, or dynamic recourse. Intervals are pointwise and unadjusted.
Except for the registered FSPC contrast, comparisons are exploratory. No claim of global optimality, universal
superiority, general wall-time speedup, or literature priority.
""")

    text(out / "README_RESULTS_PACKAGE.md", f"""# STaR-EVRP conference exhibits (Prompt 09)

Exactly **four** main figures (panels 2/2/2/1) and **three** main tables. No methodology artwork.
Active comparison methods: CON, MWR, QBR, STaR only.

| Stem | Panels |
| --- | ---: |
| Fig01_spatial_charging_repair | 2 |
| Fig02_comparative_reliability | 2 |
| Fig03_charging_complexity | 2 |
| Fig04_progressive_evaluation | 1 |

Build from the immutable snapshot in `data/inputs/` (no Phase 3/5/6 tree required for ordinary rebuild):

```text
python -B scripts/build_conference_exhibits.py build --output results/conference
```

Start with `EXHIBIT_INDEX.csv`, `FIGURE_CAPTIONS.md`, `TABLE_NOTES.md`, `CLAIMS_AND_LIMITATIONS.md`,
and `ARCHIVAL_EVIDENCE.md`. Figures: 400 DPI PNG, vector PDF (embedded fonts), editable SVG (live text).
Width 178 mm. Font: DejaVu Sans (`FONT_LICENSE.txt`).

Holdout primary population: 96 instances / 48 parents / 2,321 exposed routes. The 120-instance descriptive
coverage is retained for writer context only. Archive recovery: `docs/ARCHIVE_AND_REPRODUCTION.md`.
Snapshot archive commit `{ARCHIVE_COMMIT}`; freeze `{FROZEN}`.
""")

    lines = [
        "# Source traceability",
        "",
        f"Publication snapshot under `data/inputs/`. Archive `{ARCHIVE_TAG}` / `{ARCHIVE_COMMIT}`. "
        f"Frozen executable `{FROZEN}`.",
        "",
        "Active exhibits read only the snapshot. Historical Phase 3/5/6 paths are archival references.",
        "",
        "## Snapshot files",
        "",
    ]
    for name, digest in sorted(data["sources"].items()):
        lines.append(f"- `{name}` — `{digest}`")
    lines.extend((
        "",
        "## Companion archive locations (at pinned tag)",
        "",
        f"- `{ARCHIVE_TAG}:results/phase5/data/paired_effects.csv`",
        f"- `{ARCHIVE_TAG}:results/phase6/data/mechanism_strata.csv`",
        f"- `{ARCHIVE_TAG}:results/phase3/`",
        "",
        "See `docs/ARCHIVE_AND_REPRODUCTION.md` for worktree recovery commands.",
    ))
    text(out / "SOURCE_TRACEABILITY.md", "\n".join(lines))
    archival_evidence(out, data)

    write_json(out / "MANIFEST.json", dict(
        schema=3,
        prompt="PROMPT_09",
        archive_tag=ARCHIVE_TAG,
        archive_commit=ARCHIVE_COMMIT,
        frozen=FROZEN,
        figures=list(STEMS),
        tables=list(TABLE_STEMS),
        panel_counts=dict(zip(STEMS, (2, 2, 2, 1), strict=True)),
        methods=list(DISPLAY),
        ablations=list(ab),
        input_sha256=data["sources"],
        figure_sha256={
            stem: __import__("star_evrp.phase4_results", fromlist=["read_json"]).read_json(
                out / "figures" / f"{stem}.json"
            )["formats_sha256"]
            for stem in STEMS
        },
    ))


def build(root, out, width):
    require(width == 178, "The canonical exhibits use a fixed 178 mm double-column layout")
    # Prefer inputs already under the output tree; otherwise read the authoritative snapshot.
    data = gather(root, out)
    # Ensure the build output carries a copy of the immutable inputs for self-contained packaging.
    inputs_src = data["inputs"]
    inputs_dst = out / "data" / "inputs"
    if inputs_src.resolve() != inputs_dst.resolve():
        inputs_dst.mkdir(parents=True, exist_ok=True)
        for path in inputs_src.iterdir():
            if path.is_file():
                write_bytes(inputs_dst / path.name, path.read_bytes())
        data = gather(root, out)
    labels = captions(data)
    draw(root, out, data, width, labels)
    tables(out, data)
    handoff(root, out, data, labels)
    return data
