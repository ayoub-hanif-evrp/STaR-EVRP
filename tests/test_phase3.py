import numpy as np

from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.phase3 import phase_cases, validation
from star_evrp.phase3_analysis import boot
from star_evrp.types import Route, RouteStop
from tests.conftest import PROJECT_ROOT, make_synthetic_instance


def test_holdout_partition_never_splits_parent():
    _, rows = phase_cases(PROJECT_ROOT)
    dev = {row["parent_key"] for row in rows if row["partition"] == "development"}
    holdout = {row["parent_key"] for row in rows if row["partition"] == "holdout"}
    assert len(dev) == 12 and len(holdout) == 48 and not dev & holdout


def test_phase3_zero_station_replay_and_full_completion():
    instance = make_synthetic_instance()
    route = Route(2, [0, 1], [RouteStop(node) for node in (0, 1, 2, 0)])
    physics = SimulatorConfig(50, 1)
    trace = simulate_route_fixed(instance, route, physics)
    options = {"validation_seed": 7, "stress_seed": 8, "validation_samples": 128,
               "validation_scalar_checks": 5, "target": .95}
    result = validation(instance, route, trace, physics, options, scalar=True)
    assert result["successes"] == result["n"] == 128
    assert result["completion"] == trace.end_clock and result["mean_customer_tardiness"] == 0
    assert result == validation(instance, route, trace, physics, options, scalar=True)


def test_phase3_correlated_stress_and_customer_failure():
    instance = make_synthetic_instance(wait_mu=9.0, customer_tw=(0, 80))
    route = Route(2, [0, 1], [RouteStop(node) for node in (0, 1001, 1, 1001, 2, 0)])
    physics = SimulatorConfig(50, 1)
    trace = simulate_route_fixed(instance, route, physics)
    options = {"validation_seed": 9, "stress_seed": 10, "validation_samples": 512,
               "validation_scalar_checks": 11, "target": .95}
    result = validation(instance, route, trace, physics, options, stress={"scale": 1.25, "sigma": 1, "rho": .35}, scalar=True)
    assert result["successes"] == 0 and result["late_both"] == 512
    assert result["completion"] > instance.depot_closing_time


def test_cluster_bootstrap_targets_different_weightings():
    rows = [("parent1", 1.), ("parent1", 1.), ("parent2", -1.), ("other_family", 0.)]
    parents = [("parent1", "F1"), ("parent2", "F1"), ("other_family", "F2")]
    output = boot(rows, parents, 18, 4096)
    assert np.isclose(output[0], .25) and np.isclose(output[3], 0.)
    assert output == boot(rows, parents, 18, 4096)
    assert output[1] <= output[0] <= output[2]
