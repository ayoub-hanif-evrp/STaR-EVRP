"""Shared style and editable, deterministic conference artwork."""

from base64 import b64encode
from collections import Counter
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fontTools import subset
from fontTools.ttLib import TTFont
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.ticker import MaxNLocator, MultipleLocator
import numpy as np

from star_evrp.phase4_results import file_sha
from star_evrp.phase6_archive import write_bytes, write_csv, write_json

TEAL, SLATE, AMBER, BLUE, NAVY = "#0D9488","#64748B","#D97706","#2563EB","#1E293B"
GRID, PALE, TOP = "#E3E9EF","#F1F5F9","#ECF7F6"
STEMS = ("Fig01_spatial_charging_repair","Fig02_star_framework","Fig03_paired_reliability",
         "Fig04_charging_complexity","Fig05_quality_simulation_effort")
SUPPLEMENTARY = ("Sup01_complex_route_repair","Sup02_deteriorated_route_diagnostic")
ARTWORK = {**dict.fromkeys(STEMS,"figures"), **dict.fromkeys(SUPPLEMENTARY,"supplementary")}
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
    example=data["examples"]["Fig01"]
    fig=new_figure(width,147)
    gs=fig.add_gridspec(1,3,left=.08,right=.978,top=.916,bottom=.48,wspace=.32)
    axes=gs.subplots()
    world,orig,star=axes
    maps={k:[s for s in example["stops"] if s["plan"]==k] for k in ("CON","STaR")}
    types={"customer":("o",BLUE),"station":("s",AMBER),"depot":("D",NAVY)}
    chosen=example["selection"]["chosen"]
    label_positions=(
        {("CON",1253):(11,334),("STaR",1248):(171,478)}
        if (chosen["parent"],chosen["variant"],chosen["route"])==("C1_10_3","A",106) else {}
    )
    for tag in types:
        base=[r for r in example["nodes"] if r["type"]==tag]
        world.scatter([r["x"] for r in base],[r["y"] for r in base],
                      s={"customer":3.9,"station":8,"depot":24}[tag],marker=types[tag][0],
                      c={"customer":"#BFCAD8","station":"#E0A760","depot":NAVY}[tag],edgecolors="none",
                      zorder=3 if tag=="depot" else 1)
    world.plot([s["x"] for s in maps["CON"]],[s["y"] for s in maps["CON"]],color=BLUE,lw=1.05,zorder=3)
    # Same spatial limits for both detail panels, with uniform padding around the ordered stops.
    xy=[(s["x"],s["y"]) for s in example["stops"]]
    xmin,ymin=np.min(xy,axis=0)-25
    xmax,ymax=np.max(xy,axis=0)+25
    limits=[float(v) for v in (xmin,xmax,ymin,ymax)]
    world.add_patch(Rectangle((xmin,ymin),xmax-xmin,ymax-ymin,facecolor="none",edgecolor=BLUE,
                              lw=.9,ls=(0,(3,2)),zorder=4))
    world.annotate("Detail",xy=(xmax,min(ymax,495)),xytext=(6,-13),textcoords="offset points",
                   color=NAVY,fontsize=7.1,arrowprops=dict(arrowstyle="-",color=SLATE,lw=.55),zorder=5)
    all_x=[p["x"] for p in example["nodes"]]; all_y=[p["y"] for p in example["nodes"]]
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
    fig.text((pos.x0+pos.x1)/2,.396,f'{s["parent"]} / {s["variant"]} · route {s["route"]}',ha="center",size=8.3,weight="bold")
    fig.text((pos.x0+pos.x1)/2,.368,"Outcome-selected holdout route",ha="center",size=7.3)
    for ax,row in zip((orig,star),example["metrics"],strict=True):
        bounds=ax.get_position()
        mid=(bounds.x0+bounds.x1)/2
        fig.text(mid,.396,f'Observed reliability  {100*row["reliability"]:.2f}%',ha="center",size=8.3,weight="bold")
        att="attains" if row["attained"] else "below target"
        fig.text(mid,.368,f'Return {row["completion"]:,.2f} · Wilson {att}',ha="center",size=7.2)
    handles=route_symbols()
    handles.extend([Line2D([],[],label="Original path",color=SLATE,ls=(0,(3,2))),
                    Line2D([],[],label="Repaired path",color=TEAL)])
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.51,.316),ncol=5,frameon=False,
               fontsize=7.8,columnspacing=1.45,handlelength=1.5)
    fig.text(.08,.268,"(d)  Battery along each plan’s own travel path",size=9.4,weight="bold")
    ax1=fig.add_axes((.12,.080,.35,.15))
    ax2=fig.add_axes((.602,.080,.35,.15),sharex=ax1,sharey=ax1)
    max_dist=max(r["total_distance"] for r in example["totals"])
    for ax,totals in zip((ax1,ax2),example["totals"],strict=True):
        events=[r for r in example["stops"] if r["plan"]==totals["method"]]
        battery(ax,events,totals,max_dist,totals["capacity"],compact=True)
        ax.set_title("Original route" if totals["method"]=="CON" else "STaR",fontsize=7.6,pad=2)
    ax1.set_ylabel("Battery energy (native)")
    return fig,dict(selection=s,zoom_limits=limits,aspect="equal, equal limits in b/c",map_nodes=example["nodes"],
                    ordered_stops=example["stops"],metrics=example["metrics"],physical_summary=example["totals"])



def battery(ax, events, totals, max_dist, max_cap, *, compact=False):
    color = TEAL if totals["method"] == "STaR" else SLATE
    line = "-" if totals["method"] == "STaR" else (0,(3,2))
    x, y = [], []
    for event in events:
        x.extend((event["distance"],event["distance"]))
        y.extend((event["battery_arrival"],event["battery_departure"]))
    ax.axhline(max_cap,color=SLATE,lw=.62,ls=(0,(3,3)),zorder=1)
    ax.axhline(0,color=NAVY,lw=.68,zorder=1)
    ax.plot(x,y,color=color,lw=1.27,ls=line,zorder=2)
    for event in events:
        d,a,b=event["distance"],event["battery_arrival"],event["battery_departure"]
        if event["type"]=="station":
            ax.plot([d,d],[a,b],color=AMBER,lw=1.5,zorder=3)
            ax.plot([d,d],[a,b],"s",color=AMBER,ms=2.7,zorder=4)
            if not compact:
                order=event["station_order"]
                ax.annotate(f'S{order}',(d,(a+b)/2),xytext=(3,0),
                            textcoords="offset points",va="center",fontsize=6.7,color=NAVY)
        elif event["type"]=="customer":
            ax.plot(d,b,"o",color=BLUE,ms=2.5 if compact else 2.15,zorder=3)
            if compact:
                ax.annotate(str(event["customer_order"]),(d,b),xytext=(0,5),
                            textcoords="offset points",ha="center",fontsize=7)
    ax.plot(x[0],y[0],"D",color=NAVY,ms=3,zorder=4)
    ax.plot(x[-1],y[-1],"D",color=NAVY,ms=3,zorder=4)
    fit=max((e["distance"] for e in events))
    ax.annotate(f'{max(0,totals["final_battery"]):.1f}',(fit,y[-1]),xytext=(-6,9),
                textcoords="offset points",ha="right",fontsize=7.2,color=NAVY)
    ax.set(xlim=(-max_dist*.025,max_dist*1.045),ylim=(-.08*max_cap,1.065*max_cap),
           yticks=[0,max_cap/2,max_cap],xlabel="Distance traveled (native)")
    ax.xaxis.set_major_locator(MaxNLocator(5))
    grid(ax,"y")


def complex_spatial(data,width):
    example=data["examples"]["Sup01"]
    fig=new_figure(width,134)
    gs=fig.add_gridspec(2,2,left=.097,right=.97,top=.85,bottom=.18,wspace=.30,hspace=.72,
                        height_ratios=(1.15,1))
    axes=gs.subplots()
    stops=example["stops"]
    xy=np.array([(s["x"],s["y"]) for s in stops])
    xmin,ymin=xy.min(axis=0)-18
    xmax,ymax=xy.max(axis=0)+18
    chosen=example["selection"]["chosen"]
    fig.text(.09,.948,f'{chosen["parent"]} / {chosen["variant"]} · route {chosen["route"]}',
             weight="bold",size=9.5)
    fig.text(.09,.911,f'Outcome-selected holdout example · {chosen["customers"]} customers in the same order',size=8.0)
    for i,(label,method,color) in enumerate((("Original route","CON",SLATE),("STaR","STaR",TEAL))):
        a,b=axes[:,i]
        events=[e for e in stops if e["plan"]==method]
        x,y=[e["x"] for e in events],[e["y"] for e in events]
        a.plot(x,y,color=color,lw=.98,ls="-" if method=="STaR" else (0,(3,2)),zorder=2)
        for left,right in zip(events,events[1:]):
            arrow_leg(a,left,right,color)
        customers=[r for r in events if r["type"]=="customer"]
        a.scatter([r["x"] for r in customers],[r["y"] for r in customers],s=8,c=BLUE,
                  edgecolors="white",linewidths=.32,zorder=5)
        a.plot(x[0],y[0],"D",color=NAVY,ms=4,zorder=7)
        station_positions={}
        for e in events:
            if e["type"]=="station":
                station_positions.setdefault((e["x"],e["y"]),[]).append(e["station_order"])
        for (sx,sy),visits in station_positions.items():
            dx,dy={1:(10,2),2:(-8,11),3:(9,-10),4:(-10,1)}.get(visits[0],(7,5))
            a.plot(sx,sy,"s",color=AMBER,ms=4.8,mew=.55,mec="white",zorder=7)
            a.annotate("/".join(f'S{j}' for j in visits),(sx,sy),xytext=(dx,dy),textcoords="offset points",
                       ha="left" if dx>0 else "right",va="center",fontsize=7,weight="bold",zorder=9,
                       bbox=dict(facecolor="white",edgecolor="none",alpha=.88,pad=.55),
                       arrowprops=dict(arrowstyle="-",color=SLATE,lw=.45,shrinkA=1,shrinkB=3))
        a.set(xlim=(xmin,xmax),ylim=(ymin,ymax),aspect="equal",ylabel="y (native)",xlabel="x (native)")
        a.xaxis.set_major_locator(MaxNLocator(5))
        a.yaxis.set_major_locator(MaxNLocator(4))
        metric=example["metrics"][i]
        heading(a,"ab"[i],label)
        a.text(.5,-.36,f'Observed R {metric["reliability"]*100:.2f}% · mean return {metric["completion"]:,.1f}',
               transform=a.transAxes,ha="center",weight="bold",size=7.6)
        battery(b,events,example["totals"][i],max(t["total_distance"] for t in example["totals"]),
                example["totals"][0]["capacity"])
        heading(b,"cd"[i],f'{label} battery')
    axes[1,0].set_ylabel("Battery energy (native)")
    handles=route_symbols()
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.53,.046),ncol=3,frameon=False,
               fontsize=7.8,columnspacing=1.6,handlelength=1.1)
    return fig,dict(**example,zoom_limits=[float(v) for v in (xmin,xmax,ymin,ymax)],aspect="equal, equal limits in a/b")


def adverse_profile(data,width):
    example=data["examples"]["Sup02"]
    fig=new_figure(width,89)
    left,right=fig.subplots(1,2,gridspec_kw={"width_ratios":(1.36,1)})
    fig.subplots_adjust(left=.107,right=.92,bottom=.245,top=.72,wspace=.40)
    chosen=example["selection"]["chosen"]
    fig.text(.105,.939,f'{chosen["parent"]} / {chosen["variant"]} · route {chosen["route"]}',weight="bold",size=9.5)
    fig.text(.105,.881,"Largest observed holdout loss versus fixed-station repair · outcome-selected",size=8)
    names={"FSPC":"Fixed-station repair","STaR":"STaR"}
    colors={"FSPC":SLATE,"STaR":TEAL}
    plan_events=[[e for e in example["stops"] if e["plan"]==m and e["type"]=="customer"]
                 for m in ("FSPC","STaR")]
    order=[e["customer_order"] for e in plan_events[0]]
    diff=[b["deadline_slack"]-a["deadline_slack"] for a,b in zip(*plan_events,strict=True)]
    left.axhline(0,color=SLATE,lw=.8,ls=(0,(2,2)),zorder=1)
    left.plot(order,diff,color=TEAL,marker="o",ls="-",lw=1.15,ms=2.8,zorder=2)
    left.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=6))
    left.set(xlabel="Customer visit order",ylabel="Change in slack (native)")
    changes=[e for e in example["stops"] if e["type"]=="station" and e["plan"]=="STaR"]
    for i in (1,3):
        x=changes[i]["customers_served"]+.5
        left.axvline(x,color=AMBER,lw=.8,ls=(0,(3,2)),zorder=1)
        left.annotate(f'S{i+1}',(x,0),xytext=(-4,5),textcoords="offset points",ha="right",fontsize=6.8)
    pad=max(3,.15*max(abs(v) for v in diff))
    left.set_ylim(min(0,min(diff))-pad,max(0,max(diff))+pad)
    grid(left,"y")
    heading(left,"a","Zero-wait deadline slack")
    heading(right,"b","Archived validation")
    right.set(xlim=(0,1),ylim=(0,1))
    right.axis("off")
    for i,m in enumerate(example["metrics"]):
        y=.94-i*.45
        label=names[m["method"]]
        right.text(0,y,label,weight="bold",color=colors[m["method"]],va="top")
        right.text(0,y-.126,f'{m["successes"]:,}/{m["scenarios"]:,} successes',va="top")
        right.text(0,y-.242,f'{m["customer_only"]:,} customer-only failures',size=7.6,va="top")
        right.text(0,y-.344,f'Mean full return {m["completion"]:,.2f}',size=7.6,va="top")
    fig.text(.106,.084,"Change is STaR minus fixed-station repair. S2 and S4 are charging visits.",size=7.5)
    fig.text(.106,.040,"Slack = deadline minus service-start time.",size=7.5)
    return fig,example


def route_symbols():
    return [Line2D([],[],label=label,marker=marker,ls="",color=color,markersize=4.6)
            for label,marker,color in (("Customer","o",BLUE),("Station","s",AMBER),("Depot","D",NAVY))]


FLOW = {
    "nodes": [
        {"id":"initialize","heading":"Start from original route","lines":["Feasible ordered plan","Station laws, target, caps","Trace + score on 512 draws"],
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
        ["propose","return","proposal stream exhausted or a cooperative guard stops search"],
    ],
    "score":{"attaining":["minimize unconditional mean completion","maximize reliability"],
             "below_target":["maximize reliability","minimize unconditional mean completion"],"strict":True},
    "bounds":{"target":0.95,"screen_tolerance":1e-12,"prefix_completion_cushion":1e-8,
              "R_U":"(m + S - k) / S","C_L":"(C_k + (S - k) C_0) / S","prefix":128,"full":512},
    "validation":{"source":"phase3.py:287–345","independent_draws":10000,"feedback":False},
}


MOVES = (
    ("Replace station", "competitive_search.py:100–104",("1","A","2","3"),("1","B","2","3")),
    ("Relocate visit", "competitive_search.py:114–123",("1","A","2","3"),("1","2","A","3")),
    ("Insert visit", "competitive_search.py:106–112",("1","2","3"),("1","A","2","3")),
    ("Remove visit", "competitive_search.py:96–98",("1","A","2","3"),("1","2","3")),
    ("Adjust charge", "competitive_search.py:129–141",("1","A:q","2","3"),("1","A:q′","2","3")),
    ("Transfer charge", "competitive_search.py:142–152, 161–166",("1","A:q","2","B:p","3"),
     ("1","A:q−δ","2","B:p+δ","3")),
)
FLOW["operators"]=[dict(move=title,source=source,before=list(before),after=list(after))
                   for title,source,before,after in MOVES]
FLOW["edges"] += [
    ["return","validation","independent final assessment; no search feedback"],
    ["prefix","propose","advance if full extension cannot be completed while guards permit"],
]


def framework(width):
    fig=new_figure(width,131)
    ax=fig.add_axes((.023,.026,.954,.934))
    ax.set_axis_off()
    ax.set(xlim=(0,1),ylim=(0,1))
    xval=(.036,.273,.510,.747)
    w,h=.211,.117
    top,bottom=.789,.593
    positions={n["id"]:(xval[i],top) for i,n in enumerate(FLOW["nodes"][:4])}
    positions.update({n["id"]:(xval[3-i],bottom) for i,n in enumerate(FLOW["nodes"][4:])})
    labels = {
        "initialize": ("Start from original route", "Score on 512 draws"),
        "rank": ("Rank visits and gaps", "Largest wait risk first"),
        "propose": ("Interleave operators", "Quantity and topology edits"),
        "feasible": ("Check candidate", "Unique and feasible"),
        "screen": ("Conditional screen", "True-reliability bound"),
        "prefix": ("Prefix → full tape", "128 then 512 if viable"),
        "score": ("Compare full scores", "Strict score gain"),
        "return": ("Return incumbent", "Then validate independently"),
    }
    for name,(x,y) in positions.items():
        fill=TOP if name in ("rank","prefix","score") else PALE
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.003,rounding_size=.012",
                                   ec="#CBD5E1",fc=fill,lw=.75,zorder=1))
        label,hint=labels[name]
        ax.text(x+w/2,y+h*.64,label,ha="center",va="center",fontsize=7.4 if name=="initialize" else 8.1,
                weight="bold",zorder=3)
        ax.text(x+w/2,y+h*.29,hint,ha="center",va="center",fontsize=6.9,zorder=3)

    def arrow(start,end,color=SLATE,lw=.9):
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle="-|>",mutation_scale=7.6,linewidth=lw,color=color,
                                    shrinkA=0,shrinkB=0,zorder=5))

    def wire(points,*,dashed=False,color=SLATE):
        ax.plot(*zip(*points),color=color,lw=.72,ls=(0,(2.8,2)) if dashed else "-",zorder=4)

    for i in range(3):
        arrow((xval[i]+w+.003,top+h/2),(xval[i+1]-.003,top+h/2))
    xr=xval[3]+w/2
    arrow((xr,top-.004),(xr,bottom+h+.004))
    ax.text(xr+.013,(top+bottom+h)/2,"Feasible",va="center",fontsize=6.9)
    for i in (3,2):
        arrow((xval[i]-.003,bottom+h/2),(xval[i-1]+w+.003,bottom+h/2))
    ax.text(.73,.727,"Pass / bypass",ha="center",fontsize=6.8)
    arrow((xval[1]+.027,bottom+h+.004),(xval[1]+.027,top-.004),TEAL,lw=1.25)
    ax.text(xval[1]+.044,.747,"Strict gain: update and restart",va="center",fontsize=7.1)

    # An exhausted or guarded proposal stream returns the incumbent on its own path.
    xe=xval[2]+.061
    wire([(xe,top+h+.004),(xe,.982),(.012,.982),(.012,bottom+h/2)])
    arrow((.012,bottom+h/2),(xval[0]-.004,bottom+h/2))
    ax.text(.027,.958,"No proposals left or guard stops search",fontsize=7.15,va="center")
    # Rejected comparisons all re-enter proposal generation, subject to the same guards.
    retry=.535
    x_retry=xval[2]+.161
    wire([(xval[1]+w/2,bottom-.004),(xval[1]+w/2,retry),(.982,retry),(.982,.930),(x_retry,.930)],
         dashed=True)
    for i in (2,3):
        xm=xval[i]+w/2
        wire([(xm,bottom-.004),(xm,retry)],dashed=True)
    wire([(xval[3]+w+.003,top+h/2),(.982,top+h/2)],dashed=True)
    arrow((x_retry,.930),(x_retry,top+h+.004),lw=.75)
    ax.text(.275,.505,"Rejected or no strict gain: advance to next proposal while guards permit.",fontsize=7.45)

    ax.axhline(.463,xmin=.017,xmax=.98,color="#CBD5E1",lw=.7)
    ax.text(.026,.424,"Candidate operators",weight="bold",fontsize=9)
    ax.text(.97,.424,"Conceptual sketches · customer order fixed",ha="right",fontsize=7.35)
    xs=(.035,.356,.677)
    ys=(.325,.143)
    for i,(title,_,before,after) in enumerate(MOVES):
        x,y=xs[i%3],ys[i//3]
        ax.text(x,y+.057,title,weight="bold",fontsize=8)
        for row,seq in enumerate((before,after)):
            ypos=y-row*.059
            centers=np.linspace(x+.042,x+.273,len(seq))
            ax.plot(centers,[ypos]*len(centers),color="#94A3B8",lw=.70,zorder=1)
            ax.text(x,ypos,"in" if row==0 else "out",fontsize=6.2,va="center")
            for cx,token in zip(centers,seq,strict=True):
                customer=token.isdigit()
                ax.plot(cx,ypos,marker="o" if customer else "s",ms=9.1 if ":" not in token else 10.0,
                        mfc="white" if customer else "#FEF0D4",mec=BLUE if customer else AMBER,mew=.85,zorder=2)
                ax.text(cx,ypos,token.split(":")[0],ha="center",va="center",fontsize=6.45,zorder=3)
                if ":" in token:
                    ax.text(cx,ypos-.027,token.split(":")[1],ha="center",va="top",fontsize=6.5,zorder=3)
    ax.text(.026,.019,"Circles: ordered customers   ·   Squares: station identities   ·   q, p: charge amounts",fontsize=7.3)
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
    counts.text(0,.98,"versus fixed-station repair",transform=counts.transAxes,fontsize=7.5,va="top")
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
        left.annotate(f'{r["mean_pp"]:+.2f}',(r["mean_pp"],y),xytext=(8,9),textcoords="offset points",
                      fontsize=7.35)
        right.barh(y,r["nonattainment_pct"],height=.34,color=AMBER,alpha=.88)
        right.plot(r["nonattainment_pct"],y,"s",mec=AMBER,mfc="white",ms=3.5,mew=.8,zorder=3)
        right.annotate(f'{r["nonattained"]}/{r["n"]:,}',(r["nonattainment_pct"],y),xytext=(5,0),
                       textcoords="offset points",ha="left",va="center",fontsize=7.75)
    left.set_yticks(ypos,labels)
    left.set(xlim=(-.22,6.05),ylim=(-.47,2.47),xlabel="STaR minus fixed-station repair (pp)")
    right.set(xlim=(0,23.2),xlabel="Share of routes (%)")
    left.xaxis.set_major_locator(MultipleLocator(2))
    right.xaxis.set_major_locator(MultipleLocator(5))
    left.tick_params(axis="y",length=0,pad=8)
    right.tick_params(axis="y",length=0)
    left.spines["left"].set_visible(False)
    heading(left,"a","Reliability effect")
    heading(right,"b","Routes not attaining target")
    notes=data["complexity_notes"]
    fig.text(.223,.073,f'3+ visits: {notes["three_share"]:.1f}% of exposed routes and {notes["net_share"]:.1f}% of the net signed reliability gain.',
             size=8.0,weight="bold")
    return fig,dict(bins=rows,annotations=notes)


def effort(data,width):
    fig=new_figure(width,92)
    left,right=fig.subplots(1,2,gridspec_kw={"width_ratios":[1.24,1]})
    fig.subplots_adjust(left=.105,right=.968,top=.77,bottom=.25,wspace=.43)
    fig.text(.105,.939,"Separate timing panel · 118 routes, 60 parents",size=8.4,weight="bold")
    fig.text(.105,.889,"20, 50 and 100 ms cooperative runtime guards",size=7.6)
    points=data["timing"]
    colors={"STaR":TEAL,"SLS":SLATE}
    markers={"STaR":"o","SLS":"s"}
    fills={20:"bottom",50:"none",100:"full"}
    for r in points:
        method=r["method"]
        guard=r["guard_ms"]
        x=r["draws"]/1000
        y=r["reliability_pct"]
        primary=guard==50
        left.plot(x,y,marker=markers[method],ls="",color=colors[method],fillstyle=fills[guard],mfc=colors[method],mfcalt="white",
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


def svg_typography():
    """Supply editable Latin and Greek text with the same fonts on systems without DejaVu."""
    assets=Path(matplotlib.get_data_path())/"fonts/ttf"
    license_text=(assets/"LICENSE_DEJAVU").read_text(encoding="utf-8")
    rules=[]
    characters=[*range(32,0x180),*range(0x370,0x400),*range(0x2000,0x2070),0x2192,0x2212]
    for filename,weight in (("DejaVuSans.ttf",400),("DejaVuSans-Bold.ttf",700)):
        with TTFont(assets/filename,recalcTimestamp=False) as font:
            options=subset.Options()
            options.drop_tables += ["FFTM"]
            cut=subset.Subsetter(options)
            cut.populate(unicodes=characters)
            cut.subset(font)
            content=BytesIO()
            font.save(content)
        encoded=b64encode(content.getvalue()).decode("ascii")
        rules.append(f"@font-face{{font-family:'DejaVu Sans';font-weight:{weight};"
                     f"src:url(data:font/ttf;base64,{encoded}) format('truetype');}}")
    style=f'<desc>{escape(license_text)}</desc><defs><style type="text/css">{"".join(rules)}</style></defs>'
    return style.encode("utf-8"),license_text.encode("utf-8")


def draw(root,out,data,width,captions):
    typography,license_text=svg_typography()
    write_bytes(out/"FONT_LICENSE.txt",license_text)
    with plt.rc_context(STYLE):
        plots=(spatial,lambda _,w:framework(w),paired_reliability,charging_complexity,effort,complex_spatial,adverse_profile)
        for (name,folder),fn in zip(ARTWORK.items(),plots,strict=True):
            fig,values=fn(data,width)
            directory=out/folder
            for extension,meta in (
                ("png",{"Software":"STaR-EVRP / Matplotlib"}),
                ("pdf",{"Creator":"STaR-EVRP / Matplotlib","Title":name,"CreationDate":datetime(2000,1,1,tzinfo=timezone.utc),
                        "ModDate":datetime(2000,1,1,tzinfo=timezone.utc)}),
                ("svg",{"Creator":"STaR-EVRP / Matplotlib","Date":None,"Title":name}),
            ):
                buffer=BytesIO()
                fig.savefig(buffer,format=extension,dpi=400,metadata=meta,facecolor="white")
                content=buffer.getvalue()
                if extension=="svg":
                    content=content.replace(b"'DejaVu Sans';",b"'DejaVu Sans', sans-serif;")
                    content=content.replace(b"</metadata>",b"</metadata>\n "+typography,1)
                write_bytes(directory/f"{name}.{extension}",content)
            dim=[round(v*25.4,4) for v in fig.get_size_inches()]
            plt.close(fig)
            files={ext:file_sha(directory/f"{name}.{ext}") for ext in ("png","pdf","svg")}
            write_json(directory/f"{name}.json",dict(stem=name,physical_mm=dim,dpi=400,formats_sha256=files,
                caption=captions[name],plotted=values,source_sha256=data["sources"][name[:5]],
                plot_source_sha256=file_sha(root/"src/star_evrp/conference_figures.py"),font="DejaVu Sans"))
    write_json(out/"data/Fig02_flow.json",FLOW)
    write_csv(out/"data/Fig02_flow_nodes.csv",[dict(id=n["id"],label=n["heading"],lines=" | ".join(n["lines"]),source=n["source"]) for n in FLOW["nodes"]])
    write_csv(out/"data/Fig02_flow_edges.csv",[dict(zip(("from","to","condition"),e,strict=True)) for e in FLOW["edges"]])
