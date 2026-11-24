import pytest

from star_evrp.budget import BudgetConfig
from star_evrp.competitive_search import Neighborhood, optimize
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.phase5_ablations import optimize_component
from star_evrp.phase5_experiments import signature
from star_evrp.route_evaluator import RouteEvaluator
from star_evrp.types import Route, RouteStop
from tests.conftest import make_synthetic_instance


def fixture():
    instance=make_synthetic_instance(station_ids=[1001,1002],customer_tw=(0,80),wait_mu=3)
    route=Route(1,[0,1],[RouteStop(node) for node in (0,1001,1,1002,2,0)])
    return instance,SimulatorConfig(50,1),route


def test_all_on_equivalence_and_candidate_cap():
    instance,physics,route=fixture()
    limits=BudgetConfig(max_candidate_evals=8,max_scenario_evals=131072,wall_seconds=5)
    args=dict(seed=20261122,samples=512)
    actual=optimize_component(instance,physics,route,limits,**args)
    frozen=optimize(instance,physics,route,"STaR",limits,**args)
    assert signature(actual,instance)==signature(frozen,instance)
    assert actual.budget["candidates_evaluated"]<=8


def test_single_toggles_use_expected_hooks(monkeypatch):
    instance,physics,route=fixture()
    original=Neighborhood.proposals
    calls=[]
    def proposals(self,*args,**kwargs):
        calls.append(kwargs["critical"])
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Neighborhood,"proposals",proposals)
    counts=[]
    extend=RouteEvaluator.extend
    def record(self,route,entry,count):
        counts.append(count)
        return extend(self,route,entry,count)
    monkeypatch.setattr(RouteEvaluator,"extend",record)
    limits=BudgetConfig(max_candidate_evals=12,max_scenario_evals=1500,wall_seconds=5)
    arguments=dict(seed=20261122,samples=512)
    optimize_component(instance,physics,route,limits,**arguments,prioritize=False)
    assert calls and not any(calls) and 128 in counts
    calls.clear()
    nas=optimize_component(instance,physics,route,limits,**arguments,analytical=False)
    assert all(calls) and nas.budget["screen_checks"]==nas.screen_rejections==0
    counts.clear()
    npp=optimize_component(instance,physics,route,limits,**arguments,prefix=False)
    assert counts and set(counts)=={512} and npp.prefix_rejections==0
    assert npp.budget["scenarios_evaluated"] in (512,1024)


def test_zero_station_and_tape_split():
    from numpy import array_equal
    from star_evrp.scenario_tapes import generate_z_tape

    instance,physics,_=fixture()
    source=Route(1,[0,1],[RouteStop(node) for node in (0,1,2,0)])
    args=dict(seed=20261122,samples=512)
    budget=BudgetConfig(max_candidate_evals=8)
    assert signature(optimize_component(instance,physics,source,budget,**args),instance)==signature(
        optimize(instance,physics,source,"STaR",budget,**args),instance)
    tape=generate_z_tape(20261122,instance.parent_key,instance.variant,1,"opt",512,3)
    assert array_equal(tape[:128,:1],generate_z_tape(20261122,instance.parent_key,instance.variant,1,"opt",128,1))
    assert not array_equal(tape,generate_z_tape(20261123,instance.parent_key,instance.variant,1,"holdout",512,3))
