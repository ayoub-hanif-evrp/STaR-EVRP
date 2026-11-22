"""Synthetic STaR_v1 smoke optimization."""

from __future__ import annotations

from star_evrp.baseline_optimizers import B0_no_repair, B3_full_scenario_ls
from star_evrp.budget import BudgetConfig
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.star_optimizer import STaRConfig, optimize_route_star
from star_evrp.types import Route, RouteStop

from tests.conftest import make_synthetic_instance


def _charging_route(inst):
    sid = inst.station_node_ids[0]
    return Route(
        route_id=0,
        customer_indices=[0],
        stops=[
            RouteStop(node_id=0),
            RouteStop(node_id=sid, energy_charged=None),
            RouteStop(node_id=1),
            RouteStop(node_id=0),
        ],
    )


def test_star_smoke_runs_within_budget():
    inst = make_synthetic_instance(wait_mu=-1.2, wait_sigma=0.3, charging_rate=6.0)
    Q = inst.ev_specs.battery_capacity
    cfg = SimulatorConfig(battery_capacity=Q, energy_consumption_rate=0.22)
    route = _charging_route(inst)
    budget = BudgetConfig(
        wall_seconds=8.0,
        max_candidate_evals=15,
        max_scenario_evals=800,
        progressive_stages=(8, 16),
        validation_scenarios=32,
    )
    star_cfg = STaRConfig(budget=budget, nearby_stations=2, master_seed=11)
    report = optimize_route_star(inst, route, cfg, star_cfg)
    assert report.incumbent is not None
    assert report.incumbent.det_feasible
    assert report.candidates_examined >= 1
    assert report.budget["scenarios_evaluated"] <= budget.max_scenario_evals + 1

    b0 = B0_no_repair(inst, route, cfg, target=0.95, master_seed=11, budget_cfg=budget)
    assert b0.incumbent is not None
    b3 = B3_full_scenario_ls(
        inst, route, cfg, target=0.95, master_seed=11, budget_cfg=budget, sa_restarts=1
    )
    assert b3.incumbent is not None