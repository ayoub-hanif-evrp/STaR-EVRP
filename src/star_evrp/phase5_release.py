"""Export and validate paper-facing Phase 5 evidence (no manuscript)."""

from collections import Counter
from pathlib import Path
from statistics import fmean
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from star_evrp.phase4_release import csv_export, markdown, png_audit, tex_probe, tex_table
from star_evrp.phase4_results import file_sha, git, read_json, require, write_json
from star_evrp.phase5_analysis import ABL, COHORTS, MAIN, analyze, export_records
from star_evrp.phase5_exhibits import LABEL, PROFILE_NOTE, figures
from star_evrp.phase5_experiments import check_unchanged, get_protocol

SCRIPT="python -B scripts/run_phase5.py"
EXPLORATORY="All comparisons except the archived STaR–FSPC holdout reliability contrast are exploratory or descriptive."
TIME="Archived Phase 3 and new Phase 5 runtime cohorts are separate. The 5-second guard is cooperative. No speedup is inferred from draw counts."
SAME_CAP="A shared maximum of 64 unique plans does not imply equal consumed work; FSPC is a restricted heuristic, not a quantity-only optimum."


def dec(value):
    return "NA" if value is None else f"{value:.2f}"


def pct(value):
    return "NA" if value is None else dec(100*value)


def number(value):
    return "NA" if value is None else f"{value:.0f}"


def effect_label(row,scale=1):
    return "NA" if row["mean"] is None else f'{scale*row["mean"]:+.2f} [{scale*row["lo95"]:+.2f}, {scale*row["hi95"]:+.2f}]'


def cell(row, *fields):
    return [row[field] for field in fields]


def tables(summary,out):
    index=[]

    def add(name,headers,rows,notes,source,cohort="c64"):
        folder="main" if name.startswith("T") else "supplementary"
        where=out/"tables"/folder/name
        vals=[[str(entry) if entry is not None else "NA" for entry in row] for row in rows]
        csv_export(where.with_suffix(".csv"),headers,vals)
        where.with_suffix(".tex").write_text(tex_table(headers,vals),encoding="utf-8")
        where.with_suffix(".md").write_text(markdown(headers,vals),encoding="utf-8")
        side=out/"data/table_rows"/f"{name}.json"
        write_json(side,{"columns":headers,"rows":vals,"source":source})
        index.append({"filename":where.with_suffix(".tex").relative_to(out).as_posix(),"name":name,"caption":notes,
                      "cohort":cohort,"source":source,"source_sha256":file_sha(side)})

    population=summary["population"]
    pop=[]
    for cohort in COHORTS:
        cases=[row for row in population if cohort=="all120" or row["partition"]==cohort]
        pop.append([LABEL[cohort],len(cases),len({row["parent"] for row in cases}),
                    *[sum(row[key] for row in cases) for key in ("all_routes","exposed","zero_charge","CON_below_point","CON_nonattained")]])
    add("T01_population",["Cohort","Problems","Parents","All routes","Exposed","No charge","CON point <.95","CON not LB"],pop,
        "Coverage of all 120 original fleets. No-charge routes remain unchanged and outside repair estimates. Point-below-target and Wilson nonattainment are distinct.",
        "data/population_by_instance.csv","all cohorts")
    pool={(row["cohort"],row["method"]):row for row in summary["pool"]}
    quality=lambda row:[pct(row["mean_R"]),f'{row["lower_bound_attained"]}/{row["n"]}',
                        pct(row["lower_bound_attained"]/row["n"]),dec(row["full_completion_time"])]
    add("T02_main_methods",["Cohort","Method","R (%)","LB / n","LB (%)","Completion","Draws","Wall ms"],[
        [LABEL[cohort],method,*quality(pool[cohort,method]),number(pool[cohort,method]["search_scenarios"]),
         dec(pool[cohort,method]["search_wall_ms"])] for cohort in COHORTS for method in MAIN],
        "Main presentation methods only; SLS and FSPC also tested. T07 is mandatory disclosure. R and LB higher is better; completion is full depot return, "
        "native time units, lower is better. No pooled wall statistics. "+TIME,"data/summary.json: pool","all cohorts")
    paired={(row["cohort"],row["comparison"],row["metric"]):row for row in summary["paired"]}
    def effects(cohort,method,fields):
        return [effect_label(paired[cohort,method,metric],scale) for metric,scale in fields]
    add("T03_main_paired_effects",["Cohort","Control","Pairs","R diff. (pp)","LB diff. (pp)","Completion diff."],[
        [LABEL[cohort],method,paired[cohort,method,"reliability"]["n"],
         *effects(cohort,method,(("reliability",100),("attained",100),("full_completion",1)))]
        for cohort in COHORTS for method in MAIN[:-1]],
        "STaR minus control; unadjusted exploratory parent-cluster 95% intervals. Positive favors reliability and attainment; negative favors completion.",
        "data/summary.json: paired","all cohorts")
    add("T04_ablation_quality",["Cohort","Method","R (%)","LB / n","LB (%)","Completion"],[
        [LABEL[cohort],method,*quality(pool[cohort,method])] for cohort in COHORTS for method in ABL],
        "One component disabled at a time (NPC combines removal of amount changes with full allocation on new topology moves). All ablation effects exploratory. Native full completion.",
        "data/summary.json: pool","all cohorts")
    add("T05_ablation_work",["Partition","Method","Trials","Draws","Screen rej.","Prefix rej.","Wall ms","CPU ms"],[
        [row["partition"],row["method"],dec(row["unique_trials"]),number(row["search_scenarios"]),
         dec(row["analytical_rejections"]),dec(row["prefix_rejections"]),dec(row["search_wall_ms"]),dec(row["search_cpu_ms"])]
        for row in summary["work"] if row["method"] in ABL],
        "Per-route means. Holdout STaR/NPC come from Phase 3; other times are newly measured; development controls and ablations used separate runs. "
        "NAS screen rejections are zero but it still computes priorities. NPP full-batch search has no prefix pruning. "+TIME,
        "data/summary.json: work","partitioned runtime")
    family={(row["cohort"],row["family"],row["variant"],row["method"]):row for row in summary["family"]}
    cells=sorted({(row["family"],row["variant"]) for row in summary["population"]})
    add("T06_family_results",["Cohort","Family","V","n","CON LB","MWR LB","QBR LB","STaR LB"],[
        [LABEL[cohort],name,variant,family[cohort,name,variant,"CON"]["n"],
         *[family[cohort,name,variant,method]["lower_bound_attained"] for method in MAIN]]
        for cohort in ("holdout","all120") for name,variant in cells],
        "Attaining counts in distinct family and variant cells; originally exposed routes only. All 120 includes development; descriptive.",
        "data/summary.json: family","holdout + all120")
    primary=paired["holdout","FSPC","reliability"]
    sls=pool["holdout","SLS"]
    star=pool["holdout","STaR"]
    savings=100*(1-star["search_scenarios"]/sls["search_scenarios"])
    add("T07_primary_evidence",["Holdout c64 evidence","Pairs","Parents","Estimate or comparison","Status"],[
        ["STaR – FSPC reliability (pp)",primary["n"],primary["parents"],effect_label(primary,100),"Confirmatory"],
        ["Parent-equal reliability (pp)",primary["n"],primary["parents"],
         f'{100*primary["parent_mean"]:.2f} [{100*primary["parent_lo95"]:.2f}, {100*primary["parent_hi95"]:.2f}]',"Sensitivity"],
        ["STaR – SLS reliability (pp)",primary["n"],primary["parents"],effect_label(paired["holdout","SLS","reliability"],100),"Exploratory"],
        ["STaR vs SLS search draws",primary["n"],primary["parents"],
         f'{star["search_scenarios"]:.0f} / {sls["search_scenarios"]:.0f} ({savings:.2f}% fewer)',"Descriptive"],
        ["STaR vs SLS wall ms",primary["n"],primary["parents"],f'{star["search_wall_ms"]:.2f} / {sls["search_wall_ms"]:.2f}',"Descriptive"],
        ["STaR vs FSPC actual trials",primary["n"],primary["parents"],
         f'{star["unique_trials"]:.2f} / {pool["holdout","FSPC"]["unique_trials"]:.2f}',"Descriptive"]],
        "Mandatory main-text disclosure, even when full SLS and FSPC exhibits are supplementary. 95% parent-cluster intervals. "+SAME_CAP+" "+TIME,
        "data/summary.json: paired, pool","holdout")
    add("S01_complete_benchmark",["Cohort","Method","R (%)","LB / n","Completion","Trials","Draws","Wall ms"],[
        [LABEL[cohort],row["method"],pct(row["mean_R"]),f'{row["lower_bound_attained"]}/{row["n"]}',dec(row["full_completion_time"]),
         dec(row["unique_trials"]),number(row["search_scenarios"]),dec(row["search_wall_ms"])] for cohort in COHORTS
        for row in summary["pool"] if row["cohort"]==cohort],"All ten methods under c64. Combined timing not reported. "+EXPLORATORY,
        "data/summary.json: pool","all cohorts")
    add("S02_all_instances",["Parent","V","Split","n","CON (%)","MWR (%)","QBR (%)","STaR (%)"],[
        [row["parent"],row["variant"],{"development":"Dev.","holdout":"Holdout"}[row["partition"]],row["exposed"],
         *[pct(next(item["mean_R"] for item in summary["instance"] if item["parent"]==row["parent"]
                    and item["variant"]==row["variant"] and item["method"]==method)) for method in MAIN]]
        for row in population],"One row per source instance, including empty exposure. NA is not zero. "
        "The long-format instance CSV covers all ten methods, with counters, uncertainty, time, and runtime cohort.",
        "data/instance_results.csv","all 120 instances")
    add("S03_archived_profiles",["Profile","Method","Plan cap","Draw cap","n","R (%)","LB","Draws","Wall ms"],[
        [*cell(row,"profile","method","unique_plan_cap","scenario_cap","n"),pct(row["mean_R"]),row["lower_bound_attained"],
         number(row["search_scenarios"]),dec(row["search_wall_ms"])]
        for row in summary["archived"]["budget"] if row["method"] in ("SLS","FSPC","STaR")],
        "Original holdout profiles only. Different caps are not a single monotone sweep. Seed 2 reuses the same parents. "+PROFILE_NOTE,
        "data/summary.json: archived.budget","holdout original profiles")
    add("S04_component_paired",["Cohort","Variant","Pairs","dR (pp)","dLB (pp)","dCompletion","dDraws"],[
        [LABEL[cohort],method,paired[cohort,method,"reliability"]["n"],
         *effects(cohort,method,(("reliability",100),("attained",100),("full_completion",1),("search_scenarios",1)))]
        for cohort in COHORTS for method in ABL[1:]],
        "Full STaR minus ablation; unadjusted parent-cluster intervals, all exploratory. Additional paired plans/CPU/elapsed are in paired_effects.csv when comparable.",
        "data/summary.json: paired","all cohorts")
    add("S05_work_distributions",["Profile","Method","P25 plans","Median","P75 plans","At plan cap","At draw cap","No limit"],[
        [*cell(row,"profile","method"),*[number(row[key]) for key in ("trial_q1","trial_median","trial_q3")],
         *cell(row,"reached_plan_cap","reached_scenario_cap","no_limit_logged")]
        for row in summary["archived"]["work"] if row["method"] in ("SLS","FSPC","STaR")],
        "Archived consumed trials and counter-derived limits. Under c64, unhit limits are consistent with neighborhood exhaustion; "
        "they are not explicit termination labels. Under scenario caps an affordable remainder can be too small for the next batch. "+SAME_CAP,
        "data/summary.json: archived.work","holdout original profiles")
    add("S06_failures",["Cohort","Family","V","n","LB","Point only","Customer","Depot","Joint"],[
        [LABEL[row["cohort"]],*cell(row,"family","variant","n","attained","point_only","customer_only","depot_only","joint")]
        for row in summary["failures"] if row["method"]=="STaR" and row["cohort"] in ("holdout","all120")],
        "Predominant route-level failure classifications. Point-only: estimate >=0.95 but one-sided lower bound <0.95. "
        "The failure-mode data CSV also gives individual scenario counts and two-sided target straddling.",
        "data/failure_modes.csv","holdout + all120")
    add("S07_robustness",["Stress","Method","n","R (%)","LB","Completion"],[
        [*cell(row,"stress","method","n"),pct(row["mean_R"]),row["lower_bound_attained"],dec(row["full_completion"])]
        for row in summary["archived"]["robustness"]],"Original saved holdout fixed-plan synthetic stresses only, no reoptimization.",
        "data/summary.json: archived.robustness","holdout")
    add("S08_topology",["Stratum","n","Mean dR (pp)","Pooled part (pp)","dCompletion","dEnergy","dVisits"],[
        [*cell(row,"comparison_stratum","n"),pct(row["mean_delta_R"]),pct(row["contribution_to_overall_delta_R"]),
         *[dec(row[key]) for key in ("mean_delta_completion","mean_delta_energy","mean_delta_visits")]]
        for row in summary["archived"]["mechanism"]],"Observed ordered station-gap strata from STaR and FSPC selected plans. "
        "Post-selection contributions are additive arithmetically, not causal. Native time and energy units.",
        "data/summary.json: archived.mechanism","holdout")
    add("S09_registered_route",["Method","Stop","Node","Kind","Service","Depart","Energy","Deadline"],[
        [*cell(row,"method","stop","node","kind"),*[dec(row[key]) for key in (
            "zero_wait_service","zero_wait_departure","charged_energy","deadline")]]
        for row in summary["case_events"] if row["kind"]!="customer"],
        "Registered first eligible R2-A route; exact customer rows are retained in data/registered_route_events.csv. "
        "Station deadlines were not enforced. FSPC/STaR overlap is real.","data/registered_route_events.csv","holdout")
    add("S10_directions",["Cohort","Control","Metric","Pairs","Better","Tied","Worse"],[
        [LABEL[row["cohort"]],row["comparison"],{"reliability":"Reliability","full_completion":"Completion"}[row["metric"]],
         *cell(row,"n","better","ties","worse")]
        for row in summary["directions"] if row["cohort"] in ("all120","holdout")],
        "Observed STaR direction over complete pairs; identical success counts tie, completion tolerance 1e-8. Observed, not true per-route dominance.",
        "data/summary.json: directions","holdout + all120")
    add("S11_work_and_common_attainment",["Cohort","Control","Metric","n","STaR diff. [95% CI]"],[
        [{"holdout":"Holdout","development":"Dev.","all120":"All 120"}[row["cohort"]],row["comparison"],
         {"completion_common_attained":"Completion, joint LB","candidate_evaluations":"Plan trials","wall_ms":"Wall ms","cpu_ms":"CPU ms"}[row["metric"]],
         row["n"],effect_label(row)]
        for row in summary["paired"] if row["metric"] in ("completion_common_attained","candidate_evaluations","wall_ms","cpu_ms")
        and (row["comparison"] in ("SLS","FSPC") or row["comparison"] in ABL[1:])],
        "Unadjusted pointwise intervals. Common attainment includes only both-LB-attaining pairs. Cross archive/new and pooled runtime inference omitted.",
        "data/paired_effects.csv","all cohorts")
    add("S12_station_attributes",["Station CSV SHA-256 prefix","Problems","Holdout","Development"],[
        [row["sha256"][:16],*cell(row,"problems","holdout","development")] for row in summary["archived"]["station_tables"]],
        "Four byte-distinct contents, reused across partitions; not unseen station networks.","data/summary.json: archived.station_tables","dataset")
    parents=[row for row in summary["archived"]["parent_effects"] if row["metric"]=="reliability"]
    by_parent={(row["parent"],row["competitor"]):row for row in parents}
    add("S13_holdout_parents",["Parent","Family","n","dR vs FSPC (pp)","dR vs SLS (pp)"],[
        [*cell(row,"parent","family","paired_routes"),pct(row["mean_difference"]),
         pct(by_parent[row["parent"],"SLS"]["mean_difference"])] for row in parents if row["competitor"]=="FSPC"],
        "All 48 original parent means retain sibling A/B and routes together. Descriptive effects; only pooled registered FSPC reliability is confirmatory.",
        "data/summary.json: archived.parent_effects","holdout")
    for name,key in (("paired_effects","paired"),("failure_modes","failures"),("family_methods","family"),
                     ("work_by_cohort","work"),("archived_candidates","archived_candidates")):
        export_records(out/"data"/f"{name}.csv",summary[key])
    return index


def build(out,summary):
    source_map=file_sha(out/"manifests/source_map.json")
    figures_index=figures(summary,out,source_map)
    tables_index=tables(summary,out)
    write_json(out/"data/exhibits.json",{"figures":figures_index,"tables":tables_index})
    print(f"Built {len(figures_index)} PNGs and {len(tables_index)} table bundles",flush=True)


def validate(root,out):
    check_unchanged(root,get_protocol(root,out))
    source=read_json(out/"manifests/source_map.json")
    require(all(file_sha(out/name)==expected for name,expected in source["fresh"].items()),"Changed new raw bytes")
    exhibits=read_json(out/"data/exhibits.json")
    checks={}
    for figure in exhibits["figures"]:
        path=out/figure["filename"]
        meta=read_json(path.with_suffix(".json"))
        require(meta["summary_sha256"]==file_sha(out/"data/summary.json"),"Stale graphics source")
        checks[figure["filename"]]=png_audit(path,meta)
    for table in exhibits["tables"]:
        path=out/table["filename"]
        data=read_json(out/"data/table_rows"/(path.stem+".json"))
        with path.with_suffix(".csv").open(newline="",encoding="utf-8") as stream:
            import csv
            require(list(csv.reader(stream))==[data["columns"],*data["rows"]],"CSV discrepancy")
        require(path.read_text(encoding="utf-8")==tex_table(data["columns"],data["rows"])
                and path.with_suffix(".md").read_text(encoding="utf-8")==markdown(data["columns"],data["rows"]),"TeX/MD discrepancy")
    require(len(checks)==15 and len(exhibits["tables"])==20,"Incomplete deliverable set")
    write_json(out/"audit/formats.json",{"figures":checks,"tables":len(exhibits["tables"]),"status":"PASS"})
    return exhibits


def package(root,out,summary):
    exhibits=validate(root,out)
    protocol=get_protocol(root,out)
    hand=out/"handoff"
    hand.mkdir(exist_ok=True)
    mapping=protocol["policy"]["methods"]
    glossary=[[key,*value] for key,value in mapping.items()]
    headers=["Frozen/internal key","Acronym","Meaning"]
    csv_export(hand/"METHOD_GLOSSARY.csv",headers,glossary)
    (hand/"METHOD_GLOSSARY.md").write_text("# Method dictionary\n\n"+markdown(headers,glossary)+
        "\nSLS and FSPC are project-implemented benchmarks, not claimed reproductions of published algorithms. "
        "STaR-NPC removes amount-only moves and uses full charging for new topology moves; it starts from the original plan. "
        "STaR-NAS still computes marginal risks to rank moves; STaR-NPP changes search prefixing only, not validation.\n",encoding="utf-8")
    captions=["# Figure captions",""]; notes=["# Table notes","",
        "Use booktabs, graphicx and longtable. Long tables belong in a one-column appendix. "
        "R = mean estimated reliability; LB = route achieves one-sided 95% Wilson lower limit >=0.95. "
        "Point estimates and target straddling from two-sided Wilson intervals are separate. "
        "All completion data are unconditional full depot-return (native units); NA means no eligible routes or pooled timing intentionally omitted.",""]
    entries=[]
    for figure in exhibits["figures"]:
        name=figure["filename"]
        captions.extend([f"## {Path(name).stem}",figure["caption"],""])
        entries.append([name,figure["cohort"],figure["profile"],figure["source"],figure["summary_sha256"],figure["caption"]])
    for table in exhibits["tables"]:
        name=table["filename"]
        notes.extend([f"## {Path(name).stem}",table["caption"],""])
        for ext in (".tex",".csv",".md"):
            entries.append([str(Path(name).with_suffix(ext)).replace("\\","/"),table["cohort"],"c64 unless archived",
                            table["source"],table["source_sha256"],table["caption"]])
    headers=["Exhibit","Cohort","Profile","Source","Data hash","Caption or notes"]
    csv_export(hand/"EXHIBIT_INDEX.csv",headers,entries)
    (hand/"EXHIBIT_INDEX.md").write_text("# Exhibit index\n\n"+markdown(headers,entries),encoding="utf-8")
    (hand/"FIGURE_CAPTIONS.md").write_text("\n".join(captions),encoding="utf-8")
    (hand/"TABLE_NOTES.md").write_text("\n".join(notes),encoding="utf-8")
    pair={(row["cohort"],row["comparison"],row["metric"]):row for row in summary["paired"]}
    pool={(row["cohort"],row["method"]):row for row in summary["pool"]}
    p=pair["holdout","FSPC","reliability"]
    star,sls=(pool["holdout",m] for m in ("STaR","SLS"))
    saved_pct=100*(1-star["search_scenarios"]/sls["search_scenarios"])
    claims=[
        ["STaR minus FSPC reliability","T07/S01",effect_label(p,100),"pp",p["n"],"Original confirmatory interval",
         "Only original holdout, route-weighted; matched caps not actual work or a global quantity optimum."],
        ["STaR minus SLS reliability","T07/S03",effect_label(pair["holdout","SLS","reliability"],100),"pp",p["n"],"Exploratory interval",
         "No general or simultaneous superiority."],
        ["STaR draws and wall against SLS","T07/S02/S03",
         f'{saved_pct:.2f}% fewer draws; {star["search_wall_ms"]:.2f} vs {sls["search_wall_ms"]:.2f} ms',
         "SLS-denominator draw reduction, elapsed ms",p["n"],"Descriptive","No wall-clock speedup."],
        ["All-120 results cover development too","T01/T02",pool["all120","STaR"]["n"],"exposed routes",120,"Descriptive",
         "Do not describe all 120 as held out or pool wall across runs."],
        ["Station attribute content reuse","S12",len(summary["archived"]["station_tables"]),"distinct CSVs",120,"Dataset audit",
         "No new station-network generalization."],
    ]
    for method in ABL[1:]:
        row=pair["all120",method,"reliability"]
        claims.append([f"Full STaR minus {method} reliability","T04/S04",effect_label(row,100),"pp",row["n"],
                       "Pooled exploratory, pointwise","No component guarantees, causal inference or adjusted significance."])
    claim_headers=["Claim","Exhibit","Estimate [95% CI] or measurement","Unit","n","Class","Do not claim"]
    csv_export(hand/"CLAIMS_MATRIX.csv",claim_headers,claims)
    (hand/"CLAIMS_MATRIX.md").write_text("# Claims matrix\n\n"+markdown(claim_headers,claims),encoding="utf-8")
    citations=[]
    for row in summary["pool"]:
        citations.extend([[row["cohort"],"c64",row["method"],"Mean independent R",pct(row["mean_R"]),"%",row["n"],
                           "data/summary.json: pool","2 decimals","Descriptive"],
                          [row["cohort"],"c64",row["method"],"Attained",row["lower_bound_attained"],"routes",row["n"],
                           "data/summary.json: pool","integer","Descriptive"],
                          [row["cohort"],"c64",row["method"],"Unconditional completion",dec(row["full_completion_time"]),"native units",
                           row["n"],"data/summary.json: pool","2 decimals","Descriptive"],
                          [row["cohort"],"c64",row["method"],"Search draws",number(row["search_scenarios"]),"draws",
                           row["n"],"data/summary.json: pool","nearest integer","Descriptive"]])
    citations.insert(0,["holdout","c64","STaR – FSPC","Paired route-weighted reliability",effect_label(p,100),"pp",p["n"],
                        "T07; data/paired_effects.csv","2 decimals","Sole confirmatory contrast"])
    csv_export(hand/"NUMBERS_TO_CITE.csv",
               ["Cohort","Profile","Method(s)","Quantity/estimand","Value [95% interval]","Unit","n","Source","Rounding","Status"],citations)
    (hand/"README_RESULTS_PACKAGE.md").write_text(f"""# Final STaR-EVRP results handoff

This Phase 5 package is the authoritative set of publication exhibits. It does not replace the earlier raw archives, tags or preregistration.

**Mandatory disclosure:** the sole confirmatory comparison is the original holdout STaR minus FSPC reliability effect, {effect_label(p,100)} percentage points across {p['n']:,} exposed route pairs from {p['parents']} parents. Include T07 or disclose it in the main text. STaR uses {saved_pct:.2f}% fewer draws than SLS but takes {star['search_wall_ms']:.2f} vs {sls['search_wall_ms']:.2f} ms. Do not hide either comparator when streamlining the main baseline presentation.

Read the glossary, caption notes and claim matrix. Summary and instance results use c64 and 10,000-draw validation, with distinct development and holdout labels. The 120-instance results include tuning data and are descriptive. Full SLS and FSPC results, frozen secondary budgets and saved robustness stress outcomes are supplementary.

## Files for the writer

- `data/instance_results.csv`: every instance × all ten methods, with NA when exposure is zero and metrics at full precision.
- `data/population_by_instance.csv`: source fleet and original exposure accounting.
- `data/paired_effects.csv`, `data/family_ablation.csv`, `data/failure_modes.csv`, `data/work_by_cohort.csv`: complete analysis tables.
- `data/registered_route_events.csv`: the registered route's exact saved ordered events. `data/paired_routes.csv` and `data/route_results.csv` are in the repository with complete pairs and per-route rows.
- Tables in CSV, TeX and Markdown; figures in 400-DPI PNG with exact-value sidecars. See EXHIBIT_INDEX. Use the specified physical width.

## Limits

Synthetic independent waits and four shared station CSV contents; fixed offline CON customer orders; no real queue inference, fleet guarantee, or global routing optimality. The one-sided Wilson classification is pointwise. All intervals other than the original primary contrast are descriptive/exploratory and unadjusted. Topology strata are post-selection, not causal. {SAME_CAP} {TIME}

Reproduce using `{SCRIPT} all` with the recorded thread settings and production output, or rebuild derived outputs with `analyze` and `build-exhibits` against existing audited batches. This package does not contain a manuscript.
""",encoding="utf-8")
    (hand/"LIMITATIONS_FOR_WRITER.md").write_text("# Limits for results interpretation\n\n"+
        "\n".join(f"- {item}" for item in (
            EXPLORATORY,SAME_CAP,TIME,"All 120 includes 24 development problems; it is not held-out confirmation.",
            "All four distinct station CSV contents occur in both partitions. Synthetic waits are not calibrated queues.",
            "Fixed offline customer orders and vehicle assignments; individual route reliability is not fleet reliability.",
            "Pointwise Wilson classifications are not simultaneous guarantees or exact model feasibility.",
            "Observed topology contributions are post-selection, not an intervention.",
            "NPC changes the available amounts and new topology allocations as a bundle. No ablation establishes optimality.",
        ))+"\n",encoding="utf-8")
    manifest={"frozen_executable":protocol["frozen_commit"],"producer_base_head":protocol["head"],
              "analysis_base_head":git(root,"rev-parse","HEAD").decode().strip(),
              "command":SCRIPT+" all","runtime":summary["runtime_environment"],"counts":summary["counts"],
              "source_map":"manifests/source_map.json","software_source_sha256":{
                  path.relative_to(root).as_posix():file_sha(path) for path in (
                    *sorted((root/"src/star_evrp").glob("phase5_*.py")),root/"scripts/run_phase5.py",
                    root/"scripts/finalize_phase5.py",*sorted((root/"tests").glob("test_phase5_*.py")))},
              "quality_gate":"audit/final_gate.json",
              "files":{path.relative_to(out).as_posix():file_sha(path) for path in sorted(out.rglob("*"))
                       if path.is_file() and path.name not in (
                           "MANIFEST.json","STaR_EVRP_FINAL_RESULTS_HANDOFF.zip","final_gate.json")}}
    write_json(hand/"MANIFEST.json",manifest)
    archive_path=out/"STaR_EVRP_FINAL_RESULTS_HANDOFF.zip"
    data_files=("instance_results.csv","population_by_instance.csv","paired_effects.csv","family_ablation.csv",
                "failure_modes.csv","work_by_cohort.csv","registered_route_events.csv")
    keep=[path for path in out.rglob("*") if path.is_file() and (
        path.relative_to(out).parts[0] in ("handoff","figures","tables","manifests") or
        path.relative_to(out).parts==("data",path.name) and path.name in data_files)]
    with ZipFile(archive_path,"w") as archive:
        for path in sorted(keep):
            archive.writestr(ZipInfo(path.relative_to(out).as_posix(),date_time=(2020,1,1,0,0,0)),
                            path.read_bytes(),compress_type=ZIP_DEFLATED)
    with ZipFile(archive_path) as archive:
        require(archive.testzip() is None and len(archive.namelist())==len(keep),"Handoff archive failed")
        require(all(archive.read(path.relative_to(out).as_posix())==path.read_bytes() for path in keep),"ZIP member checksum differs")
    print(f"Handoff ZIP: {len(keep)} verified members",flush=True)
    return len(keep),file_sha(archive_path)


def action(root,out,action_name):
    if action_name in ("all","analyze"):
        summary=analyze(root,out)
    else:
        summary=read_json(out/"data/summary.json")
    if action_name in ("all","build-exhibits"):
        build(out,summary)
    if action_name in ("all","audit"):
        validate(root,out)
        compiled=tex_probe(out)
        print(compiled,flush=True)
        require(compiled["status"]=="pass","LaTeX bundle did not compile cleanly")
    if action_name in ("all","package"):
        package(root,out,summary)
