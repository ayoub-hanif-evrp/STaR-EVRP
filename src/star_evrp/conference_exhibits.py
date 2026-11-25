"""Three publication tables and their writer handoff."""

from star_evrp.conference_data import BASE, FROZEN, METHODS, gather
from star_evrp.conference_figures import ARTWORK, STEMS, SUPPLEMENTARY, draw
from star_evrp.phase4_release import LATEX, markdown
from star_evrp.phase4_results import read_json, require
from star_evrp.phase6_archive import write_bytes, write_csv, write_json

TABLE_STEMS = ("Tab01_experimental_configuration","Tab02_method_comparison","Tab03_component_ablation")


def text(path,content):
    write_bytes(path,(content.rstrip()+"\n").encode("utf-8"))


def captions(data):
    main,complex_case,adverse=(data["examples"][name] for name in ("Fig01","Sup01","Sup02"))
    loc=main["selection"]["chosen"]
    con,star=main["metrics"]
    stations=[r["node"] for r in main["stops"] if r["type"]=="station"]
    c=complex_case["selection"]["chosen"]
    a=adverse["selection"]["chosen"]
    overshoots=data["timing_notes"]["primary_stops"]
    result=(
        f'Outcome-selected holdout example {loc["parent"]}/{loc["variant"]}, route {loc["route"]}. '
        f'STaR removed station {stations[0]} after the last customer and inserted a visit to {stations[1]} before '
        f'the first. Observed reliability uses {con["successes"]:,} and {star["successes"]:,} successes on the '
        f'same {con["scenarios"]:,}-scenario archived validation tape. The observed 100% is an empirical estimate. '
        'Maps share equal scale and matched detail bounds. Both plans serve the same customers in order. The battery '
        'profiles follow each plan’s own distance from the depot. Horizontal references mark zero and nominal '
        'capacity, vertical steps show charging, and numbered circles identify customers. Mean full return includes late '
        'scenarios. See the physical ledger for the change in travel, charging and readiness waits. Units are native.',
        'Frozen Slack-Targeted Stochastic Charging Repair (STaR). The initial plan is scored on a shared 512-draw search '
        'tape. Visit priority follows the marginal isolated-wait reliability bound and gaps near the most critical visit '
        'come first. Proposals interleave quantity and topology moves. Duplicates are skipped. A newly admitted plan counts '
        'as a trial even when its deterministic check fails. The analytical screen is active only for an empirically attaining '
        'incumbent. It bounds true fixed-plan reliability, which the finite-tape estimate may exceed. The 128-draw '
        'prefix bound uses the same tape, and survivors extend to 512. The score prefers attainment. At or above target, '
        'minimize full return then maximize reliability. Below target, maximize reliability then minimize full return. '
        'A strict gain updates and restarts. Exhaustion or a guard returns the incumbent for independent validation without search feedback. '
        'Operator sketches are conceptual. New topologies use minimal and, where applicable, downstream-rate-based '
        'allocations. Letters identify stations and numbers identify customers.',
        'Paired reliability on 2,321 exposed holdout routes from 48 parents. Panel (a) shows route-weighted contrasts '
        'in percentage points (pp) with pointwise 95% family-stratified parent-cluster bootstrap intervals (9,999 '
        'resamples with A/B siblings and routes kept together). Fixed-station repair is confirmatory and scenario search '
        'is exploratory. The common 64-candidate maximum yielded 62.67 versus 20.18 mean trials. Panel (b) counts '
        'observed directions versus fixed-station repair. Equal denotes matching successes out of 10,000 and does '
        'not identify equal true probabilities.',
        'Holdout routes grouped by original charging visits. Panel (a) shows STaR minus fixed-station repair in '
        'percentage points with exploratory pointwise 95% parent-cluster intervals. The one-visit lower endpoint '
        'is slightly negative. Panel (b) shows counts and shares failing the individual reliability target criterion, '
        'a one-sided 95% Wilson lower bound of at least 0.95. Routes with 3+ visits account for 102 of 110 remaining '
        'nonattainments and 89.0% of the net signed gain. Parents may span bins. These associations are descriptive.',
        'Separate exploratory timing panel of 118 routes from 60 parents (23 development, 95 holdout). Each 20, 50 '
        'or 100 ms cooperative runtime guard used three serial repeats per method and route (2,124 runs). Panel (a) '
        'shows route-mean independent validation reliability and incremental search draws. Panel (b) shows paired '
        'reliability differences with pointwise 95% family-by-partition parent intervals after averaging repeats. At '
        '50 ms, STaR used about 18,696 draws versus 33,699 for scenario search (44.52% fewer). The paired differences '
        'were −0.134 pp [−0.510, +0.087] for reliability and +0.233 ms [−1.018, +1.461] for route-median elapsed time. '
        f'STaR exceeded the guard on {overshoots["STaR"]["overshoots"]}/{overshoots["STaR"]["repeats"]} repeats '
        f'and scenario search on {overshoots["SLS"]["overshoots"]}/{overshoots["SLS"]["repeats"]}. '
        'Both intervals include zero. The panel does not establish wall-time superiority or equivalence.',
        f'Outcome-selected exploratory case {c["parent"]}/{c["variant"]}, route {c["route"]}. '
        f'The rule chose the lower-median customer count among {complex_case["selection"]["candidate_count"]} '
        'improving R2/RC2 holdout routes with changed topology and target attainment. Maps share equal aspect and '
        'identical bounds. S1, S2 and subsequent labels identify charging events in order on each plan. '
        'SUPPLEMENTARY_NOTES.md gives all station IDs, charge quantities and rates. Battery profiles use independently '
        'accumulated Euclidean distance on common physical scales. Full return is unconditional. This example illustrates a saved repair.',
        f'Outcome-selected adverse case {a["parent"]}/{a["variant"]}, route {a["route"]}. This pair had the largest '
        'observed STaR loss versus fixed-station repair on the archived holdout tape. Panel (a) shows paired differences '
        'in deterministic customer service-start slack with zero station waits. Panel (b) reports archived stochastic validation. '
        'Customer order matches. A smaller slack at a visit can indicate sensitivity to delays. The archive does not '
        'identify a causal search mechanism or a stochastic trajectory.',
    )
    return dict(zip(ARTWORK,result,strict=True))


def table_specs(data):
    cfg=data["config"]
    dev,hold=cfg["partitions"]
    caps=cfg["work_limits"]
    overview=[
        ["Benchmark",f'Extended Homberger, {cfg["customers_per_instance"]:,} customers per instance. '
         f'{cfg["instances"]} instances from {cfg["parents"]} A/B parents.'],
        ["Split and route coverage",
         f'{dev["instances"]} development and {hold["instances"]} holdout instances ({dev["parents"]} and {hold["parents"]} parents, respectively). '
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
    h2=["Method","Mean R (%)","Attained","Full return","Trials","Search draws","Wall (ms)"]
    h3=["Component removed","Mean R (%)","Attained","Search draws","Draw difference","Reliability loss (pp)"]
    full_draws=data["ablation"][0]["draws"]
    comparison=[[r["label"],r["reliability_pct"],r["attained"],r["completion"],r["trials"],r["draws"],r["wall_ms"]] for r in data["comparison"]]
    ablation=[[r["component"],r["reliability_pct"],r["attained"],r["draws"],r["draws"]-full_draws if r["loss_pp"] is not None else None,r["loss_pp"]] for r in data["ablation"]]
    show2=[[label,f"{R:.2f}",f"{n:,}",f"{c:,.2f}",f"{trials:.2f}",f"{draws:,.0f}",f"{wall:.2f}"]
           for label,R,n,c,trials,draws,wall in comparison]
    show3=[[label,f"{R:.2f}",f"{n:,}",f"{draws:,.0f}",f"{change:+,.0f}" if change is not None else "—",f"{loss:.3f}" if loss is not None else "—"]
           for label,R,n,draws,change,loss in ablation]
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
        terms=[v.translate(LATEX).replace("—",r"\textemdash{}") for v in row]
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


def supplementary_notes(out,data):
    main,complex_case,adverse=(data["examples"][n] for n in ("Fig01","Sup01","Sup02"))
    original,repaired=main["totals"]
    delta=lambda k:repaired[k]-original[k]
    stations=[r for r in main["stops"] if r["type"]=="station"]
    markdown_tables=[]
    for example in (main,complex_case,adverse):
        charges=[r for r in example["stops"] if r["type"]=="station"]
        markdown_tables.append(markdown(
            ["Plan","Visit","Station ID","After customer","Charge","Rate","Charging time"],
            [[METHODS[r["plan"]],f'S{r["station_order"]}',str(r["node"]),str(r["customers_served"]),
              f'{r["charged"]:.2f}',f'{r["charging_rate"]:.4f}',f'{r["charging_duration"]:.2f}'] for r in charges]))
    lo,hi=adverse["metrics"]
    t=data["timing_notes"]
    timing=data["timing_effects"]
    fmt=lambda r:f'{r["mean"]:+.3f} [{r["lo95"]:+.3f}, {r["hi95"]:+.3f}]'
    timing_table=markdown(["Guard","Reliability difference (pp)","Route-median elapsed difference (ms)"],[
        [f"{g} ms",fmt(lookup(timing,metric="R_pp",guard_ms=g)),fmt(lookup(timing,metric="wall_ms",guard_ms=g))]
        for g in (20,50,100)])
    text(out/"SUPPLEMENTARY_NOTES.md",f"""# Physical and timing details

## Fig01 physical ledger

The archived original fills at station {stations[0]["node"]} and returns with {original["final_battery"]:.2f} units remaining. The saved repair charges at station {stations[1]["node"]} and returns with {max(0,repaired["final_battery"]):.2f} units. The reduction in charge is explained by reduced final residual and the change in travel energy. With consumption of {original["consumption_rate"]:g} unit per distance unit, the charge change {delta("energy_added"):+.2f} equals the travel energy change {delta("energy_consumed"):+.2f} plus the residual change {delta("final_battery"):+.2f}. There is no additional energy reserve in the validator.

The deterministic return changes by {delta("zero_wait_return"):+.2f} time units. Its components are {delta("total_distance"):+.2f} travel, {delta("charging_duration"):+.2f} charging time at heterogeneous rates, {delta("readiness_wait"):+.2f} readiness-floor waiting and {delta("service_duration"):+.2f} service. The archived means {main["metrics"][0]["completion"]:,.2f} and {main["metrics"][1]["completion"]:,.2f} include stochastic waits and late returns. The deterministic decomposition explains the physical change and cannot attribute the stochastic difference to any single component.

{markdown_tables[0]}
## Sup01 complex route

The charging-event sequence is separate from the fixed customer order. A zero in the after-customer column identifies a pre-customer station visit. All quantities are native. Exact event times, distances, battery arrivals and departures, rates, source keys and digests are in the corresponding source CSV and JSON files.

{markdown_tables[1]}
## Sup02 adverse example

The archived validation difference is {(hi["reliability"]-lo["reliability"])*100:+.2f} percentage points. Fixed-station repair recorded {lo["customer_only"]:,} customer-only, {lo["depot_only"]:,} depot-only and {lo["joint"]:,} joint failures. STaR recorded {hi["customer_only"]:,}, {hi["depot_only"]:,} and {hi["joint"]:,}, respectively. The deterministic slack is a check on the saved routes with zero station waits. It provides context for possible delay sensitivity. The aggregate observations cannot establish which realized waits drove the difference.

{markdown_tables[2]}
## Separate guard panel

Paired STaR minus scenario search, with pointwise 95% parent-cluster intervals. Guards are cooperative. The 50 ms row includes zero for both outcomes. The {t["relative_reduction_pct"]:.2f}% draw reduction at 50 ms measures simulation work. The archived 20 ms elapsed contrast favored scenario search. Neither panel supports a general runtime superiority or equivalence claim.

{timing_table}
""")


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
        f'Six methods on 2,321 exposed holdout routes from the archived six-worker, 64-candidate cohort. R is reliability. '
        f'Attained is a count out of 2,321. Full return uses native time units and includes late trajectories. '
        f'Higher reliability and attainment and lower return, work and time are '
        f'favorable. Search draws exclude validation. ᵃ Original route has no optimization. {cmp["CON"]["wall_ms"]:.2f} ms '
        f'is observed setup/evaluator time. Trials count the initial check and distinct examined candidates. STaR consumed {cmp["STaR"]["trials"]:.2f} trials versus {cmp["FSPC"]["trials"]:.2f} '
        f'for fixed-station repair. STaR used {archive_sls:.2f}% fewer draws than scenario search with mean wall '
        f'{cmp["STaR"]["wall_ms"]:.2f} versus {cmp["SLS"]["wall_ms"]:.2f} ms. Mean-wait repair finished '
        f'{cmp["STaR"]["completion"]-cmp["MWR"]["completion"]:.2f} native units sooner than STaR on average. '
        'Quantile repair had similar mean completion. CSV values retain full precision.',
        f'Exploratory component removals on 2,321 exposed holdout routes. Reliability loss is full STaR minus ablation. Draw difference is ablation minus full STaR. Partial charging '
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
    for stem in SUPPLEMENTARY:
        entries.append(dict(id=stem,kind="supplementary figure",path=f"supplementary/{stem}.pdf",
            formats="PDF, SVG, PNG; JSON sidecar",cohort="Outcome-selected holdout route",notes="SUPPLEMENTARY_NOTES.md"))
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
         "progressive evaluation. AS1 is the analytical single-visit optimizer and FT-SAA is the fixed-topology optimizer. Both are Phase 6 supplementary methods. Archive key `c64` is the 64-plan budget.")
    text(out/"CLAIMS_AND_LIMITATIONS.md",f"""# Claims and limitations for the writer

## Main evidence

- **Registered result (Fig03, Tab02).** STaR minus fixed-station repair {fmt(primary)} pp over 2,321 exposed routes and 48 parents. Actual mean trials were {cmp['STaR']['trials']:.2f} versus {cmp['FSPC']['trials']:.2f} at a common maximum of 64. The contrast estimates a difference against the implemented heuristic under the frozen budget. It does not isolate the role of topology or establish an advantage over optimal fixed-topology quantities. Parent-equal sensitivity was {primary['parent_mean_pp']:+.2f} pp [{primary['parent_lo95_pp']:.2f}, {primary['parent_hi95_pp']:.2f}].
- **Scenario search (Fig03, Tab02, Fig05).** Archived STaR minus scenario search {fmt(sls)} pp, exploratory. STaR used {archive_sls:.2f}% fewer draws and took {cmp['STaR']['wall_ms']:.2f} versus {cmp['SLS']['wall_ms']:.2f} ms. In the 118-route panel, STaR used {timing['relative_reduction_pct']:.2f}% fewer draws at 50 ms. Reliability was {signed(t50)} pp and paired route-median wall was {signed(w50)} ms. Overshoot reached {stop['STaR']['max_overshoot_ms']:.2f}/{stop['SLS']['max_overshoot_ms']:.2f} ms on {stop['STaR']['overshoots']}/{stop['SLS']['overshoots']} of 354 repeats per method. At 20 ms, paired wall was {signed(w20)} ms. Keep work and elapsed results distinct across cohorts.
- **Full benchmark (Phase 5).** The pooled 120-instance values of {100*combined['mean_R']:.2f}% STaR mean reliability and {combined['lower_bound_attained']:,}/{combined['n']:,} attainment are descriptive. Use the 96-instance holdout as the primary population.
- **Mechanisms (Fig01, Fig04).** Fig01 is an outcome-selected example using the recorded selection rule. Three-plus original visits contribute {data['complexity_notes']['net_share']:.1f}% of the net signed difference and account for {data['complexity'][-1]['nonattained']} residual failures. R2/RC2 account for 109/110 holdout nonattainments. Phase 6 associates tighter source slack and higher complexity with failure. These strata show descriptive associations. Sup01 and Sup02 are outcome-selected cases.
- **Components (Tab03, Phase 5).** Partial charging bundles two changes. Slack prioritization has a modest holdout difference and reverses sign in development. The analytical screen bounds true fixed-plan reliability, while the finite empirical score can exceed this bound. Prefix pruning compares with the same incumbent on the same tape subject to numerical tolerance. Binding budgets can change later search.

## Supplementary disclosure

- **AS1, 113-route Phase 6 one-visit panel.** AS1 minus STaR {signed(as1)} pp and {ret['mean']:+.2f} native completion units. The reliability interval crosses zero. AS1 is restricted to at most one visit. The hybrid was excluded.
- **FT-SAA, 118-route Phase 6 panel.** STaR minus FT-SAA {signed(ft)} pp and {ft_return['mean']:+.2f} native completion units. Five of 22 multi-visit cases obtained complete MILP certificates. Valid fallbacks remain in the panel. See the Phase 6 report and handoff for every status and paired result.

## Scope

Station laws are synthetic. Four station-attribute tables were reused and all appeared in development. Customer assignment and order are fixed, charging is linear, and station hours are disabled. The study has no live queues, fleet congestion, routing recourse or fleet-wide chance guarantee. Intervals are pointwise, unadjusted and conditional on archived validation. Except for the registered fixed-station repair contrast, the comparisons are exploratory. The study does not establish global optimality, universal superiority, a general wall-time speedup or literature priority.
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

Five main figures and two supplementary figures in 400-DPI PNG, vector PDF, and editable SVG. Three main tables in LaTeX, CSV, and Markdown. Sup01 and Sup02 are documented in SUPPLEMENTARY_NOTES.md. Start with EXHIBIT_INDEX.csv, FIGURE_CAPTIONS.md, TABLE_NOTES.md and CLAIMS_AND_LIMITATIONS.md. The CSV exports retain full precision. LaTeX and Markdown implement the display rounding.

Use this package with the Phase 5 full-benchmark and Phase 6 supplementary handoffs. Source paths are relative to the project root. The manifest binds sources and derivatives to their SHA-256 hashes. Figures use DejaVu Sans at 178 mm double-column width. SVGs embed editable Latin and Greek fonts under the included FONT_LICENSE.txt. Use PDF where the venue supports it. Holdout and timing-panel estimates retain separate denominators. Final pagination depends on the conference template.
""")
    lines=["# Source traceability","",f"Reviewed base `{BASE}`. Frozen executable `{FROZEN}`.",
           "Phase 8 reads Phases 1–6 as immutable inputs and refines the prior Git release. Example figures use the original Phase 3 ZIP member, matching "
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
    supplementary_notes(out,data)



def build(root,out,width):
    require(width==178,"The canonical exhibits use a fixed 178 mm double-column layout")
    data=gather(root,out)
    labels=captions(data)
    draw(root,out,data,width,labels)
    tables(out,data)
    handoff(root,out,data,labels)
    return data
