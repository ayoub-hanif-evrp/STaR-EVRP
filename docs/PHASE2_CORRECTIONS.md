# Phase 2 corrections status (P0)

Baseline audited commit: `39a49b12d86fc4f4bfb7966ae1c36bf624ca8212`. Phase 1 artifacts under `results/` are preserved. Corrected semantics and all new experiments live under `results/phase2/`.

| ID | Issue | Status | Evidence |
|----|-------|--------|----------|
| P0-A | Safe bound must use **upper** bracket `tau_upper ≥ τ*` | **Done** | `risk_bounds.py` returns infeasible upper + outward slack; `+inf` if never infeasible; `docs/PHASE2_SAFE_BOUND_PROOF.md`; `tests/test_phase2_safe_bound_upper.py` |
| P0-B | Overcharge / negative charges must be **rejected** | **Done** | `_charge_at_station` and `evaluate_route_with_waits`; `tests/test_battery_feasibility.py` |
| P0-C | Full-route completion after early TW failure | **Done** | `evaluate_route_with_waits` continues to depot; `tests/test_phase2_full_route_metrics.py` |
| P0-D | Fast vs reference semantics | **Done** | Stochastic path uses shared `evaluate_route_with_waits` with `enforce_station_time_windows`; station TW default off |
| P0-E | Probe route-level counts + CRN | **Done** | `repair_probe.py` reports `routes_with_improvement` / `routes_meeting_target`; Phase 2 uses `scenario_tapes` Z-sharing |
| P0-F | CI classifications + LaTeX escaping | **Done** | `classify_failure_mode` CI labels; `_latex_escape_cell` in table writer |

## D1 numerical crosswalk

File: `results/phase2/raw/d1_crosswalk.csv` (127 panel routes, N=2000).

On this panel, recomputed reliability and expected completion matched the Phase 1 stored aggregate values (max absolute reliability difference = 0). The P0-C fix remains required for correctness on truncated early-failure trajectories (unit-tested) and for any future metrics that previously early-stopped.