"""Phase 5 scientific graphics with explicit cohort and profile sidecars."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np

from star_evrp.phase4_results import FAMILIES, file_sha, grouped, write_json
from star_evrp.phase5_analysis import ABL, MAIN

COLOR={"CON":"#555555","MWR":"#497a9e","QBR":"#876299","STaR":"#b84213","SLS":"#0072b2","FSPC":"#008264",
       "STaR-NPC":"#777777","STaR-NSP":"#466780","STaR-NAS":"#009a80","STaR-NPP":"#805999"}
MARKS={"c64":"o","c24":"s","s8192":"^","c64_seed2":"D"}
PROFILE_NOTE="Profiles (plan cap/draw cap): c64 64/131,072; c24 24/131,072; s8192 128/8,192; c64 seed 2 repeats c64 with a second optimizer seed."
LABEL={"all120":"All 120 (descriptive)","holdout":"96 holdout","development":"24 development"}


def frame(width=178,height=83,panels=1):
    figure, axes=plt.subplots(1,panels,figsize=(width/25.4,height/25.4),squeeze=False,layout="constrained")
    return figure,axes[0]


def figures(summary,out,source_map):
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8.3,"axes.titlesize":9,"xtick.labelsize":8,
                         "ytick.labelsize":8,"legend.fontsize":8,"axes.spines.top":False,"axes.spines.right":False,
                         "axes.grid":True,"axes.axisbelow":True,"grid.alpha":.22,"lines.linewidth":1.25})
    index=[]
    n={cohort:next(row["n"] for row in summary["pool"] if row["cohort"]==cohort and row["method"]=="STaR")
       for cohort in LABEL}
    pool={(row["cohort"],row["method"]):row for row in summary["pool"]}
    data_hash=file_sha(out/"data/summary.json")

    def save(name,fig,data,caption,cohort,*,summary_keys,profile="c64",custom_n=None):
        folder="main" if name.startswith("F") else "supplementary"
        path=out/"figures"/folder/f"{name}.png"
        path.parent.mkdir(parents=True,exist_ok=True)
        fig.savefig(path,dpi=400,facecolor="white",metadata={"Software":"STaR-EVRP Phase 5"})
        size=[round(value*25.4,1) for value in fig.get_size_inches()]
        plt.close(fig)
        info={"filename":path.relative_to(out).as_posix(),"caption":caption,"cohort":cohort,"profile":profile,
              "routes":custom_n if custom_n is not None else n.get(cohort,n),"dpi":400,"physical_mm":size,
              "png_sha256":file_sha(path),"summary_sha256":data_hash,"source_map_sha256":source_map,
              "source":f"data/summary.json: {summary_keys}","plot_function":"star_evrp.phase5_exhibits.figures",
              "plot_source_sha256":file_sha(Path(__file__)), "data":data}
        write_json(path.with_suffix(".json"),info)
        index.append({key:value for key,value in info.items() if key!="data"})

    coverage=[]
    fig,axes=frame(panels=2)
    for ax,variant in zip(axes,("A","B")):
        for pos,family in enumerate(FAMILIES):
            rows=[row for row in summary["population"] if (row["family"],row["variant"])==(family,variant)]
            parts={name:sum(row["exposed"] for row in rows if row["partition"]==name) for name in ("holdout","development")}
            total=sum(row["all_routes"] for row in rows)
            covered=sum(parts.values())
            coverage.append(dict(family=family,variant=variant,total=total,**parts))
            ax.barh(pos,parts["holdout"],color="#317497",height=.56,label="Holdout" if not pos else None)
            ax.barh(pos,parts["development"],left=parts["holdout"],color="#dbad75",height=.56,
                    label="Development" if not pos else None)
            ax.text(covered+10,pos,f"{covered}/{total:,}",va="center")
        ax.set(title=f"Variant {variant}",yticks=range(6),yticklabels=FAMILIES,
               xlabel="Initially station-exposed routes",xlim=(0,max(item["total"] for item in coverage)*.59))
        ax.invert_yaxis()
    share=max(item["holdout"]+item["development"] for item in coverage)
    for ax in axes:
        ax.set_xlim(0,share*1.36)
    fig.legend(*axes[0].get_legend_handles_labels(),ncols=2,loc="outside upper center",frameon=False)
    save("F01_benchmark_coverage",fig,coverage,
         "All 120 class/variant problems, with 96 holdout and 24 development. Labels are exposed/all original CON routes; "
         "only initially station-exposed routes enter the repair comparisons.","all120",summary_keys="population")

    fig,axes=frame(panels=2)
    selected=[pool[cohort,method] for cohort in ("holdout","all120") for method in MAIN]
    for index_method,method in enumerate(MAIN):
        for offset,cohort in ((-.18,"holdout"),(.18,"all120")):
            row=pool[cohort,method]
            scores=[100*row["mean_R"],100*row["lower_bound_attained"]/row["n"]]
            for axis,score in zip(axes,scores):
                axis.barh(index_method+offset,score,height=.31,color=COLOR[method],alpha=1 if cohort=="holdout" else .46)
                label=f"{score:.1f}%" if axis is axes[0] else f'{row["lower_bound_attained"]:,}/{row["n"]:,}'
                axis.text(score+1.0,index_method+offset,label,va="center",fontsize=7.9)
    for ax,lbl in zip(axes,("Mean validation reliability (%)","Lower-bound attainment (%)")):
        ax.set(xlabel=lbl,xlim=(0,125),xticks=range(0,101,25),yticks=range(4),yticklabels=MAIN)
        ax.invert_yaxis()
    fig.legend(handles=[Line2D([],[],color=".25",lw=6,label=label,alpha=alpha)
                        for label,alpha in (("96 holdout",1),("All 120 incl. development",.46))],
               ncols=2,loc="outside upper center",frameon=False)
    save("F02_main_methods_reliability_attainment",fig,selected,
         f"Identical c64 rule; {n['holdout']:,} initially exposed holdout routes; {n['all120']:,} all-120 exposed routes "
         "including 24 development instances (descriptive). Mean success and individual one-sided Wilson lower-bound attainment are distinct. "
         "SLS and FSPC were also tested; see the supplementary evidence and mandatory registered primary disclosure.","all120",summary_keys="pool")

    fig,axes=frame(panels=2)
    restor={(row["cohort"],row["method"]):row for row in summary["restoration"]}
    data=[]
    for index_method,method in enumerate(MAIN):
        for offset,cohort in ((-.18,"holdout"),(.18,"all120")):
            mean=pool[cohort,method]["full_completion_time"]
            r=restor[cohort,method]
            data.append(dict(method=method,cohort=cohort,mean_completion=mean,restoration=r))
            alpha=1 if cohort=="holdout" else .46
            axes[0].barh(index_method+offset,mean,height=.31,color=COLOR[method],alpha=alpha)
            axes[0].text(mean+30,index_method+offset,f"{mean:,.1f}",va="center",fontsize=7.9)
            restored=100*r["attained"]/r["n"]
            axes[1].barh(index_method+offset,restored,height=.31,color=COLOR[method],alpha=alpha)
            axes[1].text(restored+1,index_method+offset,f'{r["attained"]}/{r["n"]}',va="center",fontsize=7.9)
    axes[0].set(xlabel="Mean full completion (native units)",xlim=(0,4400))
    axes[1].set(xlabel="Restored among CON point failures (%)",xlim=(0,125),xticks=range(0,101,25))
    for ax in axes:
        ax.set(yticks=range(4),yticklabels=MAIN); ax.invert_yaxis()
    fig.legend(handles=[Line2D([],[],color=".25",lw=6,label=label,alpha=alpha)
                        for label,alpha in (("96 holdout",1),("All 120 incl. development",.46))],
               ncols=2,loc="outside upper center",frameon=False)
    save("F03_main_methods_completion_and_repair",fig,data,
         "Left: unconditional full depot return on every initially exposed c64 route. Right: lower-bound attainment among "
         "routes with CON estimated reliability below 0.95; counts shown over that subset, not over all exposed routes. "
         "Both panels are descriptive; paired deteriorations are in the supplementary table.","all120",summary_keys="pool, restoration")

    fig,axes=frame(height=77,panels=2)
    ablation=[]
    for ax,metric,title in zip(axes,("reliability","attained"),("Mean reliability","Lower-bound attainment")):
        ax.axvline(0,color=".3",lw=.8,ls="--")
        for pos,method in enumerate(ABL[1:]):
            for offset,cohort,shape in ((-.14,"holdout","o"),(.14,"all120","D")):
                row=next(row for row in summary["paired"] if (row["cohort"],row["comparison"],row["metric"])==(cohort,method,metric))
                ablation.append(row)
                ax.hlines(pos+offset,100*row["lo95"],100*row["hi95"],colors=COLOR[method])
                ax.plot(100*row["mean"],pos+offset,marker=shape,color=COLOR[method],mfc="none" if cohort=="all120" else COLOR[method])
        ax.set(title=title,yticks=range(4),yticklabels=ABL[1:],xlabel="Full STaR − ablation (percentage points)")
        ax.invert_yaxis()
    fig.legend(handles=[Line2D([],[],marker=shape,ls="none",c=".25",mfc="none" if shape=="D" else ".25",label=lab)
                        for shape,lab in (("o","96 holdout"),("D","All 120 incl. development"))],
               ncols=2,loc="outside upper center",frameon=False)
    save("F04_ablation_quality",fig,ablation,
         "Exploratory paired differences at c64; positive favors full STaR. Bars denote 95% family-stratified parent-cluster "
         "percentile intervals, split by partition for the pooled panel. Unadjusted pointwise intervals; not simultaneous.","all120",summary_keys="paired")

    fig,axes=frame(panels=2,height=88)
    data=[]
    for pos,method in enumerate(ABL):
        for offset,partition in ((-.17,"holdout"),(.17,"development")):
            row=pool[partition,method]
            data.append(row)
            for ax,field in zip(axes,("search_scenarios","search_wall_ms")):
                ax.barh(pos+offset,row[field],height=.3,color=COLOR[method],alpha=1 if partition=="holdout" else .47)
    for ax,lab in zip(axes,("Mean incremental search draws","Mean search wall time (ms)")):
        ax.set(xlabel=lab,yticks=range(5),yticklabels=ABL); ax.invert_yaxis()
    axes[0].xaxis.set_major_locator(MultipleLocator(5000))
    axes[0].xaxis.set_major_formatter(FuncFormatter(lambda val,_:f"{val:,.0f}"))
    fig.legend(handles=[Line2D([],[],color=".25",lw=6,label=label,alpha=alpha)
                        for label,alpha in (("Holdout",1),("Development",.47))],
               loc="outside upper center",ncols=2,frameon=False)
    save("F05_ablation_work_and_runtime",fig,data,
         "Per-route c64 means with six workers. Holdout full/NPC elapsed times are archived Phase 3, whereas NSP/NAS/NPP "
         "are Phase 5. Development full/NPC and new ablations were measured in separate runs. No paired elapsed inference across "
         "the archive/new boundary; CPU and consumed plans are tabulated separately. Draw counts are not elapsed time.","all120",summary_keys="pool, work")

    fig,axes=frame(panels=2,height=103)
    family={(row["cohort"],row["family"],row["variant"],row["method"]):row for row in summary["family"]}
    selected=[]
    for ax,variant in zip(axes,("A","B")):
        data=np.array([[100*family["all120",f,variant,m]["lower_bound_attained"]/family["all120",f,variant,m]["n"]
                       for m in MAIN] for f in FAMILIES])
        picture=ax.imshow(data,cmap="cividis",vmin=0,vmax=100,aspect="auto")
        ylabels=[]
        for i,name in enumerate(FAMILIES):
            cell=[family["all120",name,variant,m] for m in MAIN]
            selected.extend(cell)
            ylabels.append(f"{name} ({cell[0]['n']})")
            for j,item in enumerate(cell):
                ax.text(j,i,f"{item['lower_bound_attained']}\n{data[i,j]:.0f}%",ha="center",va="center",
                        color="white" if data[i,j]<56 else "black")
        ax.set(title=f"Variant {variant}",yticks=range(6),yticklabels=ylabels,xticks=range(4),xticklabels=MAIN); ax.grid(False)
    fig.colorbar(picture,ax=list(axes),shrink=.81,label="Lower-bound attainment (%)")
    save("F06_family_variant_attainment",fig,selected,
         "All 120 instances including development (descriptive). Family A/B row labels give exposed denominators, cells give "
         "attained counts and rounded percentages. Holdout-only strata are available in the family table. R2 and RC2 remain challenging.","all120",summary_keys="family")

    stress=summary["archived"]["robustness"]
    def stressplot(name,methods):
        fig,(ax,)=frame(height=77)
        modes=("scale125","sigma125","copula035")
        stress_rows=[]
        for index_method,method in enumerate(methods):
            subset=[next(row for row in stress if (row["stress"],row["method"])==(mode,method)) for mode in modes]
            stress_rows.extend(subset)
            ax.bar(np.arange(3)+(index_method-(len(methods)-1)/2)*.19,[100*row["lower_bound_attained"]/row["n"] for row in subset],
                   width=.18,color=COLOR[method],label=method)
        ax.set(xticks=range(3),xticklabels=["Wait scale ×1.25","Log σ ×1.25","Normal copula ρ=.35"],
               ylim=(0,103),ylabel="Lower-bound attainment (%)")
        fig.legend(ncols=len(methods),loc="outside upper center",frameon=False)
        save(name,fig,stress_rows,
             f"Archived holdout c64 fixed-plan stresses on {n['holdout']:,} exposed routes per shown method. Each stress changes "
             "one synthetic assumption; copula preserves marginals. No reoptimization, real queue calibration, or extrapolation to new station tables.",
             "holdout",summary_keys="archived.robustness")
    stressplot("F07_stress_robustness",("CON","STaR"))
    fig,(ax,)=frame(height=76)
    stress_changes=[]
    models=("scale125","sigma125","copula035")
    for position,method in enumerate(("CON","SLS","FSPC","STaR")):
        reference=pool["holdout",method]
        for mode,marker,offset in zip(models,("s","^","o"),(-.16,0,.16)):
            row=next(row for row in stress if (row["stress"],row["method"])==(mode,method))
            delta=100*(row["lower_bound_attained"]-reference["lower_bound_attained"])/row["n"]
            ax.plot(delta,position+offset,marker=marker,color=COLOR[method],ls="none",ms=5)
            stress_changes.append({**row,"unstressed_attained":reference["lower_bound_attained"],"delta_attainment_pp":delta})
    ax.axvline(0,color=".3",ls="--")
    ax.set(yticks=range(4),yticklabels=["CON","SLS","FSPC","STaR"],
           xlabel="Stress minus unstressed attainment (percentage points)")
    ax.invert_yaxis()
    fig.legend(handles=[Line2D([],[],color=".28",marker=mark,ls="none",label=name) for mark,name in
                        (("s","Wait scale ×1.25"),("^","Log σ ×1.25"),("o","Normal copula ρ=.35"))],
               ncols=3,loc="outside upper center",frameon=False)
    save("S07_full_robustness",fig,stress_changes,
         "Four archived holdout c64 methods. Change in lower-bound attainment versus the same method's original model, "
         "in percentage points, on 2,321 exposed routes per method. Synthetic stress on fixed selected plans, no reoptimization.",
         "holdout",summary_keys="archived.robustness, pool")

    fig,(ax,)=frame(height=92)
    primary=next(row for row in summary["paired"] if row["status"]=="confirmatory")
    parents=[row for row in summary["archived"]["parent_effects"] if row["competitor"]=="FSPC" and row["metric"]=="reliability"]
    ax.axvline(0,color=".35",ls="--")
    for index_family,family_name in enumerate(FAMILIES,1):
        block=[row for row in parents if row["family"]==family_name]
        ax.scatter([100*row["mean_difference"] for row in block],index_family+np.linspace(-.2,.2,len(block)),
                   facecolors="none",edgecolors=COLOR["FSPC"],s=[12+.17*row["paired_routes"] for row in block])
    mean,lo,hi=[100*primary[key] for key in ("mean","lo95","hi95")]
    ax.hlines(0,lo,hi,color=COLOR["STaR"],lw=2)
    ax.plot(mean,0,"D",color=COLOR["STaR"])
    ax.annotate(f"{mean:+.2f} [{lo:.2f}, {hi:.2f}]",(hi,0),xytext=(7,0),textcoords="offset points",va="center")
    ax.set(yticks=range(7),yticklabels=["Pooled",*FAMILIES],ylim=(6.55,-.55),xlabel="STaR − FSPC reliability (percentage points)")
    ax.margins(x=.17)
    save("S01_registered_primary_contrast",fig,{"primary":primary,"parent_effects":parents},
         f"Sole confirmatory result. Route-weighted reliability on {n['holdout']:,} original holdout route pairs; "
         "interval is the archived 95% family-stratified parent cluster bootstrap. Circles are 48 descriptive parent means. "
         "Equal cap does not mean equal actual work. Disclose this result in the main text.","holdout",summary_keys="paired, archived.parent_effects")

    archive_budget={(row["profile"],row["method"]):row for row in summary["archived"]["budget"]}
    for name,field,xlabel in (("S02_competitive_quality_work","search_scenarios","Mean incremental search draws"),
                               ("S03_competitive_runtime","search_wall_ms","Mean measured search wall time (ms)")):
        fig,(ax,)=frame()
        numeric=[]
        for row in summary["archived"]["reliability_quality"]:
            method,profile=row["method"],row["profile"]
            coord=archive_budget[profile,method][field]
            numeric.append({**row,field:coord})
            ax.vlines(coord,100*row["lower95"],100*row["upper95"],colors=COLOR[method])
            ax.plot(coord,100*row["mean_R"],marker=MARKS[profile],color=COLOR[method],
                    mfc="none" if profile=="c64_seed2" else COLOR[method],ms=5)
        handles=[Line2D([],[],marker="o",ls="none",color=COLOR[method],label=method) for method in ("SLS","FSPC","STaR")]
        handles.extend(Line2D([],[],marker=marker,ls="none",color=".3",label=profile.replace("_seed2"," seed 2"),
                              mfc="none" if profile=="c64_seed2" else ".3") for profile,marker in MARKS.items())
        fig.legend(handles=handles,ncols=7,loc="outside upper center",frameon=False)
        ax.set(xlabel=xlabel,ylabel="Mean validation reliability (%)")
        if field=="search_scenarios":
            ax.xaxis.set_major_formatter(FuncFormatter(lambda val,_:f"{val:,.0f}"))
        save(name,fig,numeric,
             "Archived 96 holdout instances, exploratory intervals for quality only. Distinct profiles, not a continuous frontier. "+
             PROFILE_NOTE+" Lower search draws at c64 did not make STaR faster than SLS.","holdout",
             summary_keys="archived.reliability_quality, archived.budget",profile="archived four profiles")

    fig,axes=frame(panels=2,height=78)
    strata=summary["archived"]["mechanism"]
    npc=next(row for row in summary["paired"] if (row["cohort"],row["comparison"],row["metric"])==("holdout","STaR-NPC","reliability"))
    for index_stratum,row in enumerate(strata):
        axes[0].barh(index_stratum,100*row["contribution_to_overall_delta_R"],color="#666666" if index_stratum==0 else COLOR["FSPC"])
    axes[0].axvline(0,color=".25",lw=.7)
    axes[0].set(yticks=[0,1],yticklabels=[f"{text}\nn={row['n']:,}" for text,row in zip(("Same","Changed"),strata)],
                title="STaR − FSPC topology strata",xlabel="Contribution to pooled difference (pp)")
    axes[1].axvline(0,color=".25",lw=.7)
    axes[1].hlines(0,100*npc["lo95"],100*npc["hi95"],color=COLOR["STaR"],lw=2)
    axes[1].plot(100*npc["mean"],0,"D",color=COLOR["STaR"])
    axes[1].set(title="STaR − STaR-NPC",xlabel="Reliability difference (pp)",yticks=[],xlim=(0,100*npc["hi95"]*1.2))
    save("S04_topology_and_partial",fig,{"strata":strata,"NPC":npc},
         "Archived holdout c64. Left: post-selected ordered station-gap strata, descriptive contributions that sum to the pooled difference, "
         "not causal effects. Right: separate no-partial ablation and exploratory 95% parent-cluster interval.","holdout",summary_keys="archived.mechanism, paired")

    fig,axes=frame(panels=2,height=81)
    subset=[row for row in summary["failures"] if row["cohort"]=="holdout" and row["method"]=="STaR"]
    for ax,variant in zip(axes,("A","B")):
        offset=np.zeros(len(FAMILIES))
        for mode,shade,label in (("customer_only","#497a9e","Customer only"),("depot_only","#8b6592","Depot only"),
                                  ("joint","#3f3f3f","Joint"),("point_only","#d38a40","Point only")):
            counts=[next(row[mode] for row in subset if row["family"]==name and row["variant"]==variant) for name in FAMILIES]
            ax.barh(range(6),counts,left=offset,label=label,color=shade)
            offset+=counts
        ax.set(yticks=range(6),yticklabels=FAMILIES,title=f"Variant {variant}",xlabel="STaR nonattaining routes",xlim=(0,53))
        ax.invert_yaxis()
    fig.legend(*axes[0].get_legend_handles_labels(),loc="outside upper center",ncols=4,frameon=False)
    save("S05_failure_uncertainty",fig,subset,
         "Holdout c64 nonattainment classified by predominant scenario failure mode, with point-only routes shown separately "
         "(point estimate ≥0.95, one-sided Wilson lower bound below 0.95). Route categories are not scenario frequencies.","holdout",summary_keys="failures")

    fig,axes=frame(panels=2,height=79)
    registered=[]
    for i,method in enumerate(("CON","FSPC","STaR")):
        events=[row for row in summary["case_events"] if row["method"]==method]
        registered.extend(events)
        gap=[sum(previous["kind"]=="customer" for previous in events[:index]) for index,row in enumerate(events) if row["kind"]=="station"]
        energy=[row["charged_energy"] for row in events if row["kind"]=="station"]
        axes[0].scatter(np.array(gap)+(i-1)*.2,energy,c=COLOR[method],marker=("s","^","o")[i],label=method,s=22)
        axes[1].plot(summary["case_draws"][method]["completion_quantiles"],np.arange(21)*5,color=COLOR[method],ls=("-","--",":")[i])
    axes[0].set(xlabel="Customers served before station",ylabel="Energy added (native units)")
    axes[1].set(xlabel="Full completion (native units)",ylabel="Validation percentile")
    fig.legend(*axes[0].get_legend_handles_labels(),ncols=3,loc="outside upper center",frameon=False)
    save("S06_registered_route",fig,{"case":registered,"validation":summary["case_draws"]},
         "Registered first eligible R2-A route. Exact charging events are in the supplementary CSV; markers are offset for visibility. "
         "FSPC and STaR have overlapping completion quantiles; the case is not selected to favor STaR.","holdout",summary_keys="case_events, case_draws",custom_n=1)

    fig,(ax,)=frame(width=85,height=71)
    source=[]
    for method,style in (("SLS",":"),("FSPC","--"),("STaR","-")):
        values=[row["trials"] for row in summary["archived_candidates"] if row["profile"]=="c64" and row["method"]==method]
        xs=list(range(65))
        ecdf=[100*sum(val<=pos for val in values)/len(values) for pos in xs]
        source.append(dict(method=method,trials=xs,cumulative_pct=ecdf))
        ax.step(xs,ecdf,where="post",color=COLOR[method],ls=style,label=method)
    ax.set(xlabel="Unique plan trials per route",ylabel="Cumulative routes (%)",xlim=(0,65),ylim=(0,103))
    ax.legend(frameon=False)
    save("S08_actual_candidate_trials",fig,source,
         "Archived c64 route ECDF. All methods share a maximum of 64 unique plan trials, but FSPC's fixed-station quantity neighborhood "
         "often ends early; unhit caps are evidence consistent with exhaustion, not explicit runtime termination labels.","holdout",summary_keys="archived_candidates")
    return index
