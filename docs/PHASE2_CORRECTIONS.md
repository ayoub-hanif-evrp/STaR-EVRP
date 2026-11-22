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

**Phase 2.5 erratum:** Reliability matched (maximum absolute difference zero), but expected full completion increased on 46 of 127 routes. The largest change was RC2_10_1 A route 2: 2,324.31 to 6,858.58 benchmark time units, with reliability zero in both audits. The corrected simulator propagates every timing trajectory through the depot even after a deadline miss.
