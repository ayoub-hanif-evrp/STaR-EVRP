"""Exploratory panel summaries from exact saved method and repeat keys."""

from collections import Counter
from statistics import fmean, median

import numpy as np

from star_evrp.phase4_results import grouped, read_json, require, require_keys
from star_evrp.phase6_archive import csv_rows, key, roster, write_csv, write_json
from star_evrp.phase6_diagnostics import COHORTS, ia_estimate, summarize_direction
from star_evrp.phase6_run import _loads, _payloads, allowed_ids

STAGES = ("as1","fixed-topology","timing")
CERTIFIED = {"single_visit_oracle","target_certified","below_target_certified"}


def audit_certificate(row):
    """Use the replayed solver stages to label the certificate, without changing plans."""
    stage = {item["stage"]:item for item in row["attempts"]}
    status = row["status"]
    if status == "target_certified":
        first = stage["target_completion"]
        tie = stage["target_reliability_tie"]
        if tie.get("replay_successes",0)<tie.get("certified_min_successes",487):
            return "target_completion_only"
        if tie["replay_completion"]-first["fun"]>1e-7+1e-10:
            return "target_completion_only"
        if row["opt_successes"]<tie["certified_min_successes"]:
            return "target_completion_only"
    return status


def observations(out,protocol,stage):
    if stage=="as1" and not read_json(out/"audit/as1_gate.json")["eligible"]:
        return []
    name="as1" if stage=="as1" else "comparator"
    panel=[r for r in csv_rows(out/"manifests"/f"{name}_panel.csv") if r["route"]!="NA"]
    expected = allowed_ids(stage,protocol["configuration"])
    result=[]
    filenames = set()
    for choice in panel:
        context,raw,plans = _payloads(out,stage,protocol,choice)
        filenames.add(raw.name)
        rows,saves = _loads(raw,plans,context)
        require_keys([r["id"] for r in rows],expected,"Analysis work identities")
        for row,plan in zip(rows,saves,strict=True):
            if row["method"]=="FT-SAA":
                row = dict(row,execution_label=row["status"],status=audit_certificate(row))
            value = dict(row,partition=choice["partition"],parent=choice["parent"],variant=choice["variant"],
                         route=int(choice["route"]),family=choice["family"],source_visits=int(choice["visits"]),
                         selected_visits=len(plan["details"]["station_positions"]) if plan["details"] else None)
            result.append(value)
    for area in ("raw","plans"):
        require_keys([f.name for f in (out/area/stage).glob("*.json.gz")],filenames,f"{stage} {area} batches")
    return result


def statistics(rows, policy, block, field, tolerance):
    return {**summarize_direction([row[field] for row in rows],tolerance),**ia_estimate(rows,field,block,policy)}


def parents_for(root,cohort):
    return {row["parent_key"]:(f'{row["family"]}:{row["partition"]}' if cohort=="all120" else row["family"])
            for row in roster(root) if cohort=="all120" or cohort==row["partition"]}


def tape_metrics(vals, stem):
    return {stem+k:v for k,v in (("successes",vals["successes"]),("reliability",vals["reliability"]),
            ("attained",vals["attained"]),("lower_one",vals["wilson95_lower_one_sided"]),("completion",vals["completion"]),
            ("lower_two",vals["wilson95_two_sided"][0]),("upper_two",vals["wilson95_two_sided"][1]),
            ("point",vals["reliability"]>=.95),("straddling",vals["wilson95_two_sided"][0]<=.95<=vals["wilson95_two_sided"][1]),
            ("customer_only",vals["late_customer"]-vals["late_both"]),("depot_only",vals["late_depot"]-vals["late_both"]),
            ("joint",vals["late_both"]),("tape_seed",vals["tape_seed"]))}


def flat(row):
    excluded = {"validation","analytic","work","attempts","score"}
    saved = {k:v for k,v in row.items() if k not in excluded}
    if row["validation"]:
        for tape,vals in row["validation"].items():
            saved.update(tape_metrics(vals,tape+"_"))
    saved.update({f"analytic_{k}":v for k,v in (row["analytic"] or {}).items()})
    if row.get("work"):
        saved.update({f"search_{k}":v for k,v in row["work"].items()})
    if row.get("attempts") is not None:
        saved["solver_stages"] = len(row["attempts"])
    return saved


def contrast(a,b):
    return dict(R_pp=(a["reliability"]-b["reliability"])*100,
                attained_pp=(a["attained"]-b["attained"])*100,completion=a["completion"]-b["completion"])


def evaluate_panel(root,rows,policy,kind):
    selected = {key(r):r for r in rows if r["method"]==kind}
    check = Counter(r["status"] for r in selected.values())
    families = Counter(f'{r["family"]}:{r["partition"]}:{r["variant"]}:{r["source_visits"]}' for r in selected.values())
    raw_pairs,estimates,qchecks,metrics = [],[],[],[]
    for person in rows:
        if person["analytic"] is None:
            continue
        an=person["analytic"]
        model = an["probability"]
        for tape,data in person["validation"].items():
            sample = data["reliability"]
            full = an["mean_completion"]
            qchecks.append(dict(**{k:person[k] for k in ("partition","parent","variant","family","route","method","selected_visits")},
                tape=tape,exact_R=model,MC_R=sample,MC_minus_exact_pp=100*(sample-model),
                true_inside_wilson=data["wilson95_two_sided"][0]<=model<=data["wilson95_two_sided"][1],
                exact_completion=full,MC_completion=data["completion"],delta_completion=data["completion"]-full,
                MC_completion_se=an.get("phase6_completion_mc_se") if tape=="phase6" else None))
    for cohort in COHORTS:
        block = parents_for(root,cohort)
        relevant = [r for r in rows if cohort=="all120" or cohort==r["partition"]]
        for cert in (False,True) if kind=="FT-SAA" else (False,):
            for tape in ("phase6","archive"):
                pairable = [r for r in relevant if selected[key(r)]["validation"] and
                            (not cert or selected[key(r)]["status"] in CERTIFIED)]
                for method,rr in grouped(pairable,lambda r:r["method"]).items():
                    vv = [r["validation"][tape] for r in rr]
                    metrics.append(dict(cohort=cohort,subset="certified" if cert else "all",tape=tape,method=method,n=len(vv),
                                        reliability=fmean(r["reliability"] for r in vv),attained=sum(r["attained"] for r in vv),
                                        straddling=sum(r["wilson95_two_sided"][0]<=.95<=r["wilson95_two_sided"][1] for r in vv),
                                        completion=fmean(r["completion"] for r in vv)))
                kinds = ("FSPC","STaR","CON","SLS")
                comparisons = [(kind,control) for control in kinds] + ([("STaR","FSPC"),("STaR",kind)] if kind=="FT-SAA" else [])
                for challenger,reference in comparisons:
                    index = {(*key(r),r["method"]):r for r in pairable}
                    values = []
                    for k in sorted({key(r) for r in pairable}):
                        a,b = [index[*k,m]["validation"][tape] for m in (challenger,reference)]
                        datum = dict(partition=k[0],parent=k[1],variant=k[2],route=k[3],challenger=challenger,reference=reference,
                                     status=selected[k]["status"],tape=tape,
                                     **contrast(a,b))
                        if cohort=="all120" and not cert:
                            raw_pairs.append(datum)
                        values.append(datum)
                    for metric in ("R_pp","attained_pp","completion"):
                        estimates.append(dict(cohort=cohort,subset="certified" if cert else "all",tape=tape,challenger=challenger,
                            reference=reference,metric=metric,**statistics(values,policy,block,metric,1e-8 if metric=="completion" else 1e-12)))
    return {"records":len(rows),"panel_n":len(selected),"panel_parents":len({r["parent"] for r in selected.values()}),
            "statuses":dict(check),"families":dict(families),"metrics":metrics,"contrasts":estimates},raw_pairs,qchecks


def timing_summary(root,rows,policy):
    aggregate,repeats,estimates,summary = [],[],[],[]
    for (_,method,guard),group in grouped(rows,lambda r:(key(r),r["method"],r["nominal_ms"])).items():
        head=group[0]
        require({r["repeat"] for r in group}==set(range(1,policy["timing_repeats"]+1)),"Timing repeats incomplete")
        v = [r["validation"]["phase6"] for r in group]
        failed = sum(r["work"] is None for r in group)
        work = [r["work"] for r in group if r["work"] is not None]
        aggregate.append(dict(**{k:head[k] for k in ("partition","parent","variant","family","route")},
                              method=method,guard_ms=guard,wall_ms=1000*median(r["elapsed_s"] for r in group),
                              cpu_ms=1000*median(r["cpu_s"] for r in group),reliability=fmean(r["reliability"] for r in v),
                              completion=fmean(r["completion"] for r in v),attained=fmean(r["attained"] for r in v),
                              draws=fmean(w["scenarios_evaluated"] for w in work) if work else None,
                              trials=fmean(w["candidates_evaluated"] for w in work) if work else None,
                              fallbacks=failed,wall_exceedances=sum(r["overshoot_ms"]>0 for r in group)))
    for cohort in COHORTS:
        block=parents_for(root,cohort)
        for guard in policy["timing_guards_ms"]:
            relevant = [r for r in aggregate if r["guard_ms"]==guard and (cohort=="all120" or r["partition"]==cohort)]
            raw = [r for r in rows if r["nominal_ms"]==guard and (cohort=="all120" or r["partition"]==cohort)]
            for method,part in grouped(relevant,lambda r:r["method"]).items():
                info = dict(cohort=cohort,method=method,guard_ms=guard,n=len(part),
                            reliability=fmean(r["reliability"] for r in part),attained=fmean(r["attained"] for r in part),
                            completion=fmean(r["completion"] for r in part),
                            draws=fmean(r["draws"] for r in part if r["draws"] is not None),
                            trials=fmean(r["trials"] for r in part if r["trials"] is not None),fallbacks=sum(r["fallbacks"] for r in part))
                for field in ("wall_ms","cpu_ms"):
                    for label,val in zip(("p25","median","p75","p95"),np.quantile([r[field] for r in part],(.25,.5,.75,.95))):
                        info[f"{field}_{label}"]=float(val)
                included=[r for r in raw if r["method"]==method]
                overs=[r["overshoot_ms"] for r in included]
                info.update(repeats=len(overs),over_guard=sum(x>0 for x in overs),overshoot_max_ms=max(overs),
                            overshoot_p95_ms=float(np.quantile(overs,.95)),
                            stop_proxy=dict(Counter(r["status"] for r in included)))
                summary.append(info)
            zipped = grouped(relevant,key)
            results = []
            for _,pair in sorted(zipped.items()):
                a,b = (next(r for r in pair if r["method"]==m) for m in ("STaR","SLS"))
                results.append(dict(**{k:a[k] for k in ("partition","parent","variant","family","route")},
                                    **contrast(a,b),guard_ms=guard,wall_ms=a["wall_ms"]-b["wall_ms"],cpu_ms=a["cpu_ms"]-b["cpu_ms"],
                                    draws=a["draws"]-b["draws"] if a["draws"] is not None and b["draws"] is not None else None,
                                    trials=a["trials"]-b["trials"] if a["trials"] is not None and b["trials"] is not None else None))
            if cohort=="all120":
                repeats.extend(results)
            for metric in ("R_pp","attained_pp","completion","wall_ms","cpu_ms","draws","trials"):
                estimates.append(dict(cohort=cohort,guard_ms=guard,metric=metric,**statistics(
                    [r for r in results if r[metric] is not None],policy,block,metric,1e-8)))
    return dict(records=len(rows),panel_n=len({key(r) for r in rows}),metrics=summary,contrasts=estimates),aggregate,repeats


def analyze(root,out,protocol):
    policy=protocol["configuration"]
    summary={}
    for stage in STAGES:
        rows=observations(out,protocol,stage)
        if not rows:
            summary[stage]={"status":"skipped"}
            continue
        replay=read_json(out/"audit"/f"{stage}_replay.json")
        require(replay["rows"]==len(rows) and replay["status"]=="pass","Missing scientific replay")
        write_csv(out/"data"/f"{stage}_route_results.csv",[flat(r) for r in rows])
        if stage=="timing":
            summary[stage],aggregate,pairs=timing_summary(root,rows,policy)
            write_csv(out/"data/timing_route_aggregates.csv",aggregate)
        else:
            summary[stage],pairs,checks=evaluate_panel(root,rows,policy,"AS1" if stage=="as1" else "FT-SAA")
            write_csv(out/"data"/f"{stage}_exact_vs_mc.csv",checks)
            if stage=="fixed-topology":
                solver=[dict(**{k:r[k] for k in ("partition","parent","variant","route")},route_status=r["status"],**attempt)
                        for r in rows if r["method"]=="FT-SAA" for attempt in r["attempts"]]
                if solver:
                    write_csv(out/"data/fixed-topology_solver_stages.csv",solver)
        write_csv(out/"data"/f"{stage}_paired_routes.csv",pairs)
        write_csv(out/"data"/f"{stage}_paired_effects.csv",summary[stage]["contrasts"])
        write_csv(out/"data"/f"{stage}_summary.csv",summary[stage]["metrics"])
    write_json(out/"data/experiment_summary.json",summary)
    return summary
