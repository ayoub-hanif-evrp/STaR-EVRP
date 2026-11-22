"""Deposited CON baseline smoke test and coverage."""

from __future__ import annotations

from star_evrp.baseline import generate_baseline
from star_evrp.data_loader import discover_dataset_root, load_ev_specs, load_single_instance
from star_evrp.route_validator import validate_solution
from star_evrp.types import Route, Solution

from tests.conftest import PROJECT_ROOT, make_synthetic_instance


def test_con_smoke_real_instance():
    inst = load_single_instance(PROJECT_ROOT, "C1_10_1", "A")
    ev = load_ev_specs(discover_dataset_root(PROJECT_ROOT / "dataset"))
    Q = 700.0
    h = ev.energy_consumption_rate
    sol = generate_baseline(inst, Q, h, method="CON", project_root=PROJECT_ROOT)
    assert sol.feasible is True
    served = set()
    for route in sol.routes:
        if route.customer_indices:
            for loc in route.customer_indices:
                assert 0 <= loc < inst.num_customers
                assert loc not in served
                served.add(loc)
    assert served == set(range(inst.num_customers))
    assert sol.total_distance is not None and sol.total_distance > 0


def test_missing_and_duplicate_customers_detected():
    inst = make_synthetic_instance(num_customers=3)
    from star_evrp.deterministic_simulator import SimulatorConfig

    cfg = SimulatorConfig(
        battery_capacity=inst.ev_specs.battery_capacity,
        energy_consumption_rate=0.1,
    )
    sol = Solution(
        instance_key=inst.instance_key,
        variant="A",
        method="TEST",
        battery_capacity=cfg.battery_capacity,
        energy_consumption_rate=cfg.energy_consumption_rate,
        routes=[Route(route_id=0, customer_indices=[0, 0, 1])],
    )
    report = validate_solution(inst, sol, config=cfg)
    assert not report.feasible
    assert any("Duplicate" in i.message or "Missing" in i.message for i in report.issues)