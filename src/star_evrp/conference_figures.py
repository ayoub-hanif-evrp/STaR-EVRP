"""Shared style and editable, deterministic conference artwork."""

from collections import Counter
from datetime import datetime, timezone
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.ticker import MultipleLocator
import numpy as np

from star_evrp.phase4_results import file_sha
from star_evrp.phase6_archive import write_bytes, write_csv, write_json

TEAL, SLATE, AMBER, BLUE, NAVY = "#0D9488","#64748B","#D97706","#2563EB","#1E293B"
GRID, PALE, TOP = "#E3E9EF","#F1F5F9","#ECF7F6"
STEMS = ("Fig01_spatial_charging_repair","Fig02_star_framework","Fig03_paired_reliability",
         "Fig04_charging_complexity","Fig05_quality_simulation_effort")
STYLE = {"font.family":"DejaVu Sans","font.size":8.3,"font.weight":"normal","axes.labelcolor":NAVY,
         "text.color":NAVY,"axes.titlesize":9.4,"axes.titleweight":"bold","xtick.labelsize":8,"ytick.labelsize":8,
         "xtick.color":NAVY,"ytick.color":NAVY,"axes.edgecolor":SLATE,"axes.linewidth":.65,"axes.spines.top":False,
         "axes.spines.right":False,"axes.axisbelow":True,"xtick.direction":"out","ytick.direction":"out",
         "xtick.major.size":2.8,"ytick.major.size":2.8,"xtick.major.width":.6,"ytick.major.width":.6,
         "figure.facecolor":"white","savefig.facecolor":"white","savefig.edgecolor":"white",
         "mathtext.fontset":"dejavusans","pdf.fonttype":42,"svg.fonttype":"none","svg.hashsalt":"star-conference-v1"}


def heading(ax, letter, text):
    ax.set_title(f"({letter})  {text}",loc="left",pad=8)


def baseline(ax):
    ax.axvline(0,color=SLATE,lw=.8,ls=(0,(2,2)),zorder=1.5)


def grid(ax, axis):
    ax.grid(axis=axis,color=GRID,lw=.58)


def new_figure(width,height):
    return plt.figure(figsize=(width/25.4,height/25.4))


def arrow_leg(ax,left,right,color):
    x,y=left["x"],left["y"]
    vx,vy=right["x"]-x,right["y"]-y
    if vx*vx+vy*vy<1600:
        return
    a=(x+vx*.54,y+vy*.54)
    b=(x+vx*.61,y+vy*.61)
    ax.annotate("",xy=b,xytext=a,arrowprops=dict(arrowstyle="-|>",color=color,lw=.85,mutation_scale=7,
                 shrinkA=0,shrinkB=0),zorder=4)


def spatial(data,width):
    fig=new_figure(width,98)
    axes=fig.subplots(1,3,gridspec_kw={"width_ratios":[1,1,1]})
    fig.subplots_adjust(left=.08,right=.983,top=.88,bottom=.30,wspace=.33)
    world,orig,star=axes
    maps={k:[s for s in data["map_stops"] if s["plan"]==k] for k in ("CON","STaR")}
    types={"customer":("o",BLUE),"station":("s",AMBER),"depot":("D",NAVY)}
    chosen=data["map_selection"]["chosen"]
    label_positions=(
        {("CON",1253):(11,334),("STaR",1248):(171,478)}
        if (chosen["parent"],chosen["variant"],chosen["route"])==("C1_10_3","A",106) else {}
    )
    for tag in types:
        base=[r for r in data["map_nodes"] if r["type"]==tag]
        world.scatter([r["x"] for r in base],[r["y"] for r in base],
                      s={"customer":3.9,"station":8,"depot":24}[tag],marker=types[tag][0],
                      c={"customer":"#BFCAD8","station":"#E0A760","depot":NAVY}[tag],edgecolors="none",
                      zorder=3 if tag=="depot" else 1)
    world.plot([s["x"] for s in maps["CON"]],[s["y"] for s in maps["CON"]],color=BLUE,lw=1.05,zorder=3)
    # Same spatial limits for both detail panels, with uniform padding around the ordered stops.
    xy=[(s["x"],s["y"]) for s in data["map_stops"]]
    xmin,ymin=np.min(xy,axis=0)-25
    xmax,ymax=np.max(xy,axis=0)+25
    limits=[float(v) for v in (xmin,xmax,ymin,ymax)]
    world.add_patch(Rectangle((xmin,ymin),xmax-xmin,ymax-ymin,facecolor="none",edgecolor=BLUE,
                              lw=.9,ls=(0,(3,2)),zorder=4))
    world.annotate("Detail",xy=(xmax,min(ymax,495)),xytext=(6,-13),textcoords="offset points",
                   color=NAVY,fontsize=7.1,arrowprops=dict(arrowstyle="-",color=SLATE,lw=.55),zorder=5)
    all_x=[p["x"] for p in data["map_nodes"]]; all_y=[p["y"] for p in data["map_nodes"]]
    world.set(xlim=(min(min(all_x),xmin)-9,max(max(all_x),xmax)+9),
              ylim=(min(min(all_y),ymin)-9,max(max(all_y),ymax)+9))
    for ax,label,method,color in ((orig,"Original plan","CON",SLATE),(star,"STaR repair","STaR",TEAL)):
        path=maps[method]
        other=maps["CON" if method=="STaR" else "STaR"]
        other_stations={r["node"] for r in other if r["type"]=="station"}
        ax.plot([s["x"] for s in path],[s["y"] for s in path],color=color,lw=1.22,
                linestyle="-" if method=="STaR" else (0,(3,2)),zorder=2)
        for left,right in zip(path,path[1:]):
            arrow_leg(ax,left,right,color)
        stations=Counter(s["node"] for s in path if s["type"]=="station")
        customer=0
        for s in path[:-1]:
            marker,fill=types[s["type"]]
            ax.scatter(s["x"],s["y"],marker=marker,s=29 if s["type"]=="station" else 23,c=fill,
                       edgecolors="white",linewidths=.56,zorder=6)
            if s["type"]=="customer":
                customer+=1
                ax.annotate(str(customer),(s["x"],s["y"]),xytext=(4,4),textcoords="offset points",fontsize=7.0,zorder=9)
            if s["type"]=="station":
                change="Added" if method=="STaR" else "Removed"
                qualifier=change if s["node"] not in other_stations else "Visit"
                repeated=f' / stop {s["index"]}' if stations[s["node"]]>1 else ""
                text=f'{qualifier} {s["node"]}{repeated}\nCharge {s["charged"]:.1f}'
                placement=label_positions.get((method,s["node"]))
                ax.annotate(text,(s["x"],s["y"]),xytext=placement or ((11,-20) if method=="CON" else (-15,-12)),
                            ha="left" if method=="CON" else "right",va="top",textcoords="data" if placement else "offset points",
                            arrowprops=dict(arrowstyle="-",color=SLATE,lw=.6),fontsize=7.3,linespacing=1.22,zorder=9)
        ax.set(xlim=(xmin,xmax),ylim=(ymin,ymax))
        heading(ax,"b" if method=="CON" else "c",label)
    heading(world,"a","Benchmark instance")
    for ax in axes:
        ax.set(xlabel="x",ylabel="y",aspect="equal")
        ax.xaxis.set_major_locator(MultipleLocator(100 if ax is not world else 200))
        ax.yaxis.set_major_locator(MultipleLocator(100 if ax is not world else 200))
        ax.xaxis.labelpad=1
        ax.yaxis.labelpad=0
    fig.canvas.draw()
    s=chosen
    pos=world.get_position()
    fig.text((pos.x0+pos.x1)/2,.183,f'{s["parent"]} / {s["variant"]} · route {s["route"]}',ha="center",size=8.3,weight="bold")
    fig.text((pos.x0+pos.x1)/2,.134,"Synthetic benchmark coordinates",ha="center",size=7.3)
    for ax,row in zip((orig,star),data["map_metrics"],strict=True):
        bounds=ax.get_position()
        mid=(bounds.x0+bounds.x1)/2
        fig.text(mid,.181,f'Estimated R  {100*row["reliability"]:.2f}%',ha="center",size=8.6,weight="bold")
        att="attains" if row["attained"] else "below target"
        fig.text(mid,.133,f'Return {row["completion"]:,.2f} · Wilson {att}',ha="center",size=7.2)
    handles=[Line2D([],[],label=k,marker=m,ls="",color=c,markersize=4.6) for k,(m,c) in
             (("Customer",types["customer"]),("Station",types["station"]),("Depot",types["depot"]))]
    handles.extend([Line2D([],[],label="Original path",color=SLATE,ls=(0,(3,2))),
                    Line2D([],[],label="Repaired path",color=TEAL)])
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.51,.027),ncol=5,frameon=False,
               fontsize=7.8,columnspacing=1.45,handlelength=1.5)
    return fig,dict(selection=s,zoom_limits=limits,aspect="equal, equal limits in b/c",map_nodes=data["map_nodes"],
                    ordered_stops=data["map_stops"],metrics=data["map_metrics"])


FLOW = {
    "nodes": [
        {"id":"initialize","heading":"Start from CON","lines":["Feasible ordered plan","Station laws, target, caps","Trace + score on 512 draws"],
         "source":"competitive_search.py:188–224; route_evaluator.py:56–75, 87–107"},
        {"id":"rank","heading":"Rank visits and gaps","lines":["Lowest upper bound first","Prioritize gaps near the","most critical station"],
         "source":"competitive_search.py:150–158; timing.py:73–92"},
        {"id":"propose","heading":"Interleave moves","lines":["Adjust or transfer charge","Remove, replace, relocate","or insert, then allocate"],
         "source":"competitive_search.py:48–169, 225–249; charge_plan.py:49–73"},
        {"id":"feasible","heading":"Check candidate","lines":["Skip duplicate plans","Require energy feasibility","and zero-wait timing"],
         "source":"competitive_search.py:235–250; route_evaluator.py:56–74; deterministic_simulator.py:166–282"},
        {"id":"screen","heading":"Analytical screen","lines":["If incumbent attains:","reject when marginal bound","falls below target¹"],
         "source":"competitive_search.py:251–258; timing.py:73–92"},
        {"id":"prefix","heading":"Prefix evaluation","lines":["Score a 128-draw prefix","Prune if it cannot improve","Otherwise extend to 512"],
         "source":"competitive_search.py:259–269; route_evaluator.py:76–107"},
        {"id":"score","heading":"Compare full scores","lines":["Favor target attainment","Attain: min return, max R","Below: max R, min return"],
         "source":"competitive_search.py:269–277; search_common.py:22–28"},
        {"id":"return","heading":"Return incumbent","lines":["When proposals end with","no improvement, or a","cooperative guard stops"],
         "source":"competitive_search.py:225–234, 270–279; budget.py:35–48"},
    ],
    "edges": [
        ["initialize","rank","initial feasible trace and full score"],
        ["rank","propose","critical visits and gaps"],
        ["propose","feasible","next unique plan within guards"],
        ["feasible","screen","valid deterministic trace"],
        ["screen","prefix","bypass if incumbent below empirical target, or screen passes"],
        ["prefix","score","optimistic score strictly beats incumbent and full tape extension completes"],
        ["score","rank","strict improvement before wall guard; update incumbent and restart"],
        ["feasible","propose","invalid or duplicate (common retry line)"],
        ["screen","propose","model reliability reject (common retry line)"],
        ["prefix","propose","bound or budget reject (common retry line)"],
        ["score","propose","no strict gain (common retry line)"],
        ["propose","return","no remaining improving proposal or cooperative stop"],
    ],
    "score":{"attaining":["minimize unconditional mean completion","maximize reliability"],
             "below_target":["maximize reliability","minimize unconditional mean completion"],"strict":True},
    "bounds":{"target":0.95,"screen_tolerance":1e-12,"prefix_completion_cushion":1e-8,
              "R_U":"(m + S - k) / S","C_L":"(C_k + (S - k) C_0) / S","prefix":128,"full":512},
    "validation":{"source":"phase3.py:287–345","independent_draws":10000,"feedback":False},
}


def framework(width):
    fig=new_figure(width,102)
    ax=fig.add_axes((.024,.033,.952,.934))
    ax.set_axis_off()
    ax.set(xlim=(0,1),ylim=(0,1))
    xval=(.008,.255,.502,.749)
    w,h=.228,.236
    top,bottom=.691,.329
    positions={n["id"]:(xval[i],top) for i,n in enumerate(FLOW["nodes"][:4])}
    positions.update({n["id"]:(xval[3-i],bottom) for i,n in enumerate(FLOW["nodes"][4:])})
    for node in FLOW["nodes"]:
        x,y=positions[node["id"]]
        fill=TOP if node["id"] in ("rank","prefix","score") else PALE
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.003,rounding_size=.015",
                                   ec="#CBD5E1",fc=fill,lw=.75,zorder=1))
        ax.text(x+.011,y+h-.047,node["heading"],va="top",fontsize=8.8,weight="bold",zorder=3)
        ax.text(x+.011,y+h-.103,"\n".join(node["lines"]),va="top",fontsize=7.45,linespacing=1.30,zorder=3)

    def flow(start,end,color=SLATE,lw=.9,rad=0):
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle="-|>",mutation_scale=8,linewidth=lw,color=color,
                                    shrinkA=0,shrinkB=0,connectionstyle=f"arc3,rad={rad}",zorder=5))

    for i in range(3):
        flow((xval[i]+w+.004,top+h/2),(xval[i+1]-.004,top+h/2))
    flow((xval[3]+w/2,top-.006),(xval[3]+w/2,bottom+h+.006))
    for i in (3,2):
        flow((xval[i]-.004,bottom+h/2),(xval[i-1]+w+.004,bottom+h/2))
    flow((xval[1]-.004,bottom+h/2),(xval[0]+w+.004,bottom+h/2))
    ax.text(xval[3]+w/2+.013,.627,"Feasible",va="center",fontsize=7.1,color=SLATE)
    flow((xval[1]+.055,bottom+h+.006),(xval[1]+.055,top-.006),TEAL,lw=1.25)
    ax.text(xval[1]+.068,.630,"Strict gain: update and restart",va="center",fontsize=7.3)
    # The shared reject branch returns around the outside, away from the main flow arrows.
    path=[(xval[1]+w/2,bottom-.007),(xval[1]+w/2,.278),(.992,.278),(.992,.973),(xval[2]+w/2,.973)]
    ax.plot(*zip(*path),color=SLATE,lw=.66,dashes=(2.5,2),zorder=4)
    ax.plot([xval[3]+w+.004,.992],[top+h/2,top+h/2],color=SLATE,lw=.66,dashes=(2.5,2),zorder=4)
    for i in (2,3):
        x=xval[i]+w/2
        ax.plot([x,x],[bottom-.007,.278],color=SLATE,lw=.66,dashes=(2.5,2),zorder=4)
    flow((xval[2]+w/2,.975),(xval[2]+w/2,top+h+.006),lw=.7)
    ax.text(.37,.230,"Rejected or no strict gain: try the next proposal while guards permit.",
            fontsize=7.7,va="center")
    ax.text(.013,.139,"¹ True-reliability bound. Bypass if the incumbent misses the empirical target.",
            fontsize=7.3,va="center",color=NAVY)
    ax.text(.013,.072,"Shared ordinal optimization tape. Independent 10,000-draw validation follows search.",
            fontsize=7.3,va="center",color=NAVY)
    return fig,FLOW


def interval(ax,y,estimate,low,high,*,color,marker="o",filled=True):
    ax.plot([low,high],[y,y],color=color,lw=1.3,solid_capstyle="round",zorder=2)
    ax.plot(estimate,y,marker=marker,linestyle="",markersize=5.3,mfc=color if filled else "white",
            mec=color,mew=1.15,zorder=3)


def paired_reliability(data,width):
    fig=new_figure(width,79)
    plot,counts=fig.subplots(1,2,gridspec_kw={"width_ratios":[1.14,.9]})
    fig.subplots_adjust(left=.233,right=.966,bottom=.20,top=.82,wspace=.37)
    rows=data["paired"]
    baseline(plot); grid(plot,"x")
    for i,r in enumerate(rows):
        interval(plot,1-i,r["mean_pp"],r["lo95_pp"],r["hi95_pp"],
                 color=TEAL if i==0 else SLATE,marker="o" if i==0 else "s",filled=i==0)
        plot.annotate(f'{r["mean_pp"]:+.2f} [{r["lo95_pp"]:+.2f}, {r["hi95_pp"]:+.2f}]',
                      (r["mean_pp"],1-i),xytext=(0,13),textcoords="offset points",
                      ha="center" if i==0 else "left",size=7.55)
    plot.set_yticks([1,0],["Fixed-station repair\nConfirmatory","Scenario search\nExploratory"])
    plot.tick_params(axis="y",length=0,pad=7)
    plot.spines["left"].set_visible(False)
    plot.set(xlim=(-.12,1.93),ylim=(-.35,1.51),xlabel="STaR minus comparator (pp)")
    plot.xaxis.set_major_locator(MultipleLocator(.5))
    heading(plot,"a","Paired route reliability")
    heading(counts,"b","Observed directions")
    counts.set(xlim=(0,100),ylim=(0,1))
    counts.axis("off")
    begin=0
    direct=rows[0]
    items=[]
    for i,(desc,c) in enumerate((("Higher",TEAL),("Equal","#CBD5E1"),("Lower",AMBER))):
        n=direct[desc.lower()]
        ratio=100*n/direct["n"]
        counts.barh(.84,ratio,left=begin,height=.15,color=c,edgecolor="white",linewidth=.45)
        begin+=ratio
        y=.58-i*.21
        counts.scatter(3,y,marker="s",c=c,s=23,zorder=3)
        counts.text(9,y,desc,va="center")
        counts.text(97,y,f"{n:,}  ({ratio:.2f}%)",va="center",ha="right",fontsize=8.0)
        items.append(dict(direction=desc,count=n,percent=ratio))
    return fig,dict(effects=rows,rendered_directions=items)


def charging_complexity(data,width):
    fig=new_figure(width,87)
    left,right=fig.subplots(1,2,sharey=True,gridspec_kw={"width_ratios":[1.16,1]})
    fig.subplots_adjust(left=.225,right=.967,top=.82,bottom=.26,wspace=.21)
    rows=data["complexity"]
    ypos=[2,1,0]
    labels=[f'{r["bin"]} visit{"s" if r["bin"]!="1" else ""}\n{r["n"]:,} routes · {r["parents"]} parents' for r in rows]
    baseline(left); grid(left,"x"); grid(right,"x")
    for y,r in zip(ypos,rows,strict=True):
        interval(left,y,r["mean_pp"],r["lo95_pp"],r["hi95_pp"],color=TEAL)
        right.barh(y,r["nonattainment_pct"],height=.34,color=AMBER,alpha=.88)
        right.plot(r["nonattainment_pct"],y,"s",mec=AMBER,mfc="white",ms=3.5,mew=.8,zorder=3)
        right.annotate(f'{r["nonattained"]}/{r["n"]:,}',(r["nonattainment_pct"],y),xytext=(5,0),
                       textcoords="offset points",ha="left",va="center",fontsize=7.75)
    left.set_yticks(ypos,labels)
    left.set(xlim=(-.22,6.05),ylim=(-.47,2.47),xlabel="STaR minus fixed-station repair (pp)")
    right.set(xlim=(0,23.2),xlabel="STaR Wilson nonattainment (%)")
    left.xaxis.set_major_locator(MultipleLocator(2))
    right.xaxis.set_major_locator(MultipleLocator(5))
    left.tick_params(axis="y",length=0,pad=8)
    right.tick_params(axis="y",length=0)
    left.spines["left"].set_visible(False)
    heading(left,"a","Reliability effect")
    heading(right,"b","Remaining nonattainment")
    notes=data["complexity_notes"]
    fig.text(.223,.073,f'3+ visits: {notes["three_share"]:.1f}% of exposed routes and {notes["net_share"]:.1f}% of the net reliability gain.',
             size=8.0,weight="bold")
    return fig,dict(bins=rows,annotations=notes)


def effort(data,width):
    fig=new_figure(width,92)
    left,right=fig.subplots(1,2,gridspec_kw={"width_ratios":[1.24,1]})
    fig.subplots_adjust(left=.105,right=.968,top=.83,bottom=.25,wspace=.43)
    points=data["timing"]
    colors={"STaR":TEAL,"SLS":SLATE}
    markers={"STaR":"o","SLS":"s"}
    for r in points:
        method=r["method"]
        guard=r["guard_ms"]
        x=r["draws"]/1000
        y=r["reliability_pct"]
        primary=guard==50
        left.plot(x,y,marker=markers[method],ls="",color=colors[method],mfc="white" if primary else colors[method],
                  mew=1.4 if primary else .9,ms=6.4 if primary else 5)
        dx,dy=((-3,8) if primary else (4,7)) if method=="STaR" else (
            (-5,8) if guard==100 else (4,-11) if guard==50 else (4,6))
        left.annotate(f"{guard} ms",(x,y),xytext=(dx,dy),textcoords="offset points",ha="right" if dx<0 else "left",
                      fontsize=7.2)
    left.set(xlim=(9,45.5),ylim=(98.6,100.06),xlabel="Mean search draws (thousands)",ylabel="Mean reliability (%)")
    left.yaxis.set_major_locator(MultipleLocator(.4))
    left.xaxis.set_major_locator(MultipleLocator(10))
    grid(left,"y")
    heading(left,"a","Quality and simulation work")
    baseline(right); grid(right,"x")
    results=[r for r in data["timing_effects"] if r["metric"]=="R_pp"]
    for y,r in zip((2,1,0),results,strict=True):
        interval(right,y,r["mean"],r["lo95"],r["hi95"],color=TEAL if r["guard_ms"]==50 else SLATE,filled=r["guard_ms"]!=50)
    right.set_yticks([2,1,0],["20 ms","50 ms","100 ms"])
    right.set(xlim=(-.68,1.27),ylim=(-.48,2.48),xlabel="STaR minus scenario search (pp)")
    right.xaxis.set_major_locator(MultipleLocator(.5))
    right.tick_params(axis="y",length=0,pad=6)
    right.spines["left"].set_visible(False)
    heading(right,"b","Paired reliability")
    handles=[Line2D([],[],ls="",marker=markers[m],color=colors[m],markersize=5,
                    label="STaR" if m=="STaR" else "Scenario search") for m in ("STaR","SLS")]
    fig.legend(handles=handles,ncol=2,frameon=False,loc="lower left",bbox_to_anchor=(.103,.042),
               fontsize=7.8,handlelength=.7,columnspacing=1.2)
    note=data["timing_notes"]
    fig.text(.565,.075,f'{note["relative_reduction_pct"]:.2f}% fewer search draws at 50 ms',size=8.1,weight="bold")
    return fig,dict(plotted_points=points,paired_intervals=results,notes=note,absolute_rate_axis_focused=True)


def draw(root,out,data,width,captions):
    with plt.rc_context(STYLE):
        plots=((spatial,(data,width)),(framework,(width,)),(paired_reliability,(data,width)),
               (charging_complexity,(data,width)),(effort,(data,width)))
        for name,(fn,args) in zip(STEMS,plots,strict=True):
            fig,values=fn(*args)
            for extension,meta in (
                ("png",{"Software":"STaR-EVRP / Matplotlib"}),
                ("pdf",{"Creator":"STaR-EVRP / Matplotlib","Title":name,"CreationDate":datetime(2000,1,1,tzinfo=timezone.utc),
                        "ModDate":datetime(2000,1,1,tzinfo=timezone.utc)}),
                ("svg",{"Creator":"STaR-EVRP / Matplotlib","Date":None,"Title":name}),
            ):
                buffer=BytesIO()
                fig.savefig(buffer,format=extension,dpi=400,metadata=meta,facecolor="white")
                write_bytes(out/"figures"/f"{name}.{extension}",buffer.getvalue())
            dim=[round(v*25.4,4) for v in fig.get_size_inches()]
            plt.close(fig)
            files={ext:file_sha(out/"figures"/f"{name}.{ext}") for ext in ("png","pdf","svg")}
            write_json(out/"figures"/f"{name}.json",dict(stem=name,physical_mm=dim,dpi=400,formats_sha256=files,
                caption=captions[name],plotted=values,source_sha256=data["sources"][name[:5]],
                plot_source_sha256=file_sha(root/"src/star_evrp/conference_figures.py"),font="DejaVu Sans"))
    write_json(out/"data/Fig02_flow.json",FLOW)
    write_csv(out/"data/Fig02_flow_nodes.csv",[dict(id=n["id"],label=n["heading"],lines=" | ".join(n["lines"]),source=n["source"]) for n in FLOW["nodes"]])
    write_csv(out/"data/Fig02_flow_edges.csv",[dict(zip(("from","to","condition"),e,strict=True)) for e in FLOW["edges"]])
