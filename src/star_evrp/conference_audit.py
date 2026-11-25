"""Validate archived lineage, presentation formats, proof renders and release ZIP."""

import csv
import gzip
import json
import re
import struct
import subprocess
from contextlib import closing
from io import BytesIO
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from zlib import crc32

from PIL import Image, ImageOps

from star_evrp.conference_data import BASE, FROZEN, near, protected_hashes
from star_evrp.conference_exhibits import TABLE_STEMS, table_latex, text
from star_evrp.conference_figures import FLOW, STEMS
from star_evrp.data_loader import load_instance
from star_evrp.phase3 import read_bundle
from star_evrp.phase4_release import markdown
from star_evrp.phase4_results import file_sha, git, read_json, require, sha
from star_evrp.phase6_archive import csv_rows, write_bytes, write_json

ZIP_NAME="STaR_EVRP_CONFERENCE_EXHIBITS.zip"
SOURCE_FILES=(
    "src/star_evrp/conference_data.py","src/star_evrp/conference_figures.py",
    "src/star_evrp/conference_exhibits.py","src/star_evrp/conference_audit.py",
    "scripts/build_conference_exhibits.py","tests/test_conference_exhibits.py",
)


def verify_input_protection(root,out):
    pre=read_json(root/"results/conference/audit/preflight.json")
    require(pre["status"]=="pass" and pre["frozen"]==FROZEN,"Missing original preflight")
    protected=protected_hashes(root)
    require(protected==pre["protected_sha256"],"Protected file hash changed since preflight")
    base=set(git(root,"ls-tree","-r","--name-only",BASE).decode().splitlines())
    changed=git(root,"diff","--name-only",BASE).decode().splitlines()
    allowed=("README.md",".gitattributes","docs/CONFERENCE_EXHIBITS_REPORT.md",*SOURCE_FILES,
             "prompts/PROMPT_07_CONFERENCE_FIGURES_AND_TABLES.md")
    require(all(p in allowed or p.startswith("results/conference/") or p not in base for p in changed),
            "Unexpected historical changes")
    phase_counts={}
    for phase in (5,6):
        release=root/f"results/phase{phase}"
        hashes=read_json(release/"audit/final_gate.json")["file_sha256"]
        require(all(file_sha(release/n)==v for n,v in hashes.items()),f"Phase {phase} release changed")
        phase_counts[str(phase)]=len(hashes)
    write_json(out/"audit/preservation.json",dict(status="pass",base=BASE,frozen=FROZEN,protected_count=len(protected),
               release_counts=phase_counts,archived_optimizer_calls=0,stochastic_replay_calls=0,changed_paths=changed))


def verify_map(root,out):
    details=read_json(out/"data/Fig01_route_selection.json")
    chosen=details["chosen"]
    options=csv_rows(out/"data/Fig01_route_selection.csv")
    ranks=[(int(r["customers"]),r["parent"],r["variant"],int(r["route"])) for r in options]
    require(ranks==sorted(ranks) and len(options)==2321,"Map candidates changed or reordered")
    first=next(r for tier in ("1","2","3") for r in options if r["tier"]==tier)
    require((first["parent"],first["variant"],int(first["route"]))==
            (chosen["parent"],chosen["variant"],chosen["route"]),"Wrong selected example")
    instance=load_instance(root,chosen["parent"],chosen["variant"])
    nodes=csv_rows(out/"data/Fig01_instance_nodes.csv")
    require([(int(r["node"]),r["type"],float(r["x"]),float(r["y"])) for r in nodes]==
            [(n.node_id,n.node_type.value,n.x,n.y) for n in instance.nodes],"Map contains incorrect coordinates")
    archive=root/"results/phase3/con_bundles.zip"
    with ZipFile(archive) as z:
        data=z.read(details["con_bundle_member"])
    require(sha(data)==details["con_bundle_member_sha256"],"Original map source digest differs")
    con_routes=json.loads(gzip.decompress(data))["rows"]["routes"]
    original=next(r for r in con_routes if r["route_id"]==chosen["route"])
    stops=csv_rows(out/"data/Fig01_route_stops.csv")
    require([int(r["node"]) for r in stops if r["plan"]=="CON"]==[r["node_id"] for r in original["stops"]],
            "Original map route differs from ZIP")
    for entry in csv_rows(out/"data/Fig01_metrics.csv"):
        raw=root/entry["source"]
        plan_file=root/entry["source"].replace("/raw/","/plans/")
        code="B0" if entry["method"]=="CON" else "STaR"
        records=read_bundle(raw)["rows"]
        plans=read_bundle(plan_file)["rows"]
        row=next(r for r in records if (r["method"],r["route_id"])==(code,chosen["route"]))
        plan=next(p for p in plans if (p["method"],p["route_id"])==(code,chosen["route"]))
        relevant=[r for r in stops if r["plan"]==entry["method"]]
        require([int(r["node"]) for r in relevant]==[s["node_id"] for s in plan["stops"]],"Map plan sequence differs")
        require([float(r["charged"]) for r in relevant]==[e[4] for e in plan["events"]],"Map charge amounts differ")
        require(row["plan_sha256"]==entry["plan_digest"] and plan["fingerprint"]==entry["fingerprint"],"Map plan digest differs")
        for expected,event in zip(relevant,plan["events"],strict=True):
            node=instance.node(event[0])
            require((float(expected["x"]),float(expected["y"]))==(node.x,node.y),"Map stop changed coordinates")
        validation=row["validation"]
        for a,b in (("successes","successes"),("completion","completion"),("scenarios","n"),("wilson_lower","wilson95_lower_one_sided")):
            require(float(entry[a])==validation[b],"Map archived metric differs")
    meta=read_json(out/"figures"/(STEMS[0]+".json"))["plotted"]
    require(meta["aspect"].startswith("equal") and all(
        meta["zoom_limits"][0]<=float(r["x"])<=meta["zoom_limits"][1] and
        meta["zoom_limits"][2]<=float(r["y"])<=meta["zoom_limits"][3] for r in stops),"Shared map bounds omit stops")
    for displayed,saved in zip(meta["ordered_stops"],stops,strict=True):
        require(all(str(displayed[k])==v for k,v in saved.items()),"Map renderer used different data")
    return {"chosen":chosen,"original_zip_verified":True,"stops":len(stops),"actual_nodes":len(nodes),"shared_bounds":True}


def verify_flow(root,out):
    graph=read_json(out/"data/Fig02_flow.json")
    meta=read_json(out/"figures"/(STEMS[1]+".json"))
    require(graph==meta["plotted"]==FLOW and len(graph["nodes"])==8,"Diagram and flow specification differ")
    src=root/"src/star_evrp"
    search=(src/"competitive_search.py").read_text(encoding="utf-8")
    score=(src/"search_common.py").read_text(encoding="utf-8")
    evaluator=(src/"route_evaluator.py").read_text(encoding="utf-8")
    check = [
        ("Initial full score", "competitive_search.py:188–224", search,
         ("current = original","current_entry = evaluator.prepare(current)","best = () if method == \"B0\" else score(current, current_entry)",
          "evaluator.extend(route, entry, samples)")),
        ("Priority and interleaved moves","competitive_search.py:92–169",search,
         ("np.argsort(bounds, kind=\"stable\")","abs(gap + 0.5 - positions[0])","zip_longest(quantities, structural())")),
        ("Trial guards and duplicate rejection","competitive_search.py:225–250",search,
         ("generation_cap = 10 * budget.max_candidate_evals","if identity in seen","not entry.trace.feasible")),
        ("Conditional true-reliability screen","competitive_search.py:251–258",search,
         ("if star and best[1] == 1","bounds.min(initial=1.0) < target - 1e-12")),
        ("Prefix bound and extension","competitive_search.py:259–269; route_evaluator.py:87–107",search+evaluator,
         ("prefix = samples // 4","samples - prefix","entry.trace.end_clock","lower - 1e-8","optimistic <= best","tape[previous:count]")),
        ("Lexicographic strict acceptance","search_common.py:22–28; competitive_search.py:270–277",score+search,
         ("return (valid, 1, -self.e_completion, self.reliability)","return (valid, 0, self.reliability, -self.e_completion)",
          "and challenger > best","if not improved")),
        ("Independent validation after optimization","phase3.py:287–345; competitive_search.py:188–279",search,("seed, \"opt\"",)),
    ]
    result=[]
    for claim,reference,source,needles in check:
        require(all(needle in source for needle in needles),f"Diagram semantics stale: {claim}")
        result.append(dict(check=claim,source=reference,status="pass"))
    require(not graph["validation"]["feedback"] and "validation(" not in search,"Diagram uses optimization feedback")
    require(any(edge[:2]==["score","rank"] for edge in graph["edges"]),"Missing incumbent loop")
    return result


def png_format(path,mm):
    data=path.read_bytes()
    require(data.startswith(b"\x89PNG\r\n\x1a\n"),"PNG signature")
    cursor=8
    physical=None
    while cursor+12<=len(data):
        length,kind=struct.unpack(">I4s",data[cursor:cursor+8])
        buffer=data[cursor+8:cursor+8+length]
        expected=struct.unpack(">I",data[cursor+8+length:cursor+12+length])[0]
        require(crc32(kind+buffer)==expected,"PNG CRC")
        if kind==b"pHYs":
            physical=struct.unpack(">IIB",buffer)
        cursor+=12+length
    require(physical==(15748,15748,1) and cursor==len(data),"PNG scale or structure")
    with Image.open(path) as img:
        size=img.size
        require(all(abs(px-400*x/25.4)<1.01 for px,x in zip(size,mm,strict=True)),"PNG dimensions")
        require(img.convert("RGB").getpixel((0,0))==(255,255,255),"Nonwhite figure background")
    with Image.open(path) as img:
        img.verify()
    return list(size)


def svg_format(path,mm):
    svg=ElementTree.parse(path).getroot()
    types=[item.tag.rsplit("}",1)[-1] for item in svg.iter()]
    require("text" in types and "path" in types and "image" not in types,"SVG is not editable vector")
    for key,target in zip(("width","height"),mm,strict=True):
        near(float(svg.attrib[key].removesuffix("pt")),target*72/25.4,"SVG physical size",atol=.005)
    return {"text_objects":types.count("text"),"paths":types.count("path")}


def pdf_format(path,mm,pdfium):
    data=path.read_bytes()
    require(data.startswith(b"%PDF-") and b"/FontFile2" in data and b"/Subtype /Image" not in data,
            "PDF lacks embedded TrueType fonts or includes a raster image")
    with pdfium.PdfDocument(path) as pdf:
        require(len(pdf)==1,"Unexpected figure PDF page count")
        with closing(pdf[0]) as page:
            for found,target in zip(page.get_size(),mm,strict=True):
                near(found,target*72/25.4,"PDF page size",atol=.006)
            with closing(page.get_textpage()) as t:
                chars=t.count_chars()
                require(chars>40 and "\ufffd" not in t.get_text_range(),"PDF text missing or corrupt")
    return {"pages":1,"embedded_truetype":True,"extractable_chars":chars}


def audit(root,out,pdfium):
    verify_input_protection(root,out)
    fmt={}
    assets=out/"figures"
    require({p.name for p in assets.iterdir()}=={f"{stem}.{ext}" for stem in STEMS for ext in ("png","pdf","svg","json")},
            "Wrong number of figure exports")
    for stem in STEMS:
        where=assets/stem
        card=read_json(where.with_suffix(".json"))
        require(card["dpi"]==400 and card["physical_mm"][0]==178 and card["font"]=="DejaVu Sans","Figure style mismatch")
        require(all(file_sha(root/n)==h for n,h in card["source_sha256"].items()),"Figure has stale archived source")
        require(all(file_sha(where.with_suffix("."+ext))==value for ext,value in card["formats_sha256"].items()),
                "Figure format hash mismatch")
        require(card["plot_source_sha256"]==file_sha(root/"src/star_evrp/conference_figures.py"),"Stale renderer")
        fmt[stem]=dict(png=png_format(where.with_suffix(".png"),card["physical_mm"]),
                       svg=svg_format(where.with_suffix(".svg"),card["physical_mm"]),
                       pdf=pdf_format(where.with_suffix(".pdf"),card["physical_mm"],pdfium),sha256=card["formats_sha256"])
    require({p.name for p in (out/"tables").iterdir()}==
            {f"{stem}.{ext}" for stem in TABLE_STEMS for ext in ("csv","tex","md")},"Wrong number of tables")
    for stem in TABLE_STEMS:
        there=out/"tables"/stem
        needed=read_json(out/"data"/f"{stem}_display.json")
        h=needed["headers"]
        with there.with_suffix(".csv").open(newline="",encoding="utf-8") as handle:
            content=list(csv.reader(handle))
        expect=[[("NA" if x is None else str(x)) for x in row] for row in needed["exact"]]
        require(content==[h,*expect],"CSV not equal to full precision display input")
        r=needed["rendered"]
        require(there.with_suffix(".tex").read_text(encoding="utf-8")==table_latex(stem,h,r) and
                there.with_suffix(".md").read_text(encoding="utf-8")==markdown(h,r),"Display table drift")
    write_json(out/"audit/formats.json",dict(status="pass",formats=fmt,tables=len(TABLE_STEMS)))
    write_json(out/"audit/spatial_and_logic.json",dict(status="pass",map=verify_map(root,out),flow=verify_flow(root,out)))


def proofs(out,scratch,pdfium):
    from matplotlib import get_data_path

    scratch.mkdir(parents=True,exist_ok=True)
    assets=out/"figures"
    rendered={}
    for stem in STEMS:
        path=assets/(stem+".png")
        with Image.open(path) as img:
            small=img.convert("RGB")
            small.thumbnail((675,1000),Image.Resampling.LANCZOS)
            small.save(scratch/f"{stem}_png_675.png")
            ImageOps.grayscale(small).save(scratch/f"{stem}_gray_675.png")
        pdf_path=assets/(stem+".pdf")
        with pdfium.PdfDocument(pdf_path) as pdf:
            with closing(pdf[0]) as page:
                native=page.render(scale=400/72).to_pil().copy()
                native.save(scratch/f"{stem}_pdf_native.png")
                reduced=native.copy()
                reduced.thumbnail((675,1000),Image.Resampling.LANCZOS)
                reduced.save(scratch/f"{stem}_pdf_675.png")
                ImageOps.grayscale(reduced).save(scratch/f"{stem}_pdf_gray_675.png")
        rendered[stem]=dict(png_reduced=list(small.size),pdf_native=list(native.size),pdf_reduced=list(reduced.size))
    for font in ("DejaVuSans.ttf","DejaVuSans-Bold.ttf"):
        source=Path(get_data_path())/"fonts/ttf"/font
        write_bytes(scratch/font,source.read_bytes())
    document=[r"\documentclass[10pt]{article}",r"\usepackage{booktabs}",r"\setlength{\textwidth}{178mm}",
              r"\setlength{\oddsidemargin}{-7mm}",r"\pagestyle{empty}",
              r"\DeclareFontFamily{TU}{confsans}{}",
              r'\DeclareFontShape{TU}{confsans}{m}{n}{<-> "[DejaVuSans.ttf]"}{}',
              r'\DeclareFontShape{TU}{confsans}{b}{n}{<-> "[DejaVuSans-Bold.ttf]"}{}',
              r"\DeclareFontShape{TU}{confsans}{bx}{n}{<-> ssub * confsans/b/n}{}",
              r"\renewcommand{\rmdefault}{confsans}",r"\begin{document}"]
    for stem in TABLE_STEMS:
        document.extend(((out/"tables"/f"{stem}.tex").read_text(encoding="utf-8"),r"\clearpage"))
    document.append(r"\end{document}")
    text(scratch/"conference_tables.tex","\n".join(document))
    cmd=["tectonic","-C","--keep-logs","--color","never","conference_tables.tex"]
    run=subprocess.run(cmd,cwd=scratch,capture_output=True)
    log=scratch/"conference_tables.log"
    transcript=run.stdout+run.stderr+(b"\n"+log.read_bytes() if log.exists() else b"")
    write_bytes(out/"audit/tectonic.txt",transcript)
    bad=re.findall(rb".*(?:Overfull|Too wide|Missing character).*",transcript,re.I)
    report=dict(status="fail",command=cmd,exit=run.returncode,overfull_or_missing=[r.decode(errors="replace") for r in bad],
                version=subprocess.check_output(["tectonic","-V"],text=True).strip())
    where=out/"audit/table_compilation.json"
    write_json(where,report)
    require(run.returncode==0 and not bad,"TeX compile failed or overfull")
    with pdfium.PdfDocument(scratch/"conference_tables.pdf") as doc:
        require(len(doc)==3,"TeX proof did not fit three pages")
        for i,stem in enumerate(TABLE_STEMS):
            with closing(doc[i]) as page:
                with closing(page.get_textpage()) as t:
                    boxes=[t.get_charbox(j) for j in range(t.count_chars())]
                require(boxes,"Empty TeX proof")
                x0,y0,x1,y1=min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)
                require(x1-x0<=178*72/25.4+1.0 and y1-y0<page.get_height(),"Table exceeds print area")
                native=page.render(scale=2.5).to_pil().copy()
                native.save(scratch/f"{stem}_page.png")
                h=page.get_height()
                native.crop((max(0,int(2.5*x0)-24),max(0,int(2.5*(h-y1))-24),int(2.5*x1)+24,int(2.5*(h-y0))+24)).save(
                    scratch/f"{stem}_table.png")
    report.update(status="pass",pages=3,physical_text_width_mm=178,
                  sha256={stem:file_sha(out/"tables"/f"{stem}.tex") for stem in TABLE_STEMS},
                  proof_pdf_sha256=file_sha(scratch/"conference_tables.pdf"))
    write_json(where,report)
    write_json(out/"audit/proof_renders.json",dict(status="pass",figures=rendered,
        renderer=str(pdfium.PYPDFIUM_INFO),bundled_rendering_engine=str(pdfium.PDFIUM_INFO),grayscale=True))


def package(root,out,extract_dir):
    protected=read_json(out/"audit/preservation.json")
    numeric=read_json(out/"audit/numerical.json")
    semantics=read_json(out/"audit/spatial_and_logic.json")
    formats=read_json(out/"audit/formats.json")
    proofs_done=read_json(out/"audit/proof_renders.json")
    compile_result=read_json(out/"audit/table_compilation.json")
    visual=read_json(out/"audit/visual.json")
    tests=read_json(out/"audit/tests.json")
    repeat=read_json(out/"audit/reproducibility.json")
    for doc in (protected,numeric,semantics,formats,proofs_done,compile_result,visual,tests,repeat):
        require(doc["status"]=="pass","A required publication check failed")
    require(repeat["missing_input_rejected"] and all(file_sha(out/n)==x for n,x in repeat["derived_sha256"].items()),
            "Stale rebuild evidence")
    require(all(file_sha(out/"tables"/f"{stem}.tex")==compile_result["sha256"][stem] for stem in TABLE_STEMS),
            "TeX proof was not produced from the packaged tables")
    require(all(visual["figures"][s]["sha256"]==formats["formats"][s]["sha256"] and
                visual["figures"][s]["native_reduced_gray"] for s in STEMS),"Missing or stale visual review")
    require(all(visual["tables"][s]["tex_sha256"]==compile_result["sha256"][s] for s in TABLE_STEMS),"Unreviewed table print proof")
    code={n:file_sha(root/n) for n in SOURCE_FILES}
    refs={}
    for stem in STEMS:
        refs.update(read_json(out/"figures"/f"{stem}.json")["source_sha256"])
    for stem in TABLE_STEMS:
        refs.update(read_json(out/"data"/f"{stem}_display.json")["source_sha256"])
    for source in ("results/phase5/STaR_EVRP_FINAL_RESULTS_HANDOFF.zip","results/phase6/STaR_EVRP_PHASE6_SCIENTIFIC_SUPPLEMENT.zip",
                   "results/phase6/data/experiment_summary.json"):
        refs[source]=file_sha(root/source)
    for name,digest in refs.items():
        require(file_sha(root/name)==digest,"Stale input hash")
    gates={f"C7-G{i}":"PASS" for i in range(7)}
    write_json(out/"audit/final_gates.json",dict(status="pass",gates=gates,figures=len(STEMS),tables=len(TABLE_STEMS),
                tests=tests,planned_file_formats=["PNG at 400 DPI","vector PDF","editable SVG","CSV","LaTeX","Markdown"]))
    skip={"MANIFEST.json",ZIP_NAME,"audit/zip_envelope.json"}
    members={p.relative_to(out).as_posix():p for p in sorted(out.rglob("*")) if p.is_file() and p.relative_to(out).as_posix() not in skip}
    write_json(out/"MANIFEST.json",dict(schema=1,base=BASE,frozen=FROZEN,source_sha256=refs,code_sha256=code,
               output_sha256={n:file_sha(p) for n,p in members.items()},gates=gates))
    members["MANIFEST.json"]=out/"MANIFEST.json"
    buffer=BytesIO()
    with ZipFile(buffer,"w",compression=ZIP_DEFLATED,compresslevel=6) as archive:
        for name,where in sorted(members.items()):
            info=ZipInfo(name)
            info.compress_type=ZIP_DEFLATED
            archive.writestr(info,where.read_bytes(),compresslevel=6)
    write_bytes(out/ZIP_NAME,buffer.getvalue())
    extract_dir.mkdir(parents=True,exist_ok=False)
    with ZipFile(out/ZIP_NAME) as archive:
        require(archive.testzip() is None and archive.namelist()==sorted(members),"Bad archive members or CRC")
        for name in archive.namelist():
            safe=PurePosixPath(name)
            require(not safe.is_absolute() and ".." not in safe.parts and "\\" not in name and ":" not in name,
                    "Unsafe ZIP member")
            target=extract_dir.joinpath(*safe.parts)
            require(target.resolve().is_relative_to(extract_dir.resolve()),"ZIP target leaves extraction root")
            write_bytes(target,archive.read(name))
        require(all(file_sha(extract_dir/n)==file_sha(source) for n,source in members.items()),"ZIP extraction byte mismatch")
    result=dict(status="pass",name=ZIP_NAME,sha256=file_sha(out/ZIP_NAME),verified_members=len(members),
                extracted_bytes_verified=True)
    write_json(out/"audit/zip_envelope.json",result)
    return result
