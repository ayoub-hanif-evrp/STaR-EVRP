"""Standalone Phase 4 publication graphics and their exact plotted values."""

from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np

from star_evrp.phase4_results import FAMILIES, file_sha, write_json

COLORS = {"B0":"#555555", "B1":"#9970ab", "B2":"#a56a00", "B3":"#0072b2",
          "B4":"#008663", "STaR":"#bf4615", "STaR_no_partial":"#76548b"}
MARKERS = {"c64":"o", "c24":"s", "s8192":"^", "c64_seed2":"D"}
LABELS = {"STaR_no_partial":"No partial"}
METHODS_NOTE = "Same maximum, not same consumed work; target classification is pointwise."
PROFILE_NOTE = "c64: 64 plans / 131,072 draws; c24: 24 / 131,072; s8192: 128 / 8,192; seed 2: c64 with another search seed."
PAIR_NOTE = "Matched original exposed routes, not independent point-cloud replicates. Completion is unconditional depot return, in native units."


def frame(width=178, height=79, panels=1):
    fig, axes = plt.subplots(1, panels, figsize=(width/25.4, height/25.4), layout="constrained", squeeze=False)
    return fig, axes[0]


def figures(study, out):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 8.5,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "axes.axisbelow": True, "grid.alpha": .19, "lines.linewidth": 1.15,
                         "legend.fontsize": 7.8, "xtick.labelsize": 8, "ytick.labelsize": 8})
    summary = study.summary
    n = summary["population"][-1]["exposed"]
    items = []

    def save(folder, name, fig, data, source, message, caption, profile="c64", denominator=None):
        stem = out / "figures" / folder / name
        stem.parent.mkdir(parents=True, exist_ok=True)
        for ax in fig.axes:
            require_text = [ax.get_title(), ax.get_xlabel(), ax.get_ylabel()] + [label.get_text() for label in ax.texts]
            if any("placeholder" in label.lower() for label in require_text):
                raise ValueError(f"Placeholder axis in {name}")
        fig.savefig(stem.with_suffix(".png"), dpi=400, facecolor="white", metadata={"Software":"STaR-EVRP Phase 4"})
        width, height = [round(dim * 25.4, 1) for dim in fig.get_size_inches()]
        plt.close(fig)
        path = stem.with_suffix(".json")
        write_json(path, {"source": source, "dpi": 400, "physical_mm": [width,height], "data": data,
                          "freeze": study.lineage["freeze_digest"], "plot_source_sha256": file_sha(Path(__file__)),
                          "png_sha256": file_sha(stem.with_suffix(".png"))})
        items.append(dict(id=name, kind="figure", folder=folder, filename=stem.with_suffix(".png").relative_to(out).as_posix(),
                          profile=profile, n=n if denominator is None else denominator, message=message, source=source,
                          caption=caption, source_hash=file_sha(path)))

    primary = next(row for row in summary["paired"] if row["status"] == "confirmatory")
    parents = [row for row in summary["parent_effects"] if row["competitor"] == "B4" and row["metric"] == "reliability"]
    fig, (ax,) = frame(height=91)
    ax.axvline(0, c=".35", ls="--")
    for index, family in enumerate(FAMILIES, 1):
        sub = [row for row in parents if row["family"] == family]
        jitter = np.linspace(-.19,.19,len(sub))
        ax.scatter([100*row["mean_difference"] for row in sub], index+jitter, edgecolors="#008663", marker="o",
                   facecolors="none", s=[12 + row["paired_routes"]*.16 for row in sub], zorder=3)
    point, low, high = (primary[key]*100 for key in ("estimate","lower95","upper95"))
    ax.hlines(0, low, high, color=COLORS["STaR"], lw=2.1)
    ax.plot(point,0, "D", color=COLORS["STaR"], zorder=3)
    ax.annotate(f"{point:+.2f} [{low:.2f}, {high:.2f}]", (high,0), xytext=(6,0), textcoords="offset points", va="center")
    ax.set(yticks=range(7), yticklabels=["Pooled",*FAMILIES], ylim=(6.55,-.54),
           xlabel="STaR − B4 mean reliability (percentage points)")
    ax.margins(x=.17)
    save("main","F01_primary_parent_effects",fig,{"pooled":primary,"parents":parents}, "data/summary.json: paired, parent_effects",
         "Registered STaR–B4 effect and all 48 parent estimates.",
         f"Reliability difference in percentage points (STaR minus B4) on {n:,} initially charging-exposed CON routes at c64 (64-plan maximum). "
         "Circles show all 48 parent means (area scales with routes); the diamond shows the route-weighted estimate, with a 95% "
         "family-stratified parent-cluster percentile interval (9,999 draws, seed 312406). Only the pooled reliability contrast is confirmatory.")

    overall = summary["overall"]
    fig, axes = frame(height=87, panels=2)
    coords = np.arange(len(overall))
    labels = [LABELS.get(row["method"],row["method"]) for row in overall]
    axes[0].barh(coords,[100*row["mean_R"] for row in overall],color=[COLORS[row["method"]] for row in overall])
    for index, row in enumerate(overall):
        axes[0].text(100*row["mean_R"]-1.4,index,f'{100*row["mean_R"]:.2f}%',ha="right",va="center",color="white")
    for index,row in enumerate(overall):
        attained=row["lower_bound_attained"]
        axes[1].barh(index,100*attained/n,color=COLORS[row["method"]])
        axes[1].text(100*attained/n-1.4,index,f"{attained:,}/{n:,}",ha="right",va="center",color="white")
    for ax in axes:
        ax.set(xlim=(0,100),ylim=(len(overall)-.45,-.55))
    axes[0].set(yticks=coords,yticklabels=labels,xlabel="(a) Mean validation reliability (%)")
    axes[1].set(yticks=[],xlabel="(b) Lower-bound attainment (%)")
    save("main","F02_method_reliability_attainment",fig,overall,"data/summary.json: overall","Mean reliability and attainment are different measures.",
         f"Seven methods paired on the same {n:,} exposed c64 routes. Mean empirical reliability uses 10,000 held-out draws per plan; "
         "attainment counts routes whose one-sided 95% Wilson lower limit is at least 0.95. Counts are not simultaneous guarantees.")

    fig, axes = frame(height=77, panels=2)
    source = [row for row in summary["pairs"] if row["profile"] == "c64"]
    for ax, control in zip(axes, ("B4","B3")):
        pair = [row for row in source if row["competitor"] == control]
        times = [row["delta_full_completion"] for row in pair]
        gains = [100*row["delta_reliability"] for row in pair]
        ax.scatter(times,gains, s=9, alpha=.29, color=COLORS[control], linewidth=0)
        ax.axvline(0,color=".2",lw=.7); ax.axhline(0,color=".2",lw=.7)
        ax.set(title=f"STaR − {control}", xlabel="Δ full completion (native units)",
               ylabel="Δ reliability (percentage points)",ylim=(-105,105))
        ax.annotate("Better reliability, shorter route",(.035,.96),xycoords="axes fraction",va="top",fontsize=7.6)
    save("main","F03_paired_reliability_completion",fig,source,"data/paired_routes.csv (c64)","Per-route gains and losses are visible.",
         f"Each panel represents {n:,} matched original c64 routes. Positive reliability (percentage points) and negative completion favor STaR. "
         "Dots are empirical route estimates, not confidence intervals; overlapping points remain possible. " + PAIR_NOTE)

    budgets = {(row["profile"],row["method"]):row for row in summary["budget"]}
    for name, work, xlabel, message in (
        ("F04_scenario_work","search_scenarios","Mean incremental search draws",
         "Different caps and seeds shown as discrete comparisons."),
        ("F05_wall_runtime","search_wall_ms","Mean measured search wall time (ms)",
         "At c64 STaR spends more wall time than B3; B4 is faster."),
    ):
        fig, (ax,) = frame(height=81)
        inputs = []
        for row in summary["reliability_quality"]:
            method,profile = row["method"],row["profile"]
            here = budgets[profile,method][work]
            inputs.append({**row,work:here})
            ax.vlines(here,100*row["lower95"],100*row["upper95"], colors=COLORS[method], lw=.9)
            ax.plot(here,100*row["mean_R"], marker=MARKERS[profile], color=COLORS[method],
                    linestyle="none", ms=6, mfc="none" if profile=="c64_seed2" else COLORS[method])
        handles = [Line2D([],[],marker="o",ls="none",color=COLORS[m],label=m) for m in ("B3","B4","STaR")]
        profiles = [Line2D([],[],marker=marker,ls="none",color=".3",label=p.replace("c64_seed2","c64 seed 2"),
                           mfc="none" if p=="c64_seed2" else ".3") for p,marker in MARKERS.items()]
        fig.legend(handles=handles+profiles,ncols=7,loc="outside upper center",frameon=False,columnspacing=.95,handletextpad=.4)
        ax.set(xlabel=xlabel,ylabel="Mean validation reliability (%)",
               ylim=(100*min(row["lower95"] for row in inputs)-.22,100*max(row["upper95"] for row in inputs)+.22))
        if work == "search_scenarios":
            ax.xaxis.set_major_formatter(FuncFormatter(lambda val,_: f"{val:,.0f}"))
        save("main",name,fig,inputs,"data/summary.json: budget, reliability_quality",message,
             f"Matched quality and {xlabel.lower()} for {n:,} exposed routes per method/profile; vertical intervals are descriptive "
             "95% family-stratified parent-cluster bootstrap intervals. No interpolated frontier. " + PROFILE_NOTE +
             (" Elapsed time is measured under six workers, excludes final validation and includes search overhead; wall guard is cooperative."
              if work=="search_wall_ms" else " Draw savings do not imply elapsed savings."), "all profiles")

    fig, axes = frame(height=86,panels=2)
    cells = {(row["family"],row["variant"],row["method"]):row for row in summary["family_variant"]}
    methods = ("B0","B3","B4","STaR")
    selected = []
    for ax,variant in zip(axes,("A","B")):
        data=np.array([[100*cells[f,variant,m]["lower_bound_attained"]/cells[f,variant,m]["n"] for m in methods] for f in FAMILIES])
        picture=ax.imshow(data,cmap="cividis",norm=Normalize(0,100),aspect="auto")
        for ii,family in enumerate(FAMILIES):
            for jj,method in enumerate(methods):
                row=cells[family,variant,method]
                selected.append(row)
                ax.text(jj,ii,f"{row['lower_bound_attained']}\n{data[ii,jj]:.0f}%",ha="center",va="center",
                        color="white" if data[ii,jj]<53 else "black",linespacing=1.05)
        ax.set(xticks=range(4),xticklabels=methods,yticks=range(6),
               yticklabels=[f"{f} ({cells[f,variant,'B0']['n']})" for f in FAMILIES],title=f"Variant {variant}")
        ax.grid(False)
    fig.colorbar(picture,ax=list(axes), shrink=.82,label="Lower-bound attainment (%)")
    save("main","F06_family_variant_attainment",fig,selected,"data/summary.json: family_variant",
         "The hard R2 and RC2 cases remain visible with unequal denominators.",
         "Family × variant c64 attainment for B0, B3, B4, and STaR. Row labels give eligible routes, and cells give attained "
         "count (top) and rounded percent (bottom). A/B are sibling variants, not independent parents. One-sided Wilson rule, descriptive breakdown.")

    fig, axes = frame(height=72,panels=2)
    mech=summary["mechanism"]
    full=next(row for row in summary["paired"] if row["profile"]=="c64" and row["competitor"]=="STaR_no_partial" and row["metric"]=="reliability")
    for index,row in enumerate(mech):
        axes[0].barh(index,100*row["contribution_to_overall_delta_R"],color=["#666666","#008663"][index])
    axes[0].axvline(0,c=".3",lw=.7)
    axes[0].set(yticks=[0,1],yticklabels=[f"{label}\n(n={row['n']:,})" for label,row in zip(("Same","Changed"),mech)],
                xlabel="Contribution to pooled Δ (pp)",title="(a) STaR − B4: station topology")
    point,low,high=(100*full[key] for key in ("estimate","lower95","upper95"))
    axes[1].axvline(0,c=".3",lw=.7)
    axes[1].hlines(0,low,high,color=COLORS["STaR"],lw=2)
    axes[1].plot(point,0,"D",color=COLORS["STaR"])
    axes[1].text(point,.16,f"{point:+.2f} [{low:.2f}, {high:.2f}]",ha="center",va="bottom")
    axes[1].set(yticks=[],ylim=(-.5,.52),xlim=(0,high*1.20),xlabel="Δ reliability (percentage points)",
                title="(b) STaR − no partial")
    save("main","F07_topology_and_ablation",fig,{"mechanism":mech,"ablation":full},"data/summary.json: mechanism, paired",
         "Observed topology strata and the separate charge-quantity ablation.",
         f"(a) For the same {n:,} c64 route pairs, split by the exact ordered (customer gap, station ID) list. Weighted stratum contributions "
         "sum arithmetically to the primary point estimate but are post-selection, not independent causal effects. "
         "(b) Separate exploratory c64 no-partial ablation, with a pointwise 95% parent-cluster interval.")

    fig, (ax,) = frame(height=76)
    stress=summary["robustness"]
    modes=("scale125","sigma125","copula035")
    labs=("Wait scale ×1.25","Log σ ×1.25","Normal copula ρ = 0.35")
    for index,method in enumerate(("B0","B3","B4","STaR")):
        values=[next(row for row in stress if (row["stress"],row["method"])==(mode,method)) for mode in modes]
        pos=np.arange(3)+(index-1.5)*.19
        ax.bar(pos,[100*row["lower_bound_attained"]/row["n"] for row in values],width=.18,color=COLORS[method],label=method)
    ax.set(xticks=range(3),xticklabels=labs,ylabel="Lower-bound attainment (%)",ylim=(0,103))
    fig.legend(ncols=4,frameon=False,loc="outside upper center")
    save("main","F08_fixed_plan_robustness",fig,stress,"data/summary.json: robustness",
         "Synthetic perturbations of saved plans; no reoptimization.",
         f"Lower-bound attainment on {n:,} initially exposed routes per method under three separate synthetic waiting-model stresses. "
         "Plans are fixed at c64, validation uses 10,000 draws per plan/model. The Gaussian copula preserves the marginal distributions. "
         "The results are descriptive and are not calibration against real station data.")

    fig, axes = frame(height=77,panels=2)
    key = tuple(summary["example"])
    example = {}
    for method in ("B0","B4","STaR"):
        row=study.rows["c64", *key, method]
        plan=study.plans["c64", *key, method]
        gaps=[gap for gap,_ in plan["station_positions"]]
        energies=[item[4] for item in plan["events"] if item[1]=="station"]
        example[method]={"gaps":gaps,"energies":energies,"validation":row["validation"],"events":plan["events"]}
        index=("B0","B4","STaR").index(method)
        axes[0].scatter(np.array(gaps)+(index-1)*.18,energies,marker=("s","^","o")[index],
                        s=27,color=COLORS[method],label=method)
        axes[1].plot(row["validation"]["completion_quantiles"],np.arange(21)*5, color=COLORS[method],
                     ls=("-","--",":")[index],label=method)
    axes[0].set(xlabel="Customers served before station",ylabel="Energy added (native units)")
    axes[1].set(xlabel="Full completion (native time units)",ylabel="Validation percentile")
    fig.legend(*axes[0].get_legend_handles_labels(), ncols=3, frameon=False, loc="outside upper center")
    save("supplementary","S01_registered_R2_route",fig,example,"data/summary.json: case_routes; saved c64 plans and validation",
         "Charging schedules and full completion for the frozen illustrative route.",
         "Preregistered example R2_10_2/A/route 0, the first eligible R2-A route by parent and ID. "
         "Markers are horizontally offset only to avoid overlap. The B4 and STaR completion curves coincide at this resolution. "
         "Exact stops, customer/depot timing, and charge amounts are supplied in the supplementary case table.",denominator=1)

    fig, axes = frame(height=76,panels=2)
    near=[]
    for ax,method in zip(axes,("B3","STaR")):
        samples=sorted((row for row in study.rows.values() if row["profile"]=="c64" and row["method"]==method
                       and abs(row["validation"]["reliability"]-.95)<=.015),
                       key=lambda r:(r["validation"]["reliability"],r["parent"],r["variant"],r["route"]))
        coords=np.arange(len(samples))
        data=np.array([[100*row["validation"]["reliability"],*[100*limit for limit in row["validation"]["wilson95_two_sided"]]]
                       for row in samples])
        near.extend(dict(method=method,parent=row["parent"],variant=row["variant"],route=row["route"],
                         validation=row["validation"]) for row in samples)
        ax.vlines(coords,data[:,1],data[:,2],color=COLORS[method],lw=.8)
        ax.scatter(coords,data[:,0],c=COLORS[method],s=9)
        ax.axhline(95,c=".25",ls="--",lw=.8)
        ax.set(title=f"{method}: {len(samples)} near-target routes",xlabel="Route rank by estimated reliability",
               ylabel="Reliability (%) and two-sided 95% CI")
    save("supplementary","S02_near_target_Wilson",fig,near,"raw/c64 validation; coded subset ±1.5 pp",
         "Sampling uncertainty near 0.95, not a joint classification guarantee.",
         "Post-hoc diagnostic: c64 route estimates within ±1.5 percentage points of 0.95, using two-sided 95% Wilson intervals. "
         "These are not the one-sided lower bounds used for attainment.",denominator=len(near))

    fig,(ax,)=frame(width=85,height=68)
    work_source=[]
    for method,style in (("B4","--"),("B3",":"),("STaR","-")):
        counts=Counter(row["work"]["candidates_evaluated"] for row in study.rows.values() if
                       row["profile"]=="c64" and row["method"]==method)
        vals=list(range(65))
        pct=np.cumsum([counts[count] for count in vals])*100/n
        ax.step(vals,pct,where="post",color=COLORS[method],ls=style,label=method)
        work_source.append({"method":method,"trials":vals,"cumulative_pct":pct.tolist()})
    ax.set(xlabel="Distinct plan trials per route",ylabel="Cumulative routes (%)",xlim=(0,65),ylim=(0,103))
    ax.legend(frameon=False)
    save("supplementary","S03_actual_candidate_work",fig,work_source,"raw/c64 search work; data/summary.json: work",
         "Identical maximum of 64 does not mean identical actual work.",
         f"Post-hoc empirical CDFs of distinct candidate trials on {n:,} c64 routes per method. Deterministically rejected plans "
         "count toward trials. B4 restricts the neighborhood; this does not identify the best attainable quantity-only result.")
    return items
