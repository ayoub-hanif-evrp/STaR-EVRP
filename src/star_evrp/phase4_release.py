"""Table exports, audit evidence and writing-agent handoff for Phase 4."""

from __future__ import annotations

import csv
import json
import platform
import shutil
import struct
import subprocess
import zlib
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from PIL import Image

from star_evrp.phase4_exhibits import figures
from star_evrp.phase4_results import (VERSION, audit, file_sha, read_json, require, unchanged_scope, write_json)

COMMAND = "python -B scripts/run_phase4_results.py all"
METHOD_NOTE = "Five-second wall guard is cooperative; archived elapsed and CPU times reflect six workers."
STRATA_NOTE = "Saved-plan topology strata are descriptive and post-selection, not separate interventions."
B4_NOTE = "Equal caps, unequal consumed trials. B4 adjusts quantities only and is not a quantity oracle."
MC_NOTE = "Zero optimizer MC draws do not imply zero work. Validation is excluded from search time/draw counts."
LATEX = str.maketrans({"\\": r"\textbackslash{}", "_": r"\_", "%":r"\%", "&":r"\&", "#":r"\#",
                      "$":r"\$", "{":r"\{", "}":r"\}", "~":r"\textasciitilde{}",
                      "^":r"\textasciicircum{}", "−":"-", "≥":r"$\geq$", "–":"--"})


def csv_export(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def markdown(columns, rows):
    escaped = [[str(value).replace("|", r"\|").replace("\n"," ") for value in row] for row in (columns, *rows)]
    return "\n".join("| " + " | ".join(row) + " |" for row in
                     (escaped[0], ["---"]*len(columns), *escaped[1:]))+"\n"


def tex_table(headers, rows):
    long = len(rows) > 30
    environment = "longtable" if long else "tabular"
    orientation = "l" + "r"*(len(headers)-1)
    lines = [r"\begingroup", r"\small", r"\setlength{\tabcolsep}{3pt}"]
    if not long:
        lines.extend([r"\begin{center}", r"\resizebox{\linewidth}{!}{%"])
    lines.extend([rf"\begin{{{environment}}}{{@{{}}{orientation}@{{}}}}", r"\toprule"])
    lines.append(" & ".join(str(value).translate(LATEX) for value in headers)+r" \\")
    lines.append(r"\midrule")
    if long:
        lines.append(r"\endhead")
    lines.extend(" & ".join(str(value).translate(LATEX) for value in row)+r" \\" for row in rows)
    lines.extend([r"\bottomrule", rf"\end{{{environment}}}"])
    if not long:
        lines.extend(["}", r"\end{center}"])
    lines.append(r"\endgroup")
    return "\n".join(lines)+"\n"


def tables(study, out):
    summary = study.summary
    exhibit = []
    total = summary["population"][-1]
    n = total["exposed"]

    def add(folder, name, columns, rows, source, caption, profile="c64", denominator=n):
        rows = [[str(value) for value in row] for row in rows]
        where = out / "tables" / folder / name
        csv_export(where.with_suffix(".csv"), columns, rows)
        where.with_suffix(".md").write_text(markdown(columns,rows),encoding="utf-8")
        where.with_suffix(".tex").write_text(tex_table(columns,rows),encoding="utf-8")
        data = out / "data" / "table_rows" / f"{name}.json"
        write_json(data, {"columns":columns,"rows":rows,"source":source})
        exhibit.append(dict(id=name, kind="table", folder=folder, filename=where.with_suffix(".tex").relative_to(out).as_posix(),
                            profile=profile,n=denominator,message=caption.split(". ")[0]+".",source=source,
                            caption=caption,source_hash=file_sha(data)))

    add("main","T01_population",["Population","A","B","Total"], [
        [label,*[sum(row[field] for row in summary["population"] if row["variant"]==variant) for variant in ("A","B")],
         total[field]] for label,field in (
            ("Holdout problems","instances"), ("CON routes","all_routes"), ("Initially exposed","exposed"),
            ("No station visit","zero_charge"), ("B0 point below 0.95","below_target_B0"),
            ("B0 lower-bound nonattainment","B0_lower_bound_nonattainment"))] +
        [["Holdout parents",*[len(study.parents)]*3],["Distinct station CSVs",*[len(study.station_tables)]*3]],
        "data/summary.json: population, station_tables",
        "The same held-out parents contribute both variants. Initially exposed routes form the main denominator; point-estimate failure and lower-bound nonattainment are different.",
        denominator=total["all_routes"])
    add("main","T02_primary_methods",["Method","Mean R (%)","LB count / n","LB (%)","Completion","MC draws","Wall ms"],[
        [row["method"],f'{100*row["mean_R"]:.2f}',f'{row["lower_bound_attained"]}/{row["n"]}',
         f'{100*row["lower_bound_attained"]/row["n"]:.2f}',f'{row["full_completion_time"]:.2f}',
         f'{row["search_scenarios"]:.0f}',f'{row["search_wall_ms"]:.2f}'] for row in summary["overall"]],
        "data/summary.json: overall","Matched c64 methods. R and attainment: higher is better; full completion, elapsed time and work are distinct; completion uses native time units. "+MC_NOTE)
    effects = {(row["profile"],row["competitor"],row["metric"]):row for row in summary["paired"]}
    fmt = lambda row,scale,precision: f'{row["estimate"]*scale:+.{precision}f} [{row["lower95"]*scale:+.{precision}f}, {row["upper95"]*scale:+.{precision}f}]'
    add("main","T03_paired_contrasts",["Control","Endpoint (unit)","Pairs","Difference [95% CI]","Class"],[
        [control,label,effect["n"],fmt(effect,scale,precision),
         "Primary" if effect["status"]=="confirmatory" else "Exploratory"]
        for control in ("B4","B3","STaR_no_partial") for metric,label,scale,precision in (
            ("reliability","R (pp)",100,2),("attained","LB attainment (pp)",100,2),
            ("full_completion","Completion (native)",1,2),("search_scenarios","Search draws",1,0),("wall_ms","Wall (ms)",1,2))
        if control!="STaR_no_partial" or metric in ("reliability","attained","full_completion")
        for effect in (effects["c64",control,metric],)],"data/summary.json: paired",
        "Signed STaR minus control; positive favors reliability, negative favors time/work. Family-stratified parent-cluster intervals; only STaR–B4 c64 reliability is confirmatory.")
    primary=effects["c64","B4","reliability"]
    add("main","T04_frozen_budgets",["Profile","Caps (plans/draws)","Method","R (%)","LB count","Draws","Wall ms"],[
        [row["profile"],f'{row["unique_plan_cap"]}/{row["scenario_cap"]}',row["method"],f'{100*row["mean_R"]:.2f}',
         row["lower_bound_attained"],f'{row["search_scenarios"]:.0f}',f'{row["search_wall_ms"]:.2f}']
        for row in summary["budget"] if row["method"] in ("B3","B4","STaR")],"data/summary.json: budget",
        "Secondary frozen profiles are discrete comparisons, not a monotone sweep. Seed 2 reuses the benchmark parents. "+METHOD_NOTE,
        profile="all profiles")
    index={(row["family"],row["variant"],row["method"]):row for row in summary["family_variant"]}
    add("main","T05_family_attainment",["Family","Variant","n","B0 LB","B3 LB","B4 LB","STaR LB","STaR not LB"],[
        [row["family"],row["variant"],row["exposed"],*[index[row["family"],row["variant"],method]["lower_bound_attained"]
                                                     for method in ("B0","B3","B4","STaR")],
         row["exposed"]-index[row["family"],row["variant"],"STaR"]["lower_bound_attained"]]
        for row in summary["population"][:-1]],"data/summary.json: family_variant, population",
        "Family and A/B strata, with different route counts. LB = one-sided lower-bound attainment; all strata are descriptive.")
    add("main","T06_mechanism",["Comparison","n","Mean dR (pp)","Pooled part (pp)","dCompletion","dEnergy","dVisits"],[
        [row["comparison_stratum"],row["n"],f'{100*row["mean_delta_R"]:+.2f}',
         f'{100*row["contribution_to_overall_delta_R"]:+.2f}',f'{row["mean_delta_completion"]:+.2f}',
         f'{row["mean_delta_energy"]:+.2f}',f'{row["mean_delta_visits"]:+.2f}'] for row in summary["mechanism"]]+[
        ["STaR vs no partial",n,f'{100*effects["c64","STaR_no_partial","reliability"]["estimate"]:+.2f}',
         "",f'{effects["c64","STaR_no_partial","full_completion"]["estimate"]:+.2f}',"",""]],
        "data/summary.json: mechanism, paired","Topology strata compare STaR with B4; the ablation compares a different method. "+STRATA_NOTE)
    add("main","T07_robustness",["Stress","Method","n","R (%)","LB count","Completion"],[
        [row["stress"],row["method"],row["n"],f'{100*row["mean_R"]:.2f}',row["lower_bound_attained"],f'{row["full_completion"]:.2f}']
        for row in summary["robustness"]],"data/summary.json: robustness",
        "Synthetic fixed-plan robustness; no reoptimization. Scale125 multiplies all waits; sigma125 multiplies log-scale spread; copula035 changes dependence with preserved marginals.")
    add("supplementary","S01_primary_estimands",["Weighting","Pairs","Parents","Probability diff.","dR (pp)","95% CI (pp)"],[
        ["Route weighted",primary["n"],primary["parents"],f'{primary["estimate"]:.7f}',f'{100*primary["estimate"]:.3f}',
         f'[{100*primary["lower95"]:.3f}, {100*primary["upper95"]:.3f}]'],
        ["Parent equal",primary["n"],primary["parents"],f'{primary["parent_equal_estimate"]:.7f}',f'{100*primary["parent_equal_estimate"]:.3f}',
         f'[{100*primary["parent_equal_lower95"]:.3f}, {100*primary["parent_equal_upper95"]:.3f}]']],
        "data/summary.json: paired",
        "Exact primary estimand and parent-equal sensitivity; family-stratified parent-cluster percentile interval. Only the route-weighted effect is confirmatory.")
    add("supplementary","S02_parent_effects",["Parent","Family","n","dR B4 (pp)","dR B3 (pp)"], [
        [a["parent"],a["family"],a["paired_routes"],f'{100*a["mean_difference"]:+.3f}',f'{100*b["mean_difference"]:+.3f}']
        for a,b in zip(*( [row for row in summary["parent_effects"] if row["competitor"]==m and row["metric"]=="reliability"]
                         for m in ("B4","B3")),strict=True)],"data/summary.json: parent_effects",
        "Each parent mean pools A/B routes; these descriptive points are not independently tested effects.",denominator=48)
    add("supplementary","S03_family_variant",["Family","V","Method","n","R (%)","Point","LB","Straddle"],[
        [row["family"],row["variant"],row["method"],row["n"],f'{100*row["mean_R"]:.2f}',row["point_at_target"],
         row["lower_bound_attained"],row["two_sided_CI_contains_target"]] for row in summary["family_variant"]],
        "data/summary.json: family_variant","Full family/variant method counts; the two-sided straddle category can overlap both attainment categories.")
    add("supplementary","S04_candidate_work",["Method","Mean","Min","Q1","Median","Q3","Max","At 64","No limit hit"],[
        [row["method"],f'{row["mean_trials"]:.2f}',*[f'{row["trial_"+key]:g}' for key in ("min","q1","median","q3","max")],
         row["reached_plan_cap"],row["no_limit_logged"]] for row in summary["work"] if row["profile"]=="c64"],
        "data/summary.json: work","One trial counts the initial plan; generated proposals and cache hits are not additional trials. At c64, no-limit stops are consistent with exhaustion of the implemented neighborhood; no explicit stop reason was stored. "+B4_NOTE)
    add("supplementary","S05_runtime_accounting",["Method","Wall ms","CPU ms","Build ms","Check ms","Screen ms","Score ms","Gen.","Checks"],[
        [row["method"],f'{row["search_wall_ms"]:.2f}',f'{row["search_cpu_ms"]:.2f}',
         *[f'{1000*row["mean_"+key+"_seconds"]:.2f}' for key in ("generation","deterministic","screening","simulation")],
         f'{row["mean_generated"]:.1f}', f'{row["mean_deterministic_checks"]:.1f}'] for row in summary["budget"] if row["profile"]=="c64"],
        "data/summary.json: budget","Mean archived work per route. Score includes deterministic surrogate evaluation for B1/B2; component timers need not sum to total elapsed. "+METHOD_NOTE)
    add("supplementary","S06_nonattainment",["Family","V","n","LB","Point only","Cust. mode","Depot mode","Joint mode"],[
        [row[key] for key in ("family","variant","n","attained","point_only","customer_only","depot_only","joint")]
        for row in summary["failures"]]+[["All","A+B",*[sum(row[key] for row in summary["failures"])
                            for key in ("n","attained","point_only","customer_only","depot_only","joint")]]],
        "data/summary.json: failures","STaR route classifications. Point-only indicates estimate at least 0.95 but Wilson nonattainment. Other nonattainments use the most common observed failure mode per route; scenario-count ties follow customer, depot, joint order.")
    add("supplementary","S07_uncertainty_ties",["Method","n","LB","Point only","Point below","Wilson straddle"],[
        [row["method"],row["n"],row["lower_bound_attained"],row["point_at_target"]-row["lower_bound_attained"],
         row["n"]-row["point_at_target"],row["two_sided_CI_contains_target"]] for row in summary["overall"]],
        "data/summary.json: overall","One-sided lower bounds do not give a joint guarantee. Two-sided 95% straddle counts are a separate, nonpartitioning statistic.")
    add("supplementary","S08_paired_directions",["Control","Quantity","Pairs","STaR better","Tied","STaR worse"],[
        list(row.values()) for row in summary["ties"]],"data/summary.json: ties",
        "Post-hoc directions of observed estimates, not statements about individual true superiority. Reliability ties mean equal successes out of 10,000; completion ties are absolute difference at most 1e-8 native time units.")
    add("supplementary","S09_common_and_work",["Control","Metric","n","Difference [95% CI]"],[
        [control,desc,row["n"],fmt(row,1,2)] for control in ("B4","B3") for metric,desc in (
            ("full_completion_common_attained","Completion on common attainers"),("relative_full_completion_percent","Route-relative completion (%)"),
            ("candidate_evaluations","Distinct plans"),("cpu_ms","Process CPU ms"))
        for row in (effects["c64",control,metric],)],"data/summary.json: paired",
        "Exploratory pair contrasts. Route-relative completion uses positive comparator completion per route; common attainment conditions on both selected plans.")
    negative=sorted(summary["negative"],key=lambda row:(row["reason"],row["parent"],row["variant"],row["route"]))
    representative=[next(row for row in negative if row["reason"]==reason) for reason in sorted({r["reason"] for r in negative})]
    add("supplementary","S10_negative_examples",["Parent","V","Route","Observed mode","R (%)","LB (%)","Cust.","Depot","Both"],[
        [row["parent"],row["variant"],row["route"],row["reason"],f'{100*row["R"]:.2f}',f'{100*row["wilson_low"]:.2f}',
         row["customer_fail"],row["depot_fail"],row["joint_fail"]] for row in representative],
        "data/summary.json: negative","Post-hoc examples: lexicographically first nonattaining route per observed mode. Counts are overlapping scenario failures over 10,000 draws, not additional routes.",denominator=len(representative))
    details=[row for row in summary["case_routes"] if row["kind"] in ("station","depot")]
    add("supplementary","S11_registered_route_stops",["Method","Stop","Node","Type","Service","Depart","Energy","Deadline"],[
        [row["method"],row["stop"],row["node"],row["kind"],f'{row["zero_wait_service"]:.3f}',f'{row["zero_wait_departure"]:.3f}',
         f'{row["charged_energy"]:.6f}',f'{row["deadline"]:.1f}'] for row in details],
        "data/summary.json: case_routes","Registered R2_10_2/A/0: station and depot event rows in saved stop order. Zero-wait time and energy are native units; station deadlines shown but not enforced. The full exact event list is in data/registered_route_events.csv.",denominator=1)
    add("supplementary","S12_station_content",["Content ID (SHA-256 prefix)","Total","Holdout","Development"],[
        [row["sha256"][:16],row["problems"],row["holdout"],row["development"]] for row in summary["station_tables"]],
        "data/summary.json: station_tables","Byte-identical station-attribute CSVs grouped by full SHA-256. This is not a holdout of unseen station attribute tables.",profile="dataset",denominator=120)
    freeze=study.freeze
    add("supplementary","S13_reproduction",["Item","Recorded value"],[
        ("Freeze tag",freeze["tag"]),("Phase 3 executable",freeze["commit"][:12]),("Python",freeze["python"]),
        ("Operating system",freeze["platform"]),("CPU",freeze["processor"].split(",")[0]),
        ("Logical CPUs",freeze["logical_cpus"]),("Parallel workers",freeze["config"]["workers"]),
        ("Opt scenarios per full plan",freeze["config"]["opt_samples"]),("Validation draws",freeze["config"]["validation_samples"]),
        ("Validation seed",freeze["config"]["validation_seed"]),("Cluster seed",freeze["config"]["statistical_seed"]),
        ("Bootstrap replicates",freeze["config"]["bootstrap_draws"]), *freeze["dependencies"].items()],
        "results/phase3/manifests/freeze.json","Producer environment, not a new Phase 4 benchmark run.",profile="all profiles",denominator=len(study.rows))
    add("supplementary","S14_methods",["Method","Scoring and move set","Search MC"],[
        ("B0","Original CON plan; no search","0"),
        ("B1","Deterministic mean-wait score; topology and quantity edits","0"),
        ("B2","Independent-visit uniform quantile; probability 0.95^(1/K); both edit types","0"),
        ("B3","Iterative first improvement; topology and quantity edits","512/full score"),
        ("B4","First improvement; quantities only, fixed ordered station positions","512/full score"),
        ("STaR","Criticality order, fixed-plan and prefix screens; both edit types","128 prefix, up to 512"),
        ("STaR_no_partial","STaR topology moves with full recharge schedules; no quantity moves","128 prefix, up to 512")],
        "src/star_evrp/competitive_search.py: frozen optimizer","Reviewer-facing method truth table. B2 uses independent lognormal visit quantiles, not medians. "+B4_NOTE+" "+MC_NOTE)
    add("supplementary","S15_stop_limits",["Profile","Method","Plan cap","Draw cap","Wall","Proposal cap","No limit"],[
        [row[key] for key in ("profile","method","plan_cap","scenario_cap","wall_guard","proposal_cap","no_limit_logged")]
        for row in summary["work"] if row["method"]!="B0"], "data/summary.json: work",
        "Recorded-counter categories, not archived termination labels. In s8192 a residual scenario budget can be too small for a full extension even below the exact cap; therefore only c64 supports the narrower neighborhood-exhaustion inference.",
        profile="all profiles")
    return exhibit


def build(study,out):
    write_json(out / "data/summary.json", {key: value for key,value in study.summary.items() if key!="pairs"})
    for name, key in (("paired_routes","pairs"),("registered_route_events","case_routes"),("nonattaining_routes","negative")):
        rows=study.summary[key]
        csv_export(out/"data"/f"{name}.csv",list(rows[0]),[list(row.values()) for row in rows])
    exhibits=figures(study,out)+tables(study,out)
    write_json(out/"data/exhibits.json",exhibits)
    return exhibits


def png_audit(path, sidecar):
    data=path.read_bytes()
    require(data.startswith(b"\x89PNG\r\n\x1a\n"),f"Invalid PNG header: {path.name}")
    cursor, phys, dims = 8, None, None
    while cursor+12<=len(data):
        length, kind=struct.unpack(">I4s",data[cursor:cursor+8])
        piece=data[cursor+8:cursor+8+length]
        check=struct.unpack(">I",data[cursor+8+length:cursor+12+length])[0]
        require(zlib.crc32(kind+piece)==check,f"Bad PNG CRC: {path.name}")
        if kind==b"pHYs":
            phys=struct.unpack(">IIB",piece)
        if kind==b"IHDR":
            dims=struct.unpack(">II",piece[:8])
        if kind in (b"tEXt",b"iTXt"):
            require(b"placeholder" not in piece.lower(),"Placeholder PNG metadata")
        cursor+=12+length
    require(phys==(15748,15748,1) and dims is not None and min(dims)>=950,"PNG DPI or size invalid")
    require(all(abs(pixels/mm*25.4-400)<1 for pixels,mm in zip(dims,sidecar["physical_mm"],strict=True)),"Wrong physical width")
    with Image.open(path) as loaded:
        grayscale=loaded.convert("L")
        lower,_=grayscale.getextrema()
        histogram=grayscale.histogram()
        require(lower<120 and sum(histogram[:242])/sum(histogram)>.013,"Plot appears empty")
    require(sidecar["png_sha256"] == file_sha(path),"PNG mismatched to plotted data")
    return {"width_px":dims[0],"height_px":dims[1],"dpi":400,"mm":sidecar["physical_mm"],"sha256":file_sha(path)}


def validate(out):
    exhibits=read_json(out/"data/exhibits.json")
    evidence={"png":{},"table_formats":{}}
    for item in exhibits:
        path=out/item["filename"]
        if item["kind"]=="figure":
            sidecar=read_json(path.with_suffix(".json"))
            require(file_sha(path.with_suffix(".json"))==item["source_hash"],"Mismatched figure sidecar")
            evidence["png"][item["filename"]]=png_audit(path,sidecar)
        else:
            source=out/"data/table_rows"/f'{item["id"]}.json'
            require(file_sha(source)==item["source_hash"],"Mismatched table source")
            canon=read_json(source)
            columns, rows=canon["columns"],canon["rows"]
            with path.with_suffix(".csv").open(encoding="utf-8",newline="") as handle:
                require(list(csv.reader(handle))==[columns,*rows],"CSV mismatch")
            require(path.read_text(encoding="utf-8")==tex_table(columns,rows),"TeX mismatch")
            require(path.with_suffix(".md").read_text(encoding="utf-8")==markdown(columns,rows),"Markdown mismatch")
            evidence["table_formats"][item["filename"]]=len(rows)
    for category in ("main","supplementary"):
        require({path.relative_to(out).as_posix() for path in (out/"figures"/category).glob("*.png")}
                =={item["filename"] for item in exhibits if item["folder"]==category and item["kind"]=="figure"},"Extra or missing PNG")
    write_json(out/"audit/format_validation.json",evidence)
    return evidence


def tex_probe(out):
    target=out/"logs"/"tex"
    target.mkdir(parents=True,exist_ok=True)
    paths=sorted((out/"tables").glob("*/*.tex"))
    wrapper=target/"check_tables.tex"
    lines=[r"\documentclass[a4paper]{article}",r"\usepackage{booktabs,longtable,graphicx}",r"\begin{document}"]
    lines.extend(r"\input{"+Path("..","..",path.relative_to(out)).as_posix()+r"}\clearpage" for path in paths)
    lines.append(r"\end{document}")
    wrapper.write_text("\n".join(lines)+"\n",encoding="utf-8")
    tectonic=shutil.which("tectonic")
    other=shutil.which("pdflatex") if not tectonic else None
    if not tectonic and not other:
        result={"status":"unavailable","reason":"No local TeX executable found"}
    else:
        command=[tectonic,"--only-cached","--keep-logs",wrapper.name] if tectonic else [
            other,"-interaction=nonstopmode","-halt-on-error",wrapper.name]
        try:
            process=subprocess.run(command,cwd=target,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=90)
            output=process.stdout+process.stderr
            log=target/"check_tables.log"
            if log.exists():
                output+="\n"+log.read_text(encoding="utf-8",errors="replace")
            (target/"compiler.txt").write_text(output,encoding="utf-8")
            success=process.returncode==0 and "Overfull \\hbox" not in output
            result={"status":"pass" if success else "unavailable" if process.returncode!=0 and any(
                indicator in output.lower() for indicator in ("bundle", "cache", "download", "network")) else "fail",
                "returncode":process.returncode,"tables":len(paths),"command":[Path(command[0]).name,*command[1:]]}
            for extension in (".pdf",".aux",".log",".xdv"):
                wrapper.with_suffix(extension).unlink(missing_ok=True)
        except subprocess.TimeoutExpired:
            result={"status":"unavailable","reason":"TeX exceeded timeout"}
    write_json(out/"audit/tex_check.json",result)
    return result


def audit_export(root,out):
    try:
        study=audit(root)
    except (ValueError, FileNotFoundError, KeyError) as problem:
        write_json(out/"audit/audit_summary.json",{"status":"fail","discrepancy":str(problem),"publication_blocked":True})
        raise
    write_json(out/"audit/lineage.json",study.lineage)
    write_json(out/"audit/audit_summary.json",{
        "status":"pass","freeze":study.lineage["freeze_digest"],"reconciled":study.summary["reconciliation"],
        "routes_checked_deterministically":len(study.rows),"stored_holdout_validations_checked":len(study.rows),
        "stress_summaries_checked":study.summary["stored_stress_records_checked"],
        "phase4_optimization_runs":0,"phase4_stochastic_replays":0,"archived_scalar_checks_per_plan_model":5,
        "plans":len(study.plans),"all_routes":study.summary["population"][-1]["all_routes"],
        "parents":len(study.parents),"instances":len(study.cases),"distinct_station_contents":len(study.station_tables),
        "publication_blocked":False,
    })
    return study


def package(root,out):
    evidence=read_json(out/"audit/audit_summary.json")
    require(evidence["status"]=="pass","Cannot package failed audit")
    validate(out)
    lineage=read_json(out/"audit/lineage.json")
    unchanged_scope(root,lineage)
    exhibits=read_json(out/"data/exhibits.json")
    summary=read_json(out/"data/summary.json")
    hand=out/"handoff"
    hand.mkdir(parents=True,exist_ok=True)
    method={row["method"]:row for row in summary["overall"]}
    work={row["method"]:row for row in summary["work"] if row["profile"]=="c64"}
    effect={(row["profile"],row["competitor"],row["metric"]):row for row in summary["paired"]}
    primary=effect["c64","B4","reliability"]
    competitive=effect["c64","B3","reliability"]
    completion=effect["c64","B4","full_completion"]
    total=summary["population"][-1]
    savings=100*(1-method["STaR"]["search_scenarios"]/method["B3"]["search_scenarios"])
    delta_wall=effect["c64","B3","wall_ms"]["estimate"]
    cls=lambda row: f'{100*row["estimate"]:+.2f} pp [{100*row["lower95"]:.2f}, {100*row["upper95"]:.2f}]'
    descriptions = ["# Exhibit index", "Paths are relative to the Phase 4 output directory. Source data are full precision unless a display table is listed.", ""]
    table_index=[]
    captions=["# Standalone figure captions",""]
    notes=["# Table notes", "",
           "Use \\input with booktabs, graphicx and, where needed, longtable. Small fragments resize to the current linewidth. "
           "For two-column manuscripts place longtable supplementary fragments in a one-column appendix. "
           "CSV, TeX and Markdown are derived from the same display cells. The JSON and paired CSV preserve full precision.", "",
           "LB = one-sided 95% Wilson lower limit at least 0.95; R = empirical validation reliability; pp = percentage points; "
           "MC = incremental search Monte Carlo. Conditional completion compares only joint LB-attainers.", ""]
    for item in exhibits:
        files=[item["filename"]]
        if item["kind"]=="table":
            files=[str(Path(item["filename"]).with_suffix(extension)).replace("\\","/") for extension in (".csv",".tex",".md")]
        caption_file="FIGURE_CAPTIONS.md" if item["kind"]=="figure" else "TABLE_NOTES.md"
        into=captions if item["kind"]=="figure" else notes
        into.extend([f'## {item["id"]}',f'File: `{item["filename"]}`. Source: {item["source"]}.',item["caption"],""])
        caveat=(B4_NOTE+" "+METHOD_NOTE if item["profile"] in ("c64","all profiles") else
                "Compared benchmark files may share station attributes.")
        table_index.extend([item["id"],item["kind"],filename,item["message"],item["source"],item["profile"],
                            item["source_hash"],caption_file,item["n"],caveat] for filename in files)
    cols=["Exhibit","Kind","Filename","Scientific message","Tested source","Profile","Source SHA-256","Caption file","n","Required footnote"]
    csv_export(hand/"EXHIBIT_INDEX.csv",cols,table_index)
    (hand/"EXHIBIT_INDEX.md").write_text("\n".join(descriptions)+markdown(cols,table_index),encoding="utf-8")
    (hand/"FIGURE_CAPTIONS.md").write_text("\n".join(captions),encoding="utf-8")
    (hand/"TABLE_NOTES.md").write_text("\n".join(notes),encoding="utf-8")
    claims=[
        ["STaR improves estimated reliability over implemented B4","F01/T03/S01",cls(primary),
         "95% family-stratified percentile cluster interval","Sole confirmatory contrast","No fleet guarantee or optimal quantity-only comparator"],
        ["Secondary STaR–B3 reliability difference","T03/F03",cls(competitive),"95% unadjusted parent-cluster interval",
         "Exploratory","No general or simultaneous superiority claim"],
        ["STaR uses fewer draws than B3 but is slower","F04/F05/T02/S05",f"{savings:.2f}% fewer draws; {delta_wall:+.2f} ms",
         "Savings denominator: B3 mean; paired time interval in T03","Exploratory","Not a wall-clock speedup"],
        ["Same c64 maximum, unequal work","S03/S04/S15",f'{work["B4"]["mean_trials"]:.2f} vs {work["STaR"]["mean_trials"]:.2f} trials (B4, STaR)',
         "All routes; no-limit counts are inferred from counters","Post-hoc descriptive","No equal actual effort or global quantity optimum"],
        ["Mean entire depot-return time is lower than B4","T03/F03",f'{completion["estimate"]:+.2f} native time units',
         f'95% [{completion["lower95"]:.2f}, {completion["upper95"]:.2f}]','Exploratory',"Native units are not known minutes"],
        ["The topology-changing stratum accounts for most observed gain","F07/T06",
         "See route-weighted stratum contributions in T06","Post-selection strata","Post-hoc descriptive","Not a causal decomposition"],
        ["STaR has unresolved routes, chiefly R2/RC2","F06/S06",f'{len(summary["negative"])} nonattainments',
         "Validation Wilson classification","Descriptive","No proof of irreparability"],
        ["Synthetic wait stresses are fixed-plan checks","F08/T07","Three separate perturbations",
         "10,000 draws per plan/model","Descriptive sensitivity","No real queue or unseen network validation"],
        ["Station attribute content is heavily shared","T01/S12",f'{len(summary["station_tables"])} byte-distinct CSV contents',
         "SHA-256 identity across 120 problems","Dataset audit","No claim of 120 independent charger networks"],
    ]
    claim_cols=["Claim","Exhibits","Estimate","Uncertainty","Status","Prohibited extrapolation"]
    csv_export(hand/"CLAIMS_MATRIX.csv",claim_cols,claims)
    (hand/"CLAIMS_MATRIX.md").write_text("# Claims matrix\n\n"+markdown(claim_cols,claims),encoding="utf-8")
    cite=[
        ["Primary STaR−B4 reliability",f'{100*primary["estimate"]:+.2f}',"pp",primary["n"],"T03 / S01","2 decimals","c64"],
        ["Primary lower 95%",f'{100*primary["lower95"]:.2f}',"pp",primary["n"],"S01","2 decimals","c64"],
        ["Primary upper 95%",f'{100*primary["upper95"]:.2f}',"pp",primary["n"],"S01","2 decimals","c64"],
        ["STaR−B4 mean completion",f'{completion["estimate"]:+.2f}',"native time",primary["n"],"T03","2 decimals","c64"],
        ["STaR−B3 mean reliability",f'{100*competitive["estimate"]:+.2f}',"pp",primary["n"],"T03","2 decimals","c64"],
        ["Search draw reduction vs B3",f'{savings:.2f}',"% of B3 mean",primary["n"],"T02","2 decimals","c64"],
        ["Additional mean elapsed time vs B3",f'{delta_wall:+.2f}',"ms",primary["n"],"T03","2 decimals","c64"],
        ["B0 point-below-target",total["below_target_B0"],"routes",total["exposed"],"T01","integer","c64/B0"],
        ["B0 LB nonattainment",total["B0_lower_bound_nonattainment"],"routes",total["exposed"],"T01","integer","c64/B0"],
    ]
    for name,row in method.items():
        cite.extend([[f"{name} lower-bound attained",row["lower_bound_attained"],"routes",row["n"],"T02","integer",f"c64/{name}"],
                     [f"{name} mean reliability",f'{100*row["mean_R"]:.2f}',"%",row["n"],"T02","2 decimals",f"c64/{name}"],
                     [f"{name} mean completion",f'{row["full_completion_time"]:.2f}',"native time",row["n"],"T02","2 decimals",f"c64/{name}"],
                     [f"{name} elapsed",f'{row["search_wall_ms"]:.2f}',"ms",row["n"],"T02","2 decimals",f"c64/{name}"],
                     [f"{name} mean search draws",f'{row["search_scenarios"]:.0f}',"draws",row["n"],"T02","nearest integer",f"c64/{name}"]])
    csv_export(hand/"NUMBERS_TO_CITE.csv",["Quantity","Display","Unit","Denominator","Derived source","Precision","Profile/method"],cite)
    (hand/"LIMITATIONS_FOR_WRITER.md").write_text(f"""# Boundaries for interpretation

- {len(summary['station_tables'])} distinct station CSV contents across 120 routing problems; all four also occur in development. Holdout parents are distinct, not novel station-attribute tables.
- Synthetic lognormal independent visit waits are a modeling assumption, not real station queues; the copula and scale checks are descriptive and do not reoptimize.
- Fixed offline customer order and assignment from CON, linear station rates, Q=700, h=1. Station operating hours are disabled. Native benchmark time is not minutes.
- Success is the joint route customer/depot event, not fleet service probability or global EVRPTW optimality.
- 10,000 final validation draws per plan. Pointwise Wilson classification and mean paired cluster intervals answer different questions. Near-threshold and tie checks do not establish true route superiority.
- {B4_NOTE} "No limit hit" is a counter-based diagnosis, not a recorded termination label or a proof of an exhaustive quantity optimum.
- {METHOD_NOTE} Lower simulation work did not make STaR faster than B3.
- Only route-weighted c64 reliability STaR minus B4 is confirmatory. Other endpoints, seeds, stresses and sensitivity intervals are unadjusted and exploratory.
""",encoding="utf-8")
    (hand/"README_RESULTS_PACKAGE.md").write_text(f"""# STaR-EVRP audited results package

**Read first:** {total['instances']} paired A/B holdout problems from 48 parents; {total['all_routes']:,} total CON routes, {total['exposed']:,} initially exposed and {total['zero_charge']:,} no-charge. All c64 methods use the same exposed routes. The only confirmatory contrast is STaR minus B4 c64 mean reliability: {cls(primary)}. B4 completed fewer candidate trials despite the same maximum. STaR used {savings:.2f}% fewer search draws than B3 but was slower. It is a narrow benefit, not general dominance.

## Use the package

Start with T01–T03 and F01–F03; use F04/F05 together when discussing effort. T04 gives both caps and the second seed; it does not increase the parent sample. F06 and T05 show hard-family limitations; F07/T06 distinguish topology strata from the separate no-partial ablation. F08/T07 are synthetic, fixed-plan stresses. Supplementary plots show the registered hard route, Wilson uncertainty and the consumed-trial distribution.

Use EXHIBIT_INDEX, FIGURE_CAPTIONS, TABLE_NOTES, CLAIMS_MATRIX and NUMBERS_TO_CITE as the writing interface. See LIMITATIONS_FOR_WRITER before using any statistic. Dataset citation pointers are in the original benchmark README and Phase 3 documentation; no new bibliographic claims are made here.

## Provenance and reproduction

Frozen executable `{lineage['frozen_commit']}`; source publication `{lineage['published_source_commit']}`. The audit uses the dataset SHA-256 inventory, archived JSON-gzip plan/validation records and the frozen analysis design. No new optimization or random stress setup. Reported Phase 3 runtime is archived, not measured again in Phase 4.

Run `{COMMAND}` from the repository root; options `--project-root` and `--output` support a clean external replay. Directly use the archived CON zip; no patch or extraction to Phase 3 is needed. Use the same software versions for bytewise PNG reproduction. See MANIFEST for exact source references. Main/supplementary figures are already rendered at 400 DPI and intended physical width; the table fragments use booktabs, graphicx, and longtable for long appendices.
""",encoding="utf-8")
    quality=read_json(out/"audit/final_quality_gate.json") if (out/"audit/final_quality_gate.json").is_file() else {
        "state":"pending external visual, test and repeatability evidence",
    }
    tracked=[path for path in out.rglob("*") if path.is_file() and path.name not in
             ("MANIFEST.json","STaR_EVRP_RESULTS_HANDOFF.zip","final_quality_gate.json")]
    manifest={"version":VERSION,"head":lineage["head"],"frozen":lineage["frozen_commit"],"tag":lineage["tag"],
              "command":COMMAND,"input_audit":"audit/lineage.json","gate_status":quality.get("gates",{}),
              "software":{"python":platform.python_version(),"platform":platform.platform(),
                          "numpy":__import__("numpy").__version__,"matplotlib":__import__("matplotlib").__version__},
              "source_sha256":{path:file_sha(root/path) for path in ("src/star_evrp/phase4_results.py",
                               "src/star_evrp/phase4_exhibits.py","src/star_evrp/phase4_release.py","scripts/run_phase4_results.py",
                               "scripts/finalize_phase4_quality.py","tests/test_phase4_results.py")},
              "files":{path.relative_to(out).as_posix():file_sha(path) for path in sorted(tracked)},
              "hash_exclusions":"manifest itself, final quality envelope and ZIP (avoid circular hash dependency)"}
    write_json(hand/"MANIFEST.json",manifest)
    package_path=out/"STaR_EVRP_RESULTS_HANDOFF.zip"
    selected=[path for path in tracked if path.relative_to(out).parts[0] in ("figures","tables","handoff")]
    selected.append(hand/"MANIFEST.json")
    with ZipFile(package_path,"w") as archive:
        for path in sorted(selected):
            name=path.relative_to(out).as_posix()
            archive.writestr(ZipInfo(name,date_time=(2020,1,1,0,0,0)),path.read_bytes(),compress_type=ZIP_DEFLATED)
    with ZipFile(package_path) as archive:
        require(archive.testzip() is None and len(archive.namelist())==len(selected),"ZIP CRC or membership failure")
        for path in selected:
            require(archive.read(path.relative_to(out).as_posix())==path.read_bytes(),"ZIP round trip mismatch")
    return {"zip_members":len(selected),"zip_sha256":file_sha(package_path)}


def contact_sheets(out, directory, *, width_px):
    """Reduced-width proof sheets outside the publication figure tree."""
    directory.mkdir(parents=True,exist_ok=True)
    paths=sorted((out/"figures").glob("*/*.png"))
    for first in range(0,len(paths),4):
        images=[]
        for path in paths[first:first+4]:
            meta=read_json(path.with_suffix(".json"))
            with Image.open(path) as page:
                copy=page.convert("RGB")
                pixels=round(width_px*meta["physical_mm"][0]/178)
                copy.thumbnail((pixels,3000), Image.Resampling.LANCZOS)
                images.append(copy)
        tile_height=max(img.height for img in images)+20
        proof=Image.new("RGB",(width_px*2+32,tile_height*2+24),"#e7e7e7")
        for index,img in enumerate(images):
            proof.paste(img,(10+(index%2)*(width_px+10),10+(index//2)*tile_height))
        proof.save(directory/f"proof_{width_px}_{first//4+1}.png")
