import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.optimize import LinearConstraint, milp
from scipy.stats import norm

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.phase6_fixed import build_milp, fixed_topology
from star_evrp.phase6_math import (analytic, backward_cap, exhaustive, expected_return, lognormal_cdf,
                                 minimum_charge, one_visit_clock)
from star_evrp.search_common import SearchCandidate
from star_evrp.timing import RouteTiming, TimingStep
from star_evrp.types import NUM_TOL, Route, RouteStop
from tests.conftest import make_synthetic_instance


def one(ready=18, due=22, close=29):
    return RouteTiming((TimingStep(4,-math.inf,2,math.inf,math.inf,0),
                        TimingStep(3,ready,2,due,math.inf,None),
                        TimingStep(5,-math.inf,0,math.inf,close,None)),np.array([1.]),np.array([.6]))


@pytest.mark.parametrize(("ready","due","close","cap"),[(18,22,29,13),(18,22,27,11),(18,17,40,None),
                         (0,9,16,0),(0,9-NUM_TOL,16,None),(0,8,50,None),(0,math.inf,math.inf,math.inf)])
def test_forward_backward_and_frozen_clock(ready,due,close,cap):
    timing=one(ready,due,close)
    fwd,a,b=one_visit_clock(timing)
    bwd=backward_cap(timing)
    if cap is None:
        assert fwd is bwd is None and not timing.evaluate(np.zeros((1,1)))[0][0]
    else:
        assert fwd==pytest.approx(cap,abs=2*NUM_TOL)
        assert bwd==pytest.approx(fwd,abs=1e-12)
        dense=np.linspace(0,50,3000)
        success,ret=timing.evaluate(dense[:,None])
        assert np.array_equal(success,dense<=fwd)
        assert np.allclose(ret,np.maximum(a+dense,b),rtol=0,atol=1e-12)
        if 0 < fwd < math.inf:
            lo,hi=0.,60.
            for _ in range(50):
                mid=(lo+hi)/2
                if timing.evaluate(np.array([[mid]]))[0][0]:
                    lo=mid
                else:
                    hi=mid
            assert (lo+hi)/2 == pytest.approx(fwd,abs=1e-10)


def test_stop_loss_quadrature_and_degenerate_boundary():
    for a,b,mu,sigma in ((16,25,1,.6),(19,19,-1,.2),(1,10,4,2),(30,33,-3,2)):
        trusted=quad(lambda x:max(a+math.exp(mu+sigma*x),b)*norm.pdf(x),-14,14,
                     points=[(math.log(b-a)-mu)/sigma] if b>a and abs((math.log(b-a)-mu)/sigma)<14 else None)[0]
        assert expected_return(a,b,mu,sigma)==pytest.approx(trusted,rel=1e-10)
    assert lognormal_cdf(2.,math.log(2),0)==1
    assert lognormal_cdf(2.-1e-10,math.log(2),0)==0
    assert lognormal_cdf(0.,-1000,0)==0
    assert lognormal_cdf(10,1000,0)==0
    assert expected_return(0,30,900,1)==math.inf
    assert expected_return(0,30,-900,1)==30


def test_minimal_charge_weak_dominance_and_as1_exhaustive():
    instance=make_synthetic_instance(customer_tw=(30,70),depot_closing=100,station_ids=[1001,1002])
    source=Route(1,[0,1],[RouteStop(x) for x in (0,1,1001,2,0)])
    physics=SimulatorConfig(20,1)
    d=instance.distance_matrix
    batch=[]
    for gap in range(3):
        customer=[0,1,2,0]
        ids=customer[:gap+1]
        for station in instance.station_node_ids:
            indices=[instance.index_of(i) for i in [*ids,station,*customer[gap+1:]]]
            legs=d[indices[:-1],indices[1:]]
            q=minimum_charge(sum(legs[:gap+1]),sum(legs[gap+1:]),20)
            if q is None:
                continue
            minimal=Route(1,[0,1],[RouteStop(x,q if x==station else None) for x in [*ids,station,*customer[gap+1:]]])
            trace=simulate_route_fixed(instance,minimal,physics)
            assert trace.feasible
            p=analytic(RouteTiming.from_trace(instance,trace,physics))
            batch.append(p)
            for amount in (q,(q+sum(legs[:gap+1]))/2,sum(legs[:gap+1])):
                minimal.stops[gap+1].energy_charged=amount
                replay=simulate_route_fixed(instance,minimal,physics)
                assert replay.feasible
                current=analytic(RouteTiming.from_trace(instance,replay,physics))
                assert p["probability"] >= current["probability"]-1e-14
                assert p["mean_completion"] <= current["mean_completion"]+1e-12
    selected,result=exhaustive(instance,source,physics,target=.95,probability_tol=1e-13,clock_tol=1e-8)
    plain=simulate_route_fixed(instance,Route(1,[0,1],[RouteStop(x) for x in (0,1,2,0)]),physics)
    assert result["total"]==7 and result["evaluated"]+result["energy_rejected"]+result["timing_rejected"]==7
    assert selected is not None and plain.feasible and not any(stop.node_id>1000 for stop in selected.stops)
    assert result["mean_completion"]==pytest.approx(min([plain.end_clock,*[p["mean_completion"] for p in batch]]))


def test_marginal_and_prefix_empirical_distinction():
    instance=make_synthetic_instance(customer_tw=(10,45),depot_closing=52,wait_mu=2.5,wait_sigma=.4,station_ids=[1001,1002])
    physics=SimulatorConfig(50,1)
    for nodes in ((0,1001,1,2,0),(0,1001,1,1002,2,0)):
        route=Route(0,[0,1],[RouteStop(i,0) for i in nodes])
        trace=simulate_route_fixed(instance,route,physics)
        timing=RouteTiming.from_trace(instance,trace,physics)
        bound=timing.marginal_bounds(trace).min()
        if len(timing.mus)==1:
            assert analytic(timing)["probability"] <= bound + 1e-14
        else:
            rng=np.random.default_rng(19)
            waits=timing.waits(rng.standard_normal((12000,2)))
            wins,_=timing.evaluate(waits)
            assert np.all(waits[wins] <= timing.isolated_caps(trace))
    # A true p=.94 allows a positive-probability 512/512 success tape.
    assert .94**512 > 0
    rng=np.random.default_rng(88)
    for _ in range(500):
        prefix=rng.integers(0,129)
        lower=(12800+384*90)/512
        upper=(prefix+384)/512
        opt=SearchCandidate(None,True,upper,lower-1e-8).score_key(.95)
        for unseen in (0,358,359,384,int(rng.integers(0,385))):
            exact=SearchCandidate(None,True,(prefix+unseen)/512,lower+float(rng.choice([0,1])),).score_key(.95)
            assert opt>=exact


def test_milp_segments_and_big_m_against_replay():
    # One slow and one fast station; a ready floor absorbs late arrivals at the first customer.
    timing=RouteTiming((TimingStep(2,-math.inf,0,math.inf,math.inf,0),
                        TimingStep(2,5,1,18,math.inf,None),
                        TimingStep(2,-math.inf,0,math.inf,math.inf,1),
                        TimingStep(4,0,1,33,math.inf,None),
                        TimingStep(4,-math.inf,0,math.inf,38,None)),np.zeros(2),np.ones(2))
    waits=np.array([[0.,0.],[4,5],[8,10],[10000,3]])
    rows,bounds,integ,objective,failed,maximum_m=build_milp(timing,[1,2],[2,4,8],10,waits)
    limit=LinearConstraint(failed,0,1)
    result=milp(objective,integrality=integ,bounds=bounds,constraints=[rows.constraint(len(objective)),limit])
    assert result.success and maximum_m > 9000
    q=result.x[:2]
    steps=list(timing.steps)
    steps[0]=TimingStep(2,-math.inf,q[0],math.inf,math.inf,0)
    steps[2]=TimingStep(2,-math.inf,q[1]/2,math.inf,math.inf,1)
    replay=RouteTiming(tuple(steps),timing.mus,timing.sigmas)
    wins,completion=replay.evaluate(waits)
    assert wins.tolist()==[True,True,True,False]
    assert result.fun == pytest.approx(float(completion.mean()),abs=1e-8)
    assert q[0]==pytest.approx(0,abs=2e-9) and q[1]==pytest.approx(4,abs=2e-9)
    impossible=milp(objective,integrality=integ,bounds=bounds,
                    constraints=[rows.constraint(len(objective)),LinearConstraint(failed,0,0)])
    assert impossible.status==2
