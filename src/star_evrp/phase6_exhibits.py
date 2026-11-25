"""Publication exhibits from the verified Phase 6 diagnostic and panel arrays."""

from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from star_evrp.phase4_release import markdown, tex_table
from star_evrp.phase4_results import file_sha, read_json
from star_evrp.phase6_archive import csv_rows, write_bytes, write_csv, write_json

BLUE, ORANGE, GRAY, NAVY = "#0072B2", "#C34E05", "#687787", "#172C3A"


def panels(n, height=83):
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"axes.labelcolor":NAVY,"text.color":NAVY,
                         "xtick.color":NAVY,"ytick.color":NAVY,"axes.spines.top":False,"axes.spines.right":False,
                         "axes.edgecolor":"#89939b","figure.facecolor":"white","savefig.facecolor":"white",
                         "axes.axisbelow":True,"svg.hashsalt":"star-phase6"})
    return plt.subplots(1,n,figsize=(178/25.4,height/25.4),layout="constrained")


def style(axis, title, dimension="x"):
    axis.set_title(title,loc="left",fontweight="bold",fontsize=9,pad=7)
    axis.grid(axis=dimension,color="#dde3e8",linewidth=.5)


def interval(axis, rows, labels, colors=None):
    axis.axvline(0,color=GRAY,linestyle=":",linewidth=.8)
    for i,row in enumerate(rows):
        color = colors[i] if colors else BLUE
        if row["lo95"] is not None:
            axis.hlines(i,row["lo95"],row["hi95"],color=color,lw=2)
        axis.plot(row["mean"],i,"o",color=color,ms=4.6)
    axis.set_yticks(range(len(labels)),labels)
    axis.invert_yaxis()


def effect_rows(section,pairs,metric):
    index={(r["challenger"],r["reference"]):r for r in section["contrasts"]
           if r["cohort"]=="all120" and r["tape"]=="phase6" and r["metric"]==metric and r["subset"]=="all"}
    return [index[pair] for pair in pairs]


def complexity_display(out):
    records=[r for r in csv_rows(out/"data/charging_complexity.csv") if r["group"]=="all" and r["measure"]=="visits"]
    groups=[]
    for cohort in ("all120","development","holdout"):
        for plan in ("CON all","CON exposed","STaR exposed","STaR nonattained"):
            subset=[r for r in records if r["cohort"]==cohort and r["plan"]==plan]
            counts=[sum(int(r["count"]) for r in subset if min(int(r["level"]),4)==level) for level in range(5)]
            groups.append(dict(cohort=cohort,plan=plan,n=sum(counts),counts=counts))
    return groups


def build(root,out):
    data=out/"data"
    diag=read_json(out/"audit/diagnostics.json")
    study=read_json(data/"experiment_summary.json")
    complexity=complexity_display(out)
    paths=[]

    def figure(name,fig,caption,arrays,sources):
        path=out/"figures"/f"{name}.png"
        destination=BytesIO()
        fig.savefig(destination,dpi=400,metadata={"Software":"STaR-EVRP Phase 6 / Matplotlib"})
        write_bytes(path,destination.getvalue())
        dim=[round(x*25.4,4) for x in fig.get_size_inches()]
        plt.close(fig)
        source_hashes={f"data/{name}":file_sha(data/name) for name in sources}
        meta=dict(physical_mm=dim,png_sha256=file_sha(path),caption=caption,plotted=arrays,source_sha256=source_hashes,
                  plotting_sha256=file_sha(root/"src/star_evrp/phase6_exhibits.py"))
        write_json(path.with_suffix(".json"),meta)
        paths.append(dict(name=name,kind="figure",path=path.relative_to(out).as_posix(),caption=caption,source="; ".join(source_hashes)))

    def table(name,head,rows,caption,source):
        where=out/"tables"/name
        rows=[[str(cell) if cell is not None else "NA" for cell in row] for row in rows]
        write_csv(where.with_suffix(".csv"),[dict(zip(head,row,strict=True)) for row in rows],head)
        write_bytes(where.with_suffix(".md"),markdown(head,rows).encode())
        write_bytes(where.with_suffix(".tex"),tex_table(head,rows).encode())
        where_sidecar=data/"table_rows"/f"{name}.json"
        write_json(where_sidecar,dict(headers=head,rows=rows,source=source))
        paths.append(dict(name=name,kind="table",path=where.with_suffix(".tex").relative_to(out).as_posix(),
                          caption=caption,source=source))

    fig,(left,right)=panels(2,88)
    levels=np.arange(5)
    by_transition=np.zeros((5,5),dtype=int)
    for row in csv_rows(data/"visit_transitions.csv"):
        if row["cohort"]=="all120" and row["group"]=="all":
            by_transition[min(int(row["source"]),4),min(int(row["selected"]),4)] += int(row["n"])
    merged=[r for r in complexity if r["plan"]=="CON all" and r["cohort"] in ("development","holdout")]
    for n,r in enumerate(merged):
        left.bar(levels+.34*(n-.5),100*np.asarray(r["counts"])/r["n"],width=.31,
                 label=f'{r["cohort"].title()} ({r["n"]:,})',color=(BLUE,ORANGE)[n])
    left.set_xticks(levels,("0","1","2","3","4+"))
    left.set(xlabel="Original CON station visits",ylabel="Share of source routes (%)")
    left.legend(frameon=False,fontsize=7,loc="upper right")
    style(left,"a  All original routes","y")
    scale=np.log1p(by_transition)
    right.imshow(scale,cmap="Blues",vmin=0,vmax=scale.max())
    for i,j in np.ndindex(5,5):
        right.text(j,i,f"{by_transition[i,j]:,}" if by_transition[i,j] else "·",ha="center",va="center",
                   color="white" if scale[i,j]>.61*scale.max() else NAVY,fontsize=7)
    right.set_xticks(levels,("0","1","2","3","4+"))
    right.set_yticks(levels,("0","1","2","3","4+"))
    right.set(xlabel="Selected STaR station visits",ylabel="Original CON station visits")
    right.set_title(f'b  Exposed routes (n = {diag["exposed"]:,})',loc="left",fontweight="bold",fontsize=9,pad=7)
    figure("F06-01_charging_complexity",fig,
           "Station visits include zero-quantity stops. Left compares the original CON distribution in the development and holdout partitions. "
           "Right gives matched CON and STaR visit counts for 2,891 exposed routes; darker shading uses log(1 + count) to show sparse transitions. Descriptive archived data.",
           {"original_shares":merged,"transitions":by_transition.tolist(),"shading":"log1p(count)"},("charging_complexity.csv","visit_transitions.csv"))
    table("T06-01_charging_complexity",["Cohort","Plan","n","0","1","2","3","4+"],
          [[r["cohort"],r["plan"],r["n"],*r["counts"]] for r in complexity],
          "Exact counts of visits by partition, with counts above three pooled. CON all includes no-charge routes; all selected STaR rows use the initially exposed population or named nonattained subset.",
          "data/charging_complexity.csv")

    fig,(left,right)=panels(2,88)
    directions=[r for r in csv_rows(data/"paired_directions.csv") if r["cohort"]=="all120" and r["metric"]=="R_pp"
                and r["comparison"] in ("FSPC","SLS","QBR")]
    ys=np.arange(len(directions))
    gains=[float(r["gain_contribution"]) for r in directions]
    losses=[float(r["loss_contribution"]) for r in directions]
    left.barh(ys,gains,color=BLUE,height=.45,label="Positive contribution")
    left.barh(ys,losses,color=ORANGE,height=.45,label="Negative contribution")
    left.plot([float(r["mean_signed"]) for r in directions],ys,"D",mfc="white",mec=NAVY,ms=4,label="Net mean")
    left.set_yticks(ys,[r["comparison"] for r in directions])
    left.invert_yaxis()
    left.axvline(0,color=GRAY,lw=.6)
    left.set_xlabel("STaR gain vs comparator (pp)")
    left.legend(frameon=False,fontsize=6.6,loc="lower right")
    style(left,"a  Opposing pooled effects")
    strata=[r for r in csv_rows(data/"mechanism_strata.csv") if r["cohort"]=="all120" and r["comparison"]=="FSPC"
            and r["dimension"] in ("source_visit_bin","min_customer_slack_quartile")]
    ordered=sorted(strata,key=lambda r:(r["dimension"]!="source_visit_bin",r["group"]))
    y = np.arange(len(ordered))
    observed=[100*int(r["nonattained"])/int(r["n"]) for r in ordered]
    labels=[("1 visit" if r["group"]=="1" else f'{r["group"]} visits') if r["dimension"]=="source_visit_bin"
            else f'Slack Q{r["group"]}' for r in ordered]
    right.barh(y,observed,color=[BLUE]*3+[ORANGE]*4,height=.55)
    right.set_yticks(y,labels)
    right.invert_yaxis()
    for i,(r,x) in enumerate(zip(ordered,observed,strict=True)):
        right.text(x+.15,i,f'{int(r["nonattained"])}/{int(r["n"]):,}',va="center",fontsize=6.5)
    right.set_xlim(0,max(observed)*1.32)
    right.set_xlabel("Selected STaR nonattainment (%)")
    style(right,"b  Pre-repair strata")
    figure("F06-02_route_mechanism",fig,
           "All 2,891 exposed routes. Positive and negative observed reliability differences contribute separately to the route-weighted STaR mean. "
           "Nonattainment uses the one-sided Wilson lower bound; counts are failures over routes, with source minimum customer slack quartiles frozen on development. The strata overlap across feature types. Exploratory.",
           {"directions":directions,"strata":ordered,"nonattainment_percent":observed},("paired_directions.csv","mechanism_strata.csv"))
    table("T06-02_mechanism",["Source stratum","Routes","Parents","STaR fails","STaR - FSPC pp [95%]"],
          [[label,r["n"],r["parents"],r["nonattained"],
            f'{float(r["mean"]):+.2f} [{float(r["lo95"]):+.2f}, {float(r["hi95"]):+.2f}]' if r["lo95"]!="NA" else f'{float(r["mean"]):+.2f}']
            for label,r in zip(labels,ordered,strict=True)],
          "All 2,891 exposed routes. The within-feature strata partition routes. Bounds are 95% pointwise family-by-partition parent-bootstrap intervals where at least eight parents are represented.",
          "data/mechanism_strata.csv")

    if study["as1"].get("status")!="skipped":
        section=study["as1"]
        fig,(left,right)=panels(2,82)
        comparisons=[("AS1",m) for m in ("FSPC","SLS","STaR")]
        results=effect_rows(section,comparisons,"R_pp")
        interval(left,results,[f"vs {m}" for _,m in comparisons])
        style(left,f'a  Independent validation (n = {section["panel_n"]})')
        left.set_xlabel("AS1 reliability difference (pp)")
        vals=[float(r["MC_minus_exact_pp"]) for r in csv_rows(data/"as1_exact_vs_mc.csv")
              if r["tape"]=="phase6" and r["selected_visits"]=="1" and r["method"]=="AS1"]
        counts,bins=np.histogram(vals,bins=19)
        right.bar(bins[:-1],counts,width=np.diff(bins)*.92,align="edge",color=BLUE)
        right.axvline(0,color=ORANGE,ls="--",lw=1.1)
        right.set(xlabel="Sampled minus exact reliability (pp)",ylabel="AS1 plans")
        style(right,f"b  One-visit agreement (n = {len(vals)})","y")
        figure("F06-03_analytical_single_visit",fig,
               f'{section["panel_n"]} prospectively selected routes, originally single-visit. Left compares the new 10,000-row tape for AS1 and saved plans, '
               "with pointwise clustered 95% intervals. The CON reference is in T06-03. Right uses the AS1 plans still containing one visit. "
               "The analytical optimizer considers zero or one visit. Frozen STaR and SLS may use multiple visits. Exploratory panel.",
               {"effects":results,"bins":bins.tolist(),"counts":counts.tolist(),"observations_pp":vals},
               ("as1_paired_effects.csv","as1_exact_vs_mc.csv"))
        ms=[r for r in section["metrics"] if r["cohort"]=="all120" and r["tape"]=="phase6"]
        table("T06-03_analytical_single_visit",["Method","Routes","Mean R (%)","LB attained","Completion"],
              [[r["method"],r["n"],f'{100*r["reliability"]:.2f}',r["attained"],f'{r["completion"]:.2f}'] for r in ms],
              "Independent Phase 6 tape on the AS1 panel. Completion is unconditional in native units. Timing and analytic versus empirical uncertainty are in the associated raw CSVs.",
              "data/as1_summary.csv; data/as1_exact_vs_mc.csv")

    section=study["fixed-topology"]
    pairs=[("FT-SAA","FSPC"),("STaR","FSPC"),("STaR","FT-SAA")]
    results=effect_rows(section,pairs,"R_pp")
    completions=effect_rows(section,pairs,"completion")
    labels=[f"{a} vs {b}" for a,b in pairs]
    fig,(left,right)=panels(2,78)
    interval(left,results,labels)
    interval(right,completions,[""]*len(labels))
    style(left,"a  Reliability")
    style(right,"b  Full completion")
    left.set_xlabel("Paired reliability difference (pp)")
    right.set_xlabel("Paired completion difference (native units)")
    statuses=section["statuses"]
    fig.supxlabel(f'{statuses.get("single_visit_oracle",0)} single-visit oracles  •  '
                  f'{statuses.get("target_certified",0)+statuses.get("below_target_certified",0)} complete MILP certificates  •  '
                  f'{statuses.get("target_completion_only",0)} completion-only  •  '
                  f'{section["panel_n"]-sum(statuses.get(k,0) for k in ("single_visit_oracle","target_certified","below_target_certified","target_completion_only"))} uncertified',
                  fontsize=7)
    figure("F06-04_fixed_topology",fig,
           f'{section["panel_n"]} fixed comparator panel routes on the new 10,000-draw tape. Includes valid fallback plans on every uncertified route. '
           f'Solver status counts: {", ".join(k.replace("_"," ")+" "+str(v) for k,v in sorted(section["statuses"].items()))}. '
           "Points are paired route means and bars are pointwise 95% parent-cluster intervals. FT-SAA received a separate solver budget. Exploratory panel.",
           {"reliability":results,"completion":completions,"status_counts":section["statuses"]},
           ("fixed-topology_paired_effects.csv","fixed-topology_route_results.csv"))
    ms=[r for r in section["metrics"] if r["cohort"]=="all120" and r["tape"]=="phase6"]
    table("T06-04_fixed_topology",["Subset","Method","n","R (%)","LB attained","Completion"],
          [[r["subset"],r["method"],r["n"],f'{100*r["reliability"]:.2f}',r["attained"],f'{r["completion"]:.2f}'] for r in ms],
          "All and certified-subset comparisons on the same independent tape. The certified subset includes the single-visit mathematical oracle and certified linear-model MILP solves. "
          "All-panel rows include valid fallbacks. See solver stages for incumbent, replay, bounds and gaps.",
          "data/fixed-topology_summary.csv; data/fixed-topology_solver_stages.csv")

    section=study["timing"]
    pooled=[r for r in section["metrics"] if r["cohort"]=="all120"]
    timing_index={(r["guard_ms"],r["metric"]):r for r in section["contrasts"] if r["cohort"]=="all120"}
    guards=sorted({r["guard_ms"] for r in pooled})
    fig,(left,center,right)=panels(3,88)
    interval(left,[timing_index[g,"R_pp"] for g in guards],[f"{g} ms" for g in guards])
    left.set_ylim(len(guards)-.58,-.42)
    style(left,"a  Paired quality")
    left.set_xlabel("STaR minus SLS (pp)")
    colors={"STaR":BLUE,"SLS":ORANGE}
    for r in pooled:
        i=guards.index(r["guard_ms"])+(.12 if r["method"]=="STaR" else -.12)
        c=colors[r["method"]]
        center.hlines(i,r["wall_ms_p25"],r["wall_ms_p75"],color=c,lw=1.4)
        center.plot(r["wall_ms_median"],i,"o" if r["method"]=="STaR" else "s",color=c,ms=4)
        right.plot(r["draws"]/1000,i,"o" if r["method"]=="STaR" else "s",color=c,ms=4)
    for i,g in enumerate(guards):
        center.plot(g,i,"|",color=GRAY,ms=9)
    for ax,title,lab in ((center,"b  Realized search","Wall time (ms)"),(right,"c  Search work","Mean draws (thousands)")):
        ax.set_yticks(np.arange(len(guards)),[""]*len(guards))
        ax.set_ylim(-.42,len(guards)-.58)
        ax.invert_yaxis()
        ax.set_xlabel(lab)
        style(ax,title)
    for method,c in colors.items():
        right.plot([],[],"o" if method=="STaR" else "s",color=c,label=method,ms=4)
    right.legend(frameon=False,loc="best",fontsize=7)
    figure("F06-05_controlled_runtime",fig,
           f'{section["panel_n"]} paired routes and three repeats per method per nominal guard. Left uses within-route mean reliability and pointwise 95% parent-bootstrap intervals. '
           "Center shows the median and interquartile range of per-route median wall time, with nominal guards as gray ticks. "
           "Right shows mean incremental search draws. The 50 ms guard was primary. Cooperative guards can overshoot. Exploratory panel.",
           {"route_summaries":pooled,"paired_quality":[timing_index[g,"R_pp"] for g in guards]},
           ("timing_summary.csv","timing_paired_effects.csv"))
    table("T06-05_controlled_runtime",["Guard ms","Method","n","R (%)","Median ms","p95 ms","Draws","Over / repeats"],
          [[r["guard_ms"],r["method"],r["n"],f'{100*r["reliability"]:.2f}',f'{r["wall_ms_median"]:.2f}',
            f'{r["wall_ms_p95"]:.2f}',f'{r["draws"]:.0f}',f'{r["over_guard"]}/{r["repeats"]}']
            for r in sorted(pooled,key=lambda r:(r["guard_ms"],r["method"]))],
          "Route-level medians from three repeats. Reliability is mean of the within-route means. Overshoot counts refer to individual repeats. CPU, IQR, work counts and parent-cluster contrasts are in the linked CSVs.",
          "data/timing_summary.csv; data/timing_paired_effects.csv")
    write_json(data/"exhibits.json",paths)
    return paths
