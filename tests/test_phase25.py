from dataclasses import replace

import numpy as np
import pytest

from star_evrp.budget import BudgetConfig, BudgetTracker
from star_evrp.charge_plan import ChargePlan
from star_evrp.competitive_search import METHODS, optimize
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.route_evaluator import RouteEvaluator
from star_evrp.route_validator import validate_repair
from star_evrp.scenario_tapes import generate_z_tape
from star_evrp.search_common import SearchCandidate
from star_evrp.statistics import wilson_ci, wilson_lower
from star_evrp.stochastic_simulator import evaluate_route_with_waits
from star_evrp.types import Route, RouteStop
from tests.conftest import make_synthetic_instance


def make_route(*nodes):
    return Route(route_id=4, stops=[RouteStop(node) for node in nodes])


def test_lexicographic_policy():
    route = make_route(0, 1, 0)
    score = lambda reliability, completion: SearchCandidate(route, True, reliability, completion).score_key(0.95)
    assert score(0.90, 120) > score(0.10, 10)
    assert score(0.95, 200) > score(0.94, 10)
    assert score(0.95, 100) > score(0.99, 101)


def test_complete_plan_identity_and_round_trip():
    instance = make_synthetic_instance()
    first = make_route(0, 1001, 1, 2, 0)
    second = make_route(0, 1, 1001, 2, 0)
    assert ChargePlan.from_route(instance, first).fingerprint() != ChargePlan.from_route(instance, second).fingerprint()
    second.stops[2].energy_charged = 1.0
    plan = ChargePlan.from_route(instance, second)
    second.stops[2].energy_charged = np.nextafter(1.0, 2.0)
    assert plan.fingerprint() != ChargePlan.from_route(instance, second).fingerprint()
    recovered = plan.to_route(instance, second.route_id)
    assert recovered.customer_indices == [0, 1]
    assert recovered.stops[2] == RouteStop(1001, 1.0)
    assert ChargePlan.from_route(instance, recovered) == plan


def test_reference_rejects_structural_errors():
    instance = make_synthetic_instance()
    physics = SimulatorConfig(50, 1)
    original = make_route(0, 1, 1001, 2, 0)
    for invalid in (make_route(0, 1, 2), make_route(0, 1, 0, 2, 0)):
        assert not simulate_route_fixed(instance, invalid, physics).feasible
        assert not evaluate_route_with_waits(instance, invalid, np.zeros(0), Q=50, h=1).success
    swapped = make_route(0, 2, 1001, 1, 0)
    swapped.customer_indices = [0, 1]
    assert not simulate_route_fixed(instance, swapped, physics).feasible
    with pytest.raises(ValueError):
        validate_repair(instance, original, swapped, physics)


def test_slot_tape_prefix_and_edit_mappings():
    short = generate_z_tape(43, "parent", "A", 4, "opt", 32, 1)
    long = generate_z_tape(43, "parent", "A", 4, "opt", 1024, 3)
    assert np.array_equal(short, long[:32, :1])
    assert not np.array_equal(long, generate_z_tape(43, "parent", "A", 4, "val", 1024, 3))
    assert not np.array_equal(long[:, 0], long[:, 1])
    instance = make_synthetic_instance(station_ids=[1001, 1002])
    instance.station_attributes[1002] = replace(instance.station_attributes[1002], wait_mu=2.0)
    first = make_route(0, 1001, 1, 2, 0)
    second = make_route(0, 1002, 1, 1001, 2, 0)
    eval_first = RouteEvaluator(instance, SimulatorConfig(50, 1), 43, "opt")
    eval_second = RouteEvaluator(instance, SimulatorConfig(50, 1), 43, "opt")
    left = eval_first._ensure_z_tape(first, 32, 1)
    right = eval_second._ensure_z_tape(second, 1024, 2)
    assert np.array_equal(left, right[:32, :1])
    first_wait = eval_first.prepare(first).timing.waits(left)[:, 0]
    second_wait = eval_second.prepare(second).timing.waits(right[:32])[:, 0]
    np.testing.assert_allclose(second_wait / first_wait, np.exp(3))


def test_incremental_scenarios_and_exact_caps():
    instance = make_synthetic_instance()
    route = make_route(0, 1, 1001, 2, 0)
    budget = BudgetTracker(BudgetConfig(max_candidate_evals=1, max_scenario_evals=32))
    evaluator = RouteEvaluator(instance, SimulatorConfig(50, 1), 77, "opt", budget)
    assert evaluator.evaluate_stochastic(route, 8).scenarios == 8
    assert evaluator.evaluate_stochastic(route, 32).scenarios == 32
    assert evaluator.evaluate_stochastic(route, 33).scenarios == 0
    assert evaluator.evaluate_stochastic(make_route(0, 1001, 1, 2, 0), 8).scenarios == 0
    assert budget.candidates_evaluated == budget.deterministic_checks == 1
    assert budget.scenarios_evaluated == 32


def test_vector_timing_and_bound_with_station_hours_and_lateness():
    instance = make_synthetic_instance(customer_tw=(14.0, 45.0), wait_sigma=0.0)
    index = instance.index_of(1001)
    instance.nodes[index] = replace(instance.nodes[index], ready_time=10.0, due_date=20.0)
    route = make_route(0, 1001, 1, 2, 0)
    physics = SimulatorConfig(50, 1, True)
    entry = RouteEvaluator(instance, physics, 7, "val").prepare(route)
    cap = entry.timing.isolated_caps(entry.trace)[0]
    waits = np.array([[0.0], [1.0], [cap + 1e-4], [300.0]])
    success, completion = entry.timing.evaluate(waits)
    for index, wait in enumerate(waits):
        ref = evaluate_route_with_waits(instance, route, wait, Q=50, h=1, enforce_station_time_windows=True)
        assert success[index] == ref.success
        assert completion[index] == pytest.approx(ref.completion)
    assert success[0] and not success[2]
    assert completion[3] > 300.0


def test_method_contracts_and_below_target_screen():
    instance = make_synthetic_instance(customer_tw=(0.0, 23.0), wait_mu=3.0)
    route = make_route(0, 1001, 1, 2, 0)
    physics = SimulatorConfig(50, 1)
    limits = BudgetConfig(wall_seconds=3, max_candidate_evals=12, max_scenario_evals=512)
    for method in METHODS:
        result = optimize(instance, physics, route, method, limits, seed=71, samples=128)
        validate_repair(instance, route, result.route, physics)
        assert result.budget["candidates_evaluated"] <= 12
        assert result.budget["scenarios_evaluated"] <= 512
        if method in ("B0", "B1", "B2"):
            assert result.budget["scenarios_evaluated"] == 0
        if method == "B4":
            assert [stop.node_id for stop in result.route.stops] == [stop.node_id for stop in route.stops]
    assert wilson_lower(960, 1000) > wilson_ci(960, 1000)[0]


def test_required_station_never_triggers_target_screen_while_below_target():
    instance = make_synthetic_instance(wait_mu=10.0, wait_sigma=0.0)
    route = make_route(0, 1, 2, 1001, 0)
    physics = SimulatorConfig(19.6, 1)
    limits = BudgetConfig(wall_seconds=2, max_candidate_evals=32, max_scenario_evals=4096)
    result = optimize(instance, physics, route, "STaR", limits, seed=71, samples=128)
    assert result.score[:3] == (1, 0, 0.0)
    assert result.budget["candidates_evaluated"] > 1
    assert result.budget["screen_checks"] == result.screen_rejections == 0


def test_joint_success_implies_all_isolated_caps_on_two_visits():
    instance = make_synthetic_instance(station_ids=[1001, 1002], customer_tw=(20.0, 48.0))
    route = make_route(0, 1001, 1, 1002, 2, 0)
    physics = SimulatorConfig(50, 1)
    entry = RouteEvaluator(instance, physics, 91, "val").prepare(route)
    caps = entry.timing.isolated_caps(entry.trace)
    waits = np.random.default_rng(13).uniform(0, 1.3 * caps, (5000, len(caps)))
    success, _ = entry.timing.evaluate(waits)
    assert success.any() and (~success).any()
    assert np.all(waits[success] <= caps)
