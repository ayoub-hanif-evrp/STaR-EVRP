"""Release integrity, writer handoff and deterministic archive packaging."""

import csv
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from star_evrp.phase4_release import markdown, png_audit, tex_table
from star_evrp.phase4_results import file_sha, read_json, require
from star_evrp.phase6_analysis import STAGES, analyze
from star_evrp.phase6_archive import csv_rows, verify, write_bytes, write_csv, write_json
from star_evrp.phase6_exhibits import build

ZIP_NAME="STaR_EVRP_PHASE6_SCIENTIFIC_SUPPLEMENT.zip"
DOCS=("ANALYSIS_PROTOCOL","DIAGNOSTIC_REPORT","FINAL_REPORT","MATHEMATICAL_AUDIT","REPOSITORY_CLEANUP","RESULTS_HANDOFF")


def check_diagnostic_accounting(out):
    data=out/"data"
    features=csv_rows(data/"route_features.csv")
    exposed=[r for r in features if r["exposed"]=="True"]
    require(len(features)==8606 and len({(r["instance"],r["route"]) for r in features})==8606
            and len({r["instance"] for r in features})==120 and len(exposed)==2891,"Invalid route census")
    require(all(int(r[prefix+"visits"])==sum(int(r[prefix+name]) for name in
                ("positive_charge_visits","zero_quantity_visits","small_positive_visits"))
                for r in exposed for prefix in ("source_","selected_")),"Station visit accounting differs")
    for row in csv_rows(data/"attainment_transitions.csv"):
        n,gained,lost,retained,neither,net=(int(row[k]) for k in ("n","gained","lost","retained","neither","net"))
        require(gained+lost+retained+neither==n and gained-lost==net,"Invalid attainment transition")
    for row in csv_rows(data/"paired_directions.csv"):
        require(sum(int(row[k]) for k in ("gains","ties","losses"))==int(row["n"]),"Invalid directions")
        require(abs(float(row["gain_contribution"])+float(row["loss_contribution"])-float(row["mean_signed"]))<=1e-8,
                "Paired contributions do not reconcile")
    return {"routes":len(features),"exposed":len(exposed)}


def audits(root,out,protocol):
    verify(root,out,all_inputs=True)
    exhibits = read_json(out/"data/exhibits.json")
    figures,tables = {},[]
    for entry in exhibits:
        where=out/entry["path"]
        if entry["kind"]=="figure":
            meta=read_json(where.with_suffix(".json"))
            require(all(file_sha(out/n)==v for n,v in meta["source_sha256"].items()),"Stale plot source array")
            require(meta["plotting_sha256"]==file_sha(root/"src/star_evrp/phase6_exhibits.py"),"Stale plot source code")
            figures[where.name] = png_audit(where,meta)
        else:
            source=read_json(out/"data/table_rows"/f"{where.stem}.json")
            header,rows=(source[k] for k in ("headers","rows"))
            with where.with_suffix(".csv").open(encoding="utf-8",newline="") as f:
                require(list(csv.reader(f))==[header,*rows],"Stale table CSV")
            require(where.read_text(encoding="utf-8")==tex_table(header,rows) and
                    where.with_suffix(".md").read_text(encoding="utf-8")==markdown(header,rows),"Stale display table")
            tables.append(where.name)
    expected = 5 if read_json(out/"audit/as1_gate.json")["eligible"] else 4
    require(len(figures)==len(tables)==expected,"Exhibits missing")
    raw = sorted(f for area in ("raw","plans") for f in (out/area).rglob("*.json.gz"))
    formats=dict(status="pass",figures=figures,tables=tables,source_count=len(raw),
                 raw_sha256={f.relative_to(out).as_posix():file_sha(f) for f in raw},mechanism=check_diagnostic_accounting(out))
    write_json(out/"audit/formats.json",formats)
    return formats


def final_gate(root,out,protocol):
    formats = audits(root,out,protocol)
    diag,math,elig,visual,tex,tests,rebuild,cleanup=[read_json(out/"audit"/f"{name}.json") for name in
        ("diagnostics","math_check","as1_gate","visual","tex","tests","rebuild","cleanup")]
    require(set(formats["figures"])==set(visual["figures"]) and all(
        row["sha256"]==visual["figures"][name]["sha256"] and visual["figures"][name]["native_and_reduced"]
        for name,row in formats["figures"].items()),"Missing or stale visual evidence")
    require(all(item["status"]=="pass" for item in (diag,math,tex,tests,rebuild,cleanup)),"Necessary scientific gate failed")
    require(not tex["warnings"] and tex["pages"]==len(formats["tables"]) and all(
        file_sha(out/"tables"/name)==digest for name,digest in tex["table_sha256"].items()),"Missing or stale TeX evidence")
    math_ref = read_json(out/"audit/math_reference.json") if elig["eligible"] else {"status":"skipped","reason":elig["reason"]}
    require(not elig["eligible"] or math_ref["status"]=="pass","Independent real-route math audit failed")
    require(all(file_sha(out/name)==digest for name,digest in rebuild["hashes"].items()),"Stale clean rebuild evidence")
    replays={}
    for command in STAGES:
        if command=="as1" and not elig["eligible"]:
            replays[command]={"status":"skipped","reason":elig["reason"]}
        else:
            replay=read_json(out/"audit"/f"{command}_replay.json")
            run=read_json(out/"audit"/f"{command}_execution.json")
            require(replay["status"]=="pass" and replay["routes"]==run["routes"] and replay["rows"]==run["rows"]
                    and replay["scalar_checks"]==10*replay["unique_plan_checks"],"Missing paired validation replay")
            replays[command]={k:replay[k] for k in ("status","rows","unique_plan_checks","scalar_checks")}
    return {"status":"pass","gates":{
        "P6-G0":"PASS","P6-G1":"PASS","P6-G2":"PASS",
        "P6-G3":"PASS" if elig["eligible"] else "SKIPPED WITH JUSTIFICATION",
        "P6-G4":"PASS","P6-G5":"PASS","P6-G6":"PASS","P6-G7":"PASS"},"replays":replays,"tests":tests,
        "clean_rebuild":len(rebuild["hashes"]),"cleanup":cleanup,"archive":diag["archive"],
        "mathematical_reference":{k:v for k,v in math_ref.items() if k!="rows"},
        "figures":formats["figures"],"table_count":len(formats["tables"]),"optional":{
            "STaR-H1":"Skipped prospectively","prefix":"Historical s8192 context only","runtime_sensitivity":"20 and 100 ms included"}}


def claim_rows(out):
    exp = read_json(out/"data/experiment_summary.json")
    diag=read_json(out/"audit/diagnostics.json")
    claim = diag["archive"]["primary"]
    numbers = [{"topic":"Registered STaR vs FSPC","estimate":claim["estimate"]*100,
                "lower":claim["lower95"]*100,"upper":claim["upper95"]*100,"n":claim["n"],"unit":"pp",
                "cohort":"original holdout","status":"confirmatory; archived","source":"Phase 5 T07 and Phase 3 primary"}]
    comparisons=(("as1","AS1","STaR"),("as1","AS1","FSPC"),("fixed-topology","FT-SAA","FSPC"),
                 ("fixed-topology","STaR","FT-SAA"),("fixed-topology","STaR","FSPC"))
    for stage,a,b in comparisons:
        if exp[stage].get("status")=="skipped":
            continue
        effects=[r for r in exp[stage]["contrasts"] if r["challenger"]==a and r["reference"]==b and r["cohort"]=="all120"
                 and r["tape"]=="phase6" and r["subset"]=="all" and r["metric"] in ("R_pp","completion")]
        numbers.extend({"topic":f'{a} vs {b} ({r["metric"]})',"estimate":r["mean"],"lower":r["lo95"],"upper":r["hi95"],
                        "n":r["n"],"unit":"pp" if r["metric"]=="R_pp" else "native time","cohort":stage+" fixed panel",
                        "status":"exploratory","source":f"data/{stage}_paired_effects.csv"} for r in effects)
    numbers.extend({"topic":f'STaR vs SLS {r["guard_ms"]} ms ({r["metric"]})',"estimate":r["mean"],"lower":r["lo95"],"upper":r["hi95"],
                    "n":r["n"],"unit":{"R_pp":"pp","wall_ms":"ms","draws":"draws"}[r["metric"]],"cohort":"timing panel",
                    "status":"exploratory","source":"data/timing_paired_effects.csv"}
                   for r in exp["timing"]["contrasts"] if r["cohort"]=="all120" and r["metric"] in ("R_pp","wall_ms","draws"))
    claims=[
        ("Registered reliability improved against implemented FSPC","Phase 5 T07","Only Phase 3 registered claim; actual work differed"),
        ("The held-out archival SLS result includes quality, work and elapsed time","Phase 5 T07","Report +0.32 pp, 34.59% fewer draws and slower wall time; no general dominance"),
        ("Independent one-visit threshold and expected-return formula","Mathematical audit","Fixed plan, one stochastic visit, specified clocks and wait law"),
        ("Fixed-tape prefix optimistic score","Mathematical audit","No global or path-equivalence assumption under a binding budget"),
        ("Observed family and source-slack differences","F06-02 and mechanism_strata.csv","No causal attribution and no outcome-driven strata"),
        ("AS1 restricted-domain panel comparison","F06-03 and T06-03 when gate opens","Existing parents, no extension to multi-visit global optimum"),
        ("FT-SAA solver comparison","F06-04 and T06-04","Include limits, fallback and conditional certification; no equal computation claim"),
        ("Common nominal runtime guards","F06-05 and T06-05","Retain overshoot and actual timings; inference by parent after aggregating repeats"),
    ]
    return numbers,[dict(claim=a,source=b,qualification=c) for a,b,c in claims]


def handoff(root,out,protocol):
    gate=final_gate(root,out,protocol)
    directory=out/"handoff"
    exhibits=read_json(out/"data/exhibits.json")
    numbers,claims=claim_rows(out)
    write_csv(directory/"EXHIBIT_INDEX.csv",exhibits)
    write_csv(directory/"NUMBERS_TO_CITE.csv",numbers)
    write_csv(directory/"CLAIMS_MATRIX.csv",claims)
    for kind,name in (("figure","FIGURE_CAPTIONS"),("table","TABLE_NOTES")):
        content=[f"# {name.replace('_',' ').title()}"]+[f'## {r["name"]}\n\n{r["caption"]}\n\nData: `{r["source"]}`'
                 for r in exhibits if r["kind"]==kind]
        write_bytes(directory/f"{name}.md",("\n\n".join(content)+"\n").encode())
    glossary=(root/"results/phase5/handoff/METHOD_GLOSSARY.md").read_text(encoding="utf-8")
    glossary += ("\n| Phase 6 method | Definition |\n| --- | --- |\n"
                 "| AS1 | Analytical optimizer over zero or one station visit and all customer gaps. |\n"
                 "| FT-SAA | Fixed-Topology Sample-Average optimizer of charge quantities. |\n")
    write_bytes(directory/"METHOD_GLOSSARY.md",glossary.encode())
    write_bytes(directory/"README_RESULTS_PACKAGE.md",(
        "# Phase 6 scientific supplement\n\nUse together with the authoritative Phase 5 results handoff. "
        "Start with the Phase 6 final report and claims matrix. The full raw batches and ordered plans live under "
        "`results/phase6/raw` and `results/phase6/plans` in the repository. "
        "Every archived new comparison is exploratory. The frozen STaR method and original confirmatory estimate remain unchanged.\n").encode())
    write_bytes(directory/"LIMITATIONS_FOR_WRITER.md",(
        "# Scientific scope\n\nKeep the original Phase 3 primary and Phase 5 SLS, FSPC and work disclosures. "
        "The benchmark has fixed CON customers and synthetic station lognormal waits. All four station CSV contents occurred in development. "
        "No new independent charging environment, fleet recourse, queues or station hours was tested. "
        "Panel estimates describe selected routes only. Intervals are unadjusted and conditional on the validation draws. "
        "Report FT-SAA replay flags and model tolerances, and maintain the distinction between bounds, empirical rates and Wilson classification. "
        "Draw savings and actual elapsed time need separate interpretation. AS1 and FT-SAA are supplementary experiments.\n").encode())
    included={}
    for area in ("figures","tables","manifests","handoff","data","audit"):
        for path in sorted((out/area).rglob("*")):
            if not path.is_file() or path.name in ("MANIFEST.json","final_gate.json","cleanup_final_git.json"):
                continue
            if area=="data" and (path.name=="route_features.csv" or path.name=="paired_routes.csv"):
                continue
            included[path.relative_to(out).as_posix()]=path
    for name in DOCS:
        path=root/"docs"/f"PHASE6_{name}.md"
        included[f"docs/{path.name}"]=path
    release_code = [*root.glob("src/star_evrp/phase6_*.py"),*root.glob("tests/test_phase6_*.py")]
    manifest={"schema":1,"base_commit":protocol["configuration"]["base_commit"],"frozen_commit":protocol["frozen_commit"],
              "gate_status":gate["gates"],"release_source_sha256":{p.relative_to(root).as_posix():file_sha(p) for p in release_code},
              "sha256":{name:file_sha(path) for name,path in included.items()},
              "full_benchmark_package":"results/phase5/STaR_EVRP_FINAL_RESULTS_HANDOFF.zip",
              "bulk_files_in_repository":["results/phase6/data/route_features.csv","results/phase6/data/paired_routes.csv",
                                           "results/phase6/raw","results/phase6/plans"]}
    write_json(directory/"MANIFEST.json",manifest)
    included["handoff/MANIFEST.json"]=directory/"MANIFEST.json"
    archive=BytesIO()
    with ZipFile(archive,"w",compression=ZIP_DEFLATED,compresslevel=6) as z:
        for name,path in sorted(included.items()):
            info=ZipInfo(name)
            info.compress_type=ZIP_DEFLATED
            z.writestr(info,path.read_bytes(),compresslevel=6)
    where=out/ZIP_NAME
    write_bytes(where,archive.getvalue())
    with ZipFile(where) as z:
        require(z.testzip() is None and set(z.namelist())==set(included),"Phase 6 ZIP mismatch")
        require(all(z.read(n)==p.read_bytes() for n,p in included.items()),"Phase 6 ZIP byte mismatch")
    gate.update(zip_members=len(included),zip_sha256=file_sha(where),
                file_sha256={p.relative_to(out).as_posix():file_sha(p) for p in sorted(out.rglob("*"))
                             if p.is_file() and p!=out/"audit/final_gate.json"})
    write_json(out/"audit/final_gate.json",gate)
    return gate


def action(root,out,protocol,task):
    if task=="analyze":
        return analyze(root,out,protocol)
    if task=="build-exhibits":
        return build(root,out)
    if task=="audit":
        return audits(root,out,protocol)
    if task=="package":
        return handoff(root,out,protocol)
    raise ValueError(task)
