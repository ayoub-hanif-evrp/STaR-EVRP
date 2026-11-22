# STaR-EVRP Phase 2 Final Scientific Report

**Project:** Slack-Targeted Stochastic Charging Repair (STaR-EVRP)  
**Phase:** Algorithm development + fair development-set experiments  
**Primary config:** Q=700, h=1.0, target route reliability 0.95  
**Holdout:** sealed (96 instances unused)  
**Date:** 2026-11-22  

---

## 1. Head SHA, environment, dataset, split

| Item | Value |
|------|-------|
| Phase 1 audited commit | `39a49b12d86fc4f4bfb7966ae1c36bf624ca8212` |
| Python | 3.12.10 |
| Platform | Windows 11 |
| NumPy / SciPy | 2.5.3 / 1.18.1 |
| Dataset | `dataset/EVRPTW_ChargingStations_Dataset/` |
| Split | Frozen Phase 1 development (24) / holdout (96) |
| Experiment panel | 127 charging-exposed development routes (`results/phase2/manifests/dev_panel.json`) |
| Freeze file | `results/phase2/manifests/phase2_freeze.json` |

Tests at Phase 2 completion: **49 passed**.

---

## 2. P0 corrections (point-by-point)

See also `docs/PHASE2_CORRECTIONS.md` and `docs/PHASE2_SAFE_BOUND_PROOF.md`.

| ID | Verdict | Summary |
|----|---------|---------|
| **P0-A** | Fixed | Isolated-wait search returns **upper** infeasible bracket (+slack); `U=min F(τ_upper)`; product bound also reported. Legacy lower-bracket helper retained only for counterexample tests. |
| **P0-B** | Fixed | Explicit charges that overfill capacity or are negative/NaN are **rejected**, never clipped. |
| **P0-C** | Fixed | Stochastic evaluator continues to final depot after customer/depot misses; records full completion and all-customer tardiness. |
| **P0-D** | Fixed | Shared `evaluate_route_with_waits` honors station-TW flag; primary protocol keeps station TW off. |
| **P0-E** | Fixed | Probe summaries count **distinct routes**; Phase 2 CRN shares **Z**, not W. |
| **P0-F** | Fixed | Failure modes use CI-based labels; LaTeX table cells escape `_ % & #`. |

**D1 crosswalk (Phase 2.5 erratum):** `results/phase2/raw/d1_crosswalk.csv`. On the 127-route panel (N=2000), reliability matched Phase 1 (max |Δrel|=0), but full completion increased on 46 routes, by up to 4,534.27 benchmark time units. Historical Phase 1 completion can reflect early termination and must not be used as full-route completion.

---

## 3. Final model and search semantics

- Customer order, vehicle assignment, and hard TWs fixed.
- Charging edits only: replace / remove / insert / relocate / partial charge / bounded two-edit.
- Success: all customer latest starts and depot return respected under sampled waits.
- Objective (lex): deterministic validity → meet 0.95 on opt estimate → minimize E[full completion]; else maximize reliability then minimize completion.
- Costs always use **full-route** completion times.

---

## 4. STaR_v1 algorithm (summary)

1. Start from CON charging plan.  
2. Criticality / slack targeting of visits and gaps.  
3. Restricted neighborhood (geo + reachability + rate/wait attributes).  
4. Deterministic energy/TW filter.  
5. Certified rejection when `U_min < 0.95` (exploration mode retains below-target improvers).  
6. Progressive MC under matched Z tapes (64→256).  
7. Lex incumbent update; budget stop.  
8. Independent validation on `val` tape (N=2000 in this freeze).

Details: `docs/PHASE2_METHOD.md`, `src/star_evrp/star_optimizer.py`.

**Budgets (fair across methods):** wall 25s / route, ≤50 candidate evals, stages [64,256], val 2000 — `configs/phase2_dev.yaml`.

---

## 5. Baselines and fairness

| Method | Role |
|--------|------|
| B0 NoRepair-CON | Stochastic evaluation of unchanged CON plan |
| B1 MeanWait-Greedy | Same moves; score with arithmetic mean waits |
| B2 UniformQuantile | Same moves; uniform risk budget heuristic |
| B3 FullScenario-LS | Same moves; progressive MC local search |
| STaR_v1 | Proposed hybrid |

All share the same start solution, neighborhood generators, physics, scenario distribution, and computational caps. No customer reordering. No holdout leakage.

---

## 6. Development results (127 exposed panel routes)

Raw: `results/phase2/raw/dev/` (635 JSON = 127×5). Aggregate: `results/phase2/processed/phase2_aggregate.csv`.

### Main comparison (independent validation)

| Method | Mean rel (val) | Meet target (val CI) | Mean E[T] | Mean runtime (s) |
|--------|----------------:|---------------------:|----------:|-----------------:|
| B0 | 0.741 | 62 / 127 | 3825 | 0.15 |
| B1 | 0.882 | 102 / 127 | 3648 | 0.75 |
| B2 | 0.883 | 103 / 127 | 3663 | 0.73 |
| B3 | 0.875 | 101 / 127 | 3684 | 0.77 |
| **STaR_v1** | **0.882** | **103 / 127** | 3692 | **0.28** |

### Repair-eligible subset (B0 reliability < 0.95): n=65

| Method | Meet val CI | Improved vs B0 |
|--------|------------:|---------------:|
| B0 | 0 | 0 |
| B1 | 40 | 43 |
| B2 | 41 | 44 |
| B3 | 39 | 43 |
| STaR_v1 | 41 | 41 |

### Family stress (STaR_v1 val-CI attainment)

| Family | Meet / N |
|--------|---------:|
| C1 | 7 / 7 |
| C2 | 24 / 24 |
| R1 | 24 / 24 |
| RC1 | 24 / 24 |
| RC2 | 13 / 24 |
| **R2** | **11 / 24** |

**Honest finding:** STaR_v1 matches the best baselines on attainment while being **~2.5–3× faster**. It does **not** dominate MeanWait-Greedy/UniformQuantile on reliability under this budget. R2 remains hard (11/24).

### Ablations (762 results)

| Ablation | Meet val CI | Mean rel | Mean runtime |
|----------|------------:|---------:|-------------:|
| STaR_v1 | 103 | 0.882 | 0.32 |
| STaR_no_reject | 101 | 0.875 | 0.40 |
| STaR_no_criticality | 103 | 0.882 | 0.68 |
| STaR_no_progressive | 103 | 0.882 | 0.37 |
| STaR_single_edit | 103 | 0.882 | 0.33 |
| **STaR_no_partial** | **84** | **0.796** | 0.22 |

**Decisive component:** partial charging — removing it drops attainment from 103→84.

---

## 7. Paired statistics

Parent/route pairing vs B0 is the analysis unit. Method-level means above are over the same 127 routes. Near-threshold routes use Wilson lower bounds for CI certification; point estimates ≥0.95 without lower-bound clearance are not labeled certified.

Tables: `table12_paired_statistical_analysis.*`.

---

## 8. Screening and computation

Certified rejection is mathematically a necessary-condition screen (upper bracket). Ablation without rejection remains competitive (101 meets) with slightly higher runtime — screening is not the sole driver of STaR’s speed advantage (cheap ranking + progressive eval also matter).

---

## 9. Figures and tables

**PNG figures (10):** `results/phase2/figures/fig07` … `fig16` — index in `docs/PHASE2_FIGURE_INDEX.md`.

**Tables (8 families, csv/md/tex):** `table07` … `table14` under `results/phase2/tables/`.

Audit: `python scripts/audit_phase2_results.py` → `ok: true`, 635 dev results, no issues.

---

## 10. Reproduction commands

```bash
pip install -e .
python -m pytest -q
python scripts/run_phase2_smoke.py --config configs/phase2_smoke.yaml
python scripts/run_phase2_d1_reconcile.py --config configs/phase2_dev.yaml
python scripts/run_phase2_development.py --config configs/phase2_dev.yaml --panel-only
python scripts/run_phase2_ablations.py --config configs/phase2_ablation.yaml
python scripts/build_phase2_figures.py
python scripts/build_phase2_tables.py
python scripts/audit_phase2_results.py
```

Resume-safe: existing per-route/method JSON files are skipped.

---

## 11. Acceptance gates

| Gate | Decision | Rationale |
|------|----------|-----------|
| **P2-G0 Correctness** | **PASS** | Upper-bound screen, overcharge reject, full-route metrics, 49 tests green |
| **P2-G1 Method completeness** | **PASS** | STaR_v1 + B0–B3 ran on 127 exposed panel routes with shared budgets |
| **P2-G2 Development evidence** | **PASS** | Full panel comparison, independent val, ablations, negatives (R2), paired stats |
| **P2-G3 Paper presentation** | **PASS** | 10 PNG figures + 8 table families from raw JSON |
| **P2-G4 Phase 3 readiness** | **PASS** | Freeze manifest + readiness doc; holdout sealed; no holdout run |

---

## 12. Phase 3 holdout specification (not executed)

See `docs/PHASE2_READINESS.md`. Do not open holdout performance until Prompt 3.

---

## 13. Conference-paper recommendation

**Yes, with honest framing.**

Evidence supports a charging-only repair paper that:

1. Fixes and certifies the stochastic evaluation/screen foundation.  
2. Shows large reliability gains vs unrepaired CON on exposed routes.  
3. Demonstrates STaR_v1 is **competitive with strong same-neighborhood stochastic baselines at lower compute**, with partial charging as a critical component.  
4. Transparently reports **R2 nonattainment** and that simple MeanWait/UniformQuantile baselines are strong under equal budgets.

Do **not** claim STaR uniquely dominates all baselines on development attainment. Prefer the efficiency–reliability trade-off and mechanistic ablation as the scientific contribution heading into holdout confirmation.

---

## Limitations

- Panel (127 routes), not all 570 exposed routes (disclosed budget-limited balanced sample per Prompt §10).  
- Validation N=2000 (config freeze); prompt’s 5000 is available by raising `validation_scenarios`.  
- B4 ALNS-Lite not claimed; B3 covers strong scenario LS.  
- Working-tree Phase 2 code may postdate the Phase 1 git SHA until committed.  
- Holdout unused by design.
