"""Numerical audit of the mathematical formulae on the full AS1 panel."""

from statistics import fmean

import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr
from scipy.stats import norm

from star_evrp.phase3 import _route
from star_evrp.phase4_results import require
from star_evrp.phase6_archive import case_key, contexts, csv_rows, key, write_json
from star_evrp.phase6_math import analytic, backward_cap, one_visit_clock
from star_evrp.phase6_run import _loads, _payloads
from star_evrp.route_validator import validate_repair
from star_evrp.timing import RouteTiming


def reference(root,out,protocol):
    panel = {key(r)[:3]:r for r in csv_rows(out/"manifests/as1_panel.csv") if r["route"]!="NA"}
    rows = []
    for case,instance,physics,original,_ in contexts(root,protocol["freeze_digest"]):
        mark=case_key(case)
        if mark not in panel:
            continue
        row=panel[mark]
        k=key(row)
        context,raw,plans=_payloads(out,"as1",protocol,row)
        metrics,details=_loads(raw,plans,context)
        for record,plan in zip(metrics,details,strict=True):
            if record["method"] not in ("CON","AS1") or record["analytic"] is None or not plan["details"]:
                continue
            source=_route(original[k[-1]])
            chosen=_route({"route_id":k[-1],**plan["details"]})
            trace=validate_repair(instance,source,chosen,physics)
            timing=RouteTiming.from_trace(instance,trace,physics)
            if len(timing.mus)!=1:
                continue
            calc=analytic(timing)
            cap,a,b=one_visit_clock(timing)
            backward=backward_cap(timing)
            require(cap is not None and backward is not None and abs(cap-backward)<1e-8,"Valid one-visit clock failed")
            isolated=float(timing.isolated_caps(trace)[0])
            require(isolated>=cap-1e-8,"Frozen marginal cap below exact")
            tol=1e-8
            amounts=np.r_[np.linspace(0,max(0,cap-tol),64),cap+tol,np.linspace(cap+2*tol,cap+20,64)]
            success,clocks=timing.evaluate(amounts[:,None])
            keep=np.abs(amounts-cap)>tol/2
            require(np.array_equal(success[keep],amounts[keep]<=cap) and np.max(np.abs(clocks-np.maximum(amounts+a,b)))<1e-8,
                    "Dense reference clock differs")
            mu,sigma=map(float,(timing.mus[0],timing.sigmas[0]))
            pivot=(np.log(b-a)-mu)/sigma if b>a and sigma>0 else -np.inf
            if sigma>0:
                expected=quad(lambda z:max(a+np.exp(mu+sigma*z),b)*norm.pdf(z),-15,15,
                              epsabs=1e-8,points=[pivot] if abs(pivot)<15 else None)[0]
                reference_R=float(ndtr((np.log(cap)-mu)/sigma)) if cap>0 else 0.0
            else:
                expected=max(a+np.exp(mu),b)
                reference_R=float(np.exp(mu)<=cap)
            require(abs(expected-calc["mean_completion"])<1e-8 and abs(reference_R-calc["probability"])<1e-13,
                    "Exact mean or CDF differs from independent reference")
            observed=record["validation"]["phase6"]
            se=record["analytic"]["phase6_completion_mc_se"]
            rows.append(dict(route=list(k),method=record["method"],exact_cap=cap,isolated_cap=isolated,
                             cap_cushion=isolated-cap,forward_backward_abs=abs(cap-backward),
                             quadrature_abs=abs(expected-calc["mean_completion"]),
                             completion_mc_error=observed["completion"]-expected,completion_mc_se=se,
                             completion_within_2se_or_roundoff=abs(observed["completion"]-expected)<=max(2*se,1e-8),
                             reliability_mc_error_pp=100*(observed["reliability"]-reference_R),
                             probability_within_wilson=observed["wilson95_two_sided"][0]<=reference_R<=observed["wilson95_two_sided"][1]))
    by_method={}
    for method in ("CON","AS1"):
        matching=[r for r in rows if r["method"]==method]
        by_method[method]=dict(n=len(matching),model_reliability_inside_wilson=sum(r["probability_within_wilson"] for r in matching),
            completion_within_2se_or_roundoff=sum(r["completion_within_2se_or_roundoff"] for r in matching),
            mean_mc_probability_error_pp=fmean(r["reliability_mc_error_pp"] for r in matching))
    require(len(rows)==2*len(panel),"Missing real one-visit reference plans")
    result=dict(status="pass",n=len(rows),dense_waits_per_plan=129,methods=by_method,
                minimum_frozen_cap_cushion=min(r["cap_cushion"] for r in rows),
                maximum_frozen_cap_cushion=max(r["cap_cushion"] for r in rows),
                maximum_quad_difference=max(r["quadrature_abs"] for r in rows),rows=rows)
    write_json(out/"audit/math_reference.json",result)
    return result
