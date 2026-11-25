"""Three publication tables and their writer handoff."""

from star_evrp.conference_data import BASE, FROZEN, METHODS, gather
from star_evrp.conference_figures import STEMS, draw
from star_evrp.phase4_release import LATEX, markdown
from star_evrp.phase4_results import read_json, require
from star_evrp.phase6_archive import write_bytes, write_csv, write_json

TABLE_STEMS = ("Tab01_experimental_configuration","Tab02_method_comparison","Tab03_component_ablation")


def text(path,content):
    write_bytes(path,(content.rstrip()+"\n").encode("utf-8"))


def captions(data):
    loc=data["map_selection"]["chosen"]
    con,star=data["map_metrics"]
    stations=[r["node"] for r in data["map_stops"] if r["type"]=="station"]
    overshoots=data["timing_notes"]["primary_stops"]
    result=(
        f'Outcome-selected holdout example {loc["parent"]}/{loc["variant"]}, route {loc["route"]}. '
        f'The original and repaired maps share the same ordered customers. STaR removed station {stations[0]} after the '
        f'last customer and inserted a visit to {stations[1]} before the first. Observed reliability is '
        f'{con["successes"]:,} and {star["successes"]:,} successes on the same {con["scenarios"]:,}-scenario archived '
        'validation tape. Mean full return includes late scenarios. Coordinates, charge and time use native benchmark units.',
        'Frozen Slack-Targeted Stochastic Charging Repair (STaR) with a fixed customer sequence. The analytical screen '
        'uses a true-reliability necessary condition when the incumbent attains the empirical target. Prefix pruning '
        'tests the best possible score on the same tape. A strict gain restarts the neighborhood. Independent final validation follows search.',
        'Paired reliability on 2,321 exposed holdout routes from 48 parents under the 64-plan budget. Panel (a) shows '
        'route-weighted STaR-minus-comparator means with pointwise 95% family-stratified parent bootstrap intervals '
        '(9,999 resamples, A/B siblings and routes retained together). Fixed-station repair is confirmatory, scenario '
        'search exploratory. Panel (b) compares STaR with fixed-station repair. Ties have equal success counts out of 10,000.',
        'Holdout routes stratified by original constructive-plan station visits. Panel (a) shows STaR minus fixed-station '
        'repair in percentage points with exploratory pointwise 95% parent-cluster intervals. Panel (b) gives the count '
        'and share whose one-sided 95% Wilson lower bound after STaR is below 0.95. The signed contribution of the 3+ '
        'group is its mean times its route share. Parents may appear in more than one bin.',
        'Separate exploratory timing panel of 118 routes from 60 parents (23 development, 95 holdout). The 20, 50 and '
        '100 ms cooperative guards each used three serial repeats per method and route. Panel (a) shows route-mean '
        'independent validation reliability and incremental search draws, excluding validation. Panel (b) shows paired differences '
        'with pointwise 95% family-by-partition parent intervals after averaging repeats. At 50 ms, STaR exceeded the guard '
        f'on {overshoots["STaR"]["overshoots"]}/{overshoots["STaR"]["repeats"]} runs and scenario search on '
        f'{overshoots["SLS"]["overshoots"]}/{overshoots["SLS"]["repeats"]}. '
        'Reliability and elapsed-time difference intervals include zero at 50 ms.',
    )
    return dict(zip(STEMS,result,strict=True))


def table_specs(data):
    cfg=data["config"]
    dev,hold=cfg["partitions"]
    caps=cfg["work_limits"]
    overview=[
        ["Benchmark",f'Extended Homberger, {cfg["customers_per_instance"]:,} customers per instance. '
         f'{cfg["instances"]} instances from {cfg["parents"]} A/B parents.'],
        ["Split and route coverage",
         f'{dev["instances"]} development and {hold["instances"]} holdout instances ({hold["parents"]} holdout parents). '
         f'{cfg["all_routes"]:,} routes / {cfg["exposed"]:,} exposed overall. Holdout: {hold["all_routes"]:,} / {hold["exposed"]:,}.'],
        ["Route and energy model",
         f'Fixed customers and order, capacity Q = {cfg["battery_capacity"]}, consumption h = {cfg["energy_consumption"]:g}. '
         'Euclidean travel, linear station-specific charging, native units.'],
        ["Station waits",f'Independent synthetic lognormal waits per visit. {cfg["distinct_station_tables"]} reused station attribute tables. '
         'Station hours disabled.'],
        ["Search and target",f'{100*cfg["target"]:g}% route target. Maximum {caps["max_candidate_evals"]} distinct trials, '
         f'{caps["max_scenario_evals"]:,} search draws and {caps["wall_seconds"]} s cooperative guard. '
         'Trials include the original plan.'],
        ["Candidate evaluation",
         f'{cfg["search_draws"]} common draws for full stochastic scores, with a {cfg["prefix_draws"]}-draw STaR prefix. '
         f'Up to {cfg["nearby_count"]} nearby eligible stations per considered gap.'],
        ["Validation and inference",f'{cfg["validation_draws"]:,} independent validation draws per plan, paired across methods. '
         f'One-sided 95% Wilson attainment. {cfg["bootstrap_replicates"]:,} family-stratified parent bootstrap resamples.'],
    ]
    h2=["Method","Mean R (%)","Attained","Full return (native)","Search draws","Wall (ms)"]
    h3=["Component removed","Mean R (%)","Attained","Search draws","Reliability loss (pp)"]
    comparison=[[r["label"],r["reliability_pct"],r["attained"],r["completion"],r["draws"],r["wall_ms"]] for r in data["comparison"]]
    ablation=[[r["component"],r["reliability_pct"],r["attained"],r["draws"],r["loss_pp"]] for r in data["ablation"]]
    show2=[[label,f"{R:.2f}",f"{n:,}",f"{c:,.2f}",f"{draws:,.0f}",f"{wall:.2f}"]
           for label,R,n,c,draws,wall in comparison]
    show3=[[label,f"{R:.2f}",f"{n:,}",f"{draws:,.0f}",f"{loss:.3f}" if loss is not None else "—"]
           for label,R,n,draws,loss in ablation]
    return tuple(zip(TABLE_STEMS,((["Parameter","Configuration"],overview,overview),
                                 (h2,comparison,show2),(h3,ablation,show3)),strict=True))


def table_latex(stem,headers,rows):
    configuration=stem==TABLE_STEMS[0]
    layout=r"@{}p{34mm}p{138mm}@{}" if configuration else "@{}l"+"r"*(len(headers)-1)+"@{}"
    bold={"STaR","None (full STaR)"}
    lines=[r"\begingroup",r"\small",r"\setlength{\tabcolsep}{4pt}",r"\renewcommand{\arraystretch}{1.12}",r"\noindent",
           rf"\begin{{tabular}}{{{layout}}}",r"\toprule",
           " & ".join(r"\textbf{"+h.translate(LATEX)+"}" for h in headers)+r" \\",r"\midrule"]
    for index,row in enumerate(rows):
        terms=[v.translate(LATEX).replace("—","---") for v in row]
        if row[0] in bold:
            terms[0]=r"\textbf{"+terms[0]+"}"
        if stem==TABLE_STEMS[1] and index==3:
            lines.append(r"\addlinespace[2pt]")
        if stem==TABLE_STEMS[1] and index==0:
            terms[-1]+=r"\textsuperscript{a}"
        if configuration:
            terms=[r"{\raggedright "+term+r"\par}" for term in terms]
        lines.append(" & ".join(terms)+r" \\")
    lines += [r"\bottomrule",r"\end{tabular}",r"\endgroup"]
    return "\n".join(lines)+"\n"


def tables(out,data):
    for stem,(headers,exact,rounded) in table_specs(data):
        path=out/"tables"/stem
        write_csv(path.with_suffix(".csv"),[dict(zip(headers,r,strict=True)) for r in exact],headers)
        text(path.with_suffix(".tex"),table_latex(stem,headers,rounded))
        text(path.with_suffix(".md"),markdown(headers,rounded))
        write_json(out/"data"/f"{stem}_display.json",dict(headers=headers,exact=exact,rendered=rounded,
                   source_sha256=data["sources"][stem[:5]]))


def lookup(rows,**criteria):
    matches=[r for r in rows if all(r.get(key)==value for key,value in criteria.items())]
    require(len(matches)==1,f"Expected one matching row: {criteria}")
    return matches[0]


def handoff(root,out,data,figure_caps):
    exp=read_json(root/"results/phase6/data/experiment_summary.json")
    phase5=read_json(root/"results/phase5/data/summary.json")
    combined=lookup(phase5["pool"],cohort="all120",method="STaR")
    common=dict(cohort="all120",subset="all",tape="phase6")
    ft=lookup(exp["fixed-topology"]["contrasts"],challenger="STaR",reference="FT-SAA",metric="R_pp",**common)
    ft_return=lookup(exp["fixed-topology"]["contrasts"],challenger="STaR",reference="FT-SAA",metric="completion",**common)
    as1=lookup(exp["as1"]["contrasts"],challenger="AS1",reference="STaR",metric="R_pp",**common)
    ret=lookup(exp["as1"]["contrasts"],challenger="AS1",reference="STaR",metric="completion",**common)
    primary,sls=data["paired"]
    cmp={r["method"]:r for r in data["comparison"]}
    ab={r["method"]:r for r in data["ablation"]}
    archive_sls=100*(1-cmp["STaR"]["draws"]/cmp["SLS"]["draws"])
    gain_draws=ab["STaR-NPP"]["draws"]-ab["STaR"]["draws"]
    timing=data["timing_notes"]
    stop=timing["primary_stops"]
    t50=lookup(data["timing_effects"],guard_ms=50,metric="R_pp")
    w50=lookup(data["timing_effects"],guard_ms=50,metric="wall_ms")
    w20=lookup(data["timing_effects"],guard_ms=20,metric="wall_ms")
    signed=lambda r:f'{r["mean"]:+.3f} [{r["lo95"]:+.3f}, {r["hi95"]:+.3f}]'
    fmt=lambda r:f'{r["mean_pp"]:+.2f} [{r["lo95_pp"]:+.2f}, {r["hi95_pp"]:+.2f}]'
    notes=[
        "Frozen benchmark and registered holdout settings. The 4,543 no-charge holdout routes are unchanged and excluded "
        "from exposed metrics. There are no endogenous queues or wait-dependent decisions. Attainment means the "
        "one-sided 95% Wilson lower bound reaches 0.95. With 64 trials and 512 draws per trial the 131,072 scenario "
        "ceiling cannot bind. The STaR–FSPC reliability contrast is the sole confirmatory endpoint.",
        f'Six methods on 2,321 exposed holdout routes in the archived six-worker, 64-plan cohort. Attained is a count out of '
        f'2,321. Full return includes late trajectories. Higher reliability and attainment and lower return, work and time are '
        f'favorable. Search draws exclude validation. ᵃ Original route has no optimization. {cmp["CON"]["wall_ms"]:.2f} ms '
        f'is observed setup/evaluator time. STaR consumed {cmp["STaR"]["trials"]:.2f} trials versus {cmp["FSPC"]["trials"]:.2f} '
        f'for fixed-station repair. STaR used {archive_sls:.2f}% fewer draws than scenario search with mean wall '
        f'{cmp["STaR"]["wall_ms"]:.2f} versus {cmp["SLS"]["wall_ms"]:.2f} ms. Mean-wait repair finished '
        f'{cmp["STaR"]["completion"]-cmp["MWR"]["completion"]:.2f} native units sooner than STaR on average. '
        'Quantile repair had similar mean completion. CSV values retain full precision.',
        f'Exploratory component removals on 2,321 exposed holdout routes. Loss is full STaR minus ablation. Partial charging '
        f'removes quantity-only moves and partial allocation on new topologies while retaining the original incumbent. Slack '
        f'prioritization changes order only. Analytical screening removes analytical rejection while retaining ranking and '
        f'prefix evaluation. Removing progressive evaluation fully scores admitted candidates. STaR used {gain_draws:,.0f} fewer '
        f'draws than this ablation, with identical recorded reliability, attainment and completion on every route. Effects '
        'are nonadditive. Timing is omitted because measurements span separate cohorts. The modest slack result reverses '
        'sign in development. Exact effects and intervals are in data/Tab03_exact.csv.',
    ]
    text(out/"FIGURE_CAPTIONS.md","# Figure captions\n\n"+"\n\n".join(f"## {k}\n\n{v}" for k,v in figure_caps.items()))
    text(out/"TABLE_NOTES.md","# Table notes\n\n"+"\n\n".join(f"## {k}\n\n{v}" for k,v in zip(TABLE_STEMS,notes,strict=True)))
    entries=[]
    for i,stem in enumerate(STEMS):
        entries.append(dict(id=stem,kind="figure",path=f"figures/{stem}.pdf",formats="PDF, SVG, PNG; JSON sidecar",
            cohort=("Selected holdout route","Frozen algorithm","2,321 holdout routes","2,321 holdout routes",
                    "118-route Phase 6 timing panel")[i],notes="FIGURE_CAPTIONS.md"))
    for i,stem in enumerate(TABLE_STEMS):
        entries.append(dict(id=stem,kind="table",path=f"tables/{stem}.tex",formats="TeX, CSV, Markdown",
            cohort="Full benchmark and holdout design" if i==0 else "2,321 holdout routes",notes="TABLE_NOTES.md"))
    write_csv(out/"EXHIBIT_INDEX.csv",entries)
    text(out/"METHOD_GLOSSARY.md","# Method glossary\n\n| Acronym | Paper label | Algorithm role |\n| --- | --- | --- |\n"+
         "\n".join(f'| {method} | {label} | {"Proposed Slack-Targeted Stochastic Charging Repair" if method=="STaR" else "Additional scientific control" if method in ("FSPC","SLS") else "Principal baseline"} |'
                   for method,label in METHODS.items())+
         "\n\nFSPC adjusts partial-charge quantities on the source station topology. SLS is scenario-based local search. "
         "CON is the unchanged constructive plan. MWR uses mean waits and QBR uses per-visit quantiles.\n\n"
         "NPC, NSP, NAS and NPP respectively remove partial charging, slack prioritization, analytical screening and "
         "progressive evaluation. AS1 and FT-SAA are Phase 6 supplementary methods. Archive key `c64` is the 64-plan budget.")
    text(out/"CLAIMS_AND_LIMITATIONS.md",f"""# Claims and limitations for the writer

## Main evidence

- **Registered result (Fig03, Tab02).** STaR minus FSPC {fmt(primary)} pp over 2,321 exposed routes and 48 parents. Actual mean trials were {cmp['STaR']['trials']:.2f} versus {cmp['FSPC']['trials']:.2f} at a common maximum of 64. The contrast estimates a difference against the implemented heuristic under the frozen budget. It does not isolate the role of topology or establish an advantage over optimal fixed-topology quantities. Parent-equal sensitivity was {primary['parent_mean_pp']:+.2f} pp [{primary['parent_lo95_pp']:.2f}, {primary['parent_hi95_pp']:.2f}].
- **Scenario search (Fig03, Tab02, Fig05).** Archived STaR minus SLS {fmt(sls)} pp, exploratory. STaR used {archive_sls:.2f}% fewer draws and took {cmp['STaR']['wall_ms']:.2f} versus {cmp['SLS']['wall_ms']:.2f} ms. In the 118-route panel, STaR used {timing['relative_reduction_pct']:.2f}% fewer draws at 50 ms. Reliability was {signed(t50)} pp and paired route-median wall was {signed(w50)} ms. Overshoot reached {stop['STaR']['max_overshoot_ms']:.2f}/{stop['SLS']['max_overshoot_ms']:.2f} ms on {stop['STaR']['overshoots']}/{stop['SLS']['overshoots']} of 354 repeats per method. At 20 ms, paired wall was {signed(w20)} ms. Keep work and elapsed results distinct across cohorts.
- **Full benchmark (Phase 5).** The pooled 120-instance values of {100*combined['mean_R']:.2f}% STaR mean reliability and {combined['lower_bound_attained']:,}/{combined['n']:,} attainment are descriptive. Use the 96-instance holdout as the primary population.
- **Mechanisms (Fig01, Fig04).** Fig01 is an outcome-selected example using the recorded selection rule. Three-plus original visits contribute {data['complexity_notes']['net_share']:.1f}% of the net signed difference and account for {data['complexity'][-1]['nonattained']} residual failures. R2/RC2 account for 109/110 holdout nonattainments. Phase 6 associates tighter source slack and higher complexity with failure. Draw causal conclusions from none of these strata.
- **Components (Tab03, Phase 5).** Partial charging bundles two changes. Slack prioritization has a modest holdout difference and reverses sign in development. The analytical screen bounds true fixed-plan reliability, while the finite empirical score can exceed this bound. Prefix pruning compares with the same incumbent on the same tape subject to numerical tolerance. Binding budgets can change later search.

## Supplementary disclosure

- **AS1, 113-route Phase 6 one-visit panel.** AS1 minus STaR {signed(as1)} pp and {ret['mean']:+.2f} native completion units. The reliability interval crosses zero. AS1 is restricted to at most one visit. The hybrid was excluded.
- **FT-SAA, 118-route Phase 6 panel.** STaR minus FT-SAA {signed(ft)} pp and {ft_return['mean']:+.2f} native completion units. Five of 22 multi-visit cases obtained complete MILP certificates. Valid fallbacks remain in the panel. See the Phase 6 report and handoff for every status and paired result.

## Scope

Station laws are synthetic. Four station-attribute tables were reused and all appeared in development. Customer assignment and order are fixed, charging is linear, and station hours are disabled. The study has no live queues, fleet congestion, routing recourse or fleet-wide chance guarantee. Intervals are pointwise, unadjusted and conditional on archived validation. Except for the registered FSPC contrast, the comparisons are exploratory. The study does not establish global optimality, universal superiority, a general wall-time speedup or literature priority.
""")
    text(out/"PAPER_OUTLINE.md","""# Exhibit placement map

| Section | Exhibit |
| --- | --- |
| Problem and model | Fig01, actual charging repair |
| Method | Fig02, frozen framework |
| Setup | Tab01, experimental configuration |
| Main comparative evidence | Tab02 and Fig03 |
| Route mechanisms | Fig04 |
| Components and computational work | Tab03 and Fig05 |

Plan around ten pages including references. Template and pagination remain to be checked. If space is tight, move Fig05 to the supplement first and retain its numerical disclosure. Keep Fig01–Fig04 in the main paper.
""")
    text(out/"README_RESULTS_PACKAGE.md","""# STaR-EVRP conference exhibits

Five figures in 400-DPI PNG, vector PDF and editable SVG, plus three tables in LaTeX, CSV and Markdown. Start with EXHIBIT_INDEX.csv, FIGURE_CAPTIONS.md, TABLE_NOTES.md and CLAIMS_AND_LIMITATIONS.md. The CSV exports retain full precision. LaTeX and Markdown implement the display rounding.

Use this package with the Phase 5 full-benchmark and Phase 6 supplementary handoffs. Source paths are relative to the project root. The manifest binds sources and derivatives to their SHA-256 hashes. Figures use DejaVu Sans at 178 mm double-column width without assuming a conference template. Use PDF where the venue supports it. Holdout and timing-panel estimates retain separate denominators.
""")
    lines=["# Source traceability","",f"Reviewed base `{BASE}`. Frozen executable `{FROZEN}`.",
           "Phase 7 reads Phases 1–6 as immutable inputs. Figure 1 uses the original Phase 3 ZIP member, matching "
           "frozen validation/plan bundles and actual benchmark coordinates.",""]
    for name,refs in data["sources"].items():
        lines.extend((f"## {name}","",*(f"- `{path}` — `{digest}`" for path,digest in refs.items()),""))
    lines.extend(("## Diagram semantics","",
                  "- Rank visits by increasing marginal upper bound and prioritize gaps near the most critical visit.",
                  "- The analytical screen uses the minimum marginal true-reliability bound and rejects below target minus 1e-12.",
                  "- At prefix k = 128 out of S = 512, optimistic reliability is (m + S − k) / S. Lower completion "
                  "is (C_k + (S − k) C_0) / S. Here m counts prefix successes, C_k sums prefix completion, and C_0 is zero-wait return. "
                  "The frozen optimistic score subtracts a 1e-8 completion cushion.",
                  "- Strict improvements restart the neighborhood. Independent validation follows search without feedback.",
                  "","## Companion archives","",
                  "- `results/phase5/STaR_EVRP_FINAL_RESULTS_HANDOFF.zip`",
                  "- `results/phase6/STaR_EVRP_PHASE6_SCIENTIFIC_SUPPLEMENT.zip`"))
    text(out/"SOURCE_TRACEABILITY.md","\n".join(lines))


def build(root,out,width):
    require(width==178,"The canonical exhibits use a fixed 178 mm double-column layout")
    data=gather(root,out)
    labels=captions(data)
    draw(root,out,data,width,labels)
    tables(out,data)
    handoff(root,out,data,labels)
    return data
