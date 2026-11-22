# STaR_v1 Phase 2 method summary

## Problem

Fixed customer sequence and depot structure; optimize charging stops and energy amounts for `R(p) >= 0.95` minimizing full-route expected completion `E[T_return]`.

## Modules

| Module | Role |
|--------|------|
| `charge_plan.py` | Fingerprints and customer-order helpers |
| `scenario_tapes.py` | Shared Z tapes; `W = exp(mu + sigma*Z)` |
| `route_evaluator.py` | Det check, progressive 64→256→1024, cache |
| `charge_moves.py` | replace/remove/insert/relocate/charge_amount/two_edit |
| `safe_screen.py` | Certified vs exploration rejection |
| `criticality.py` | Visit/gap prioritization |
| `budget.py` | Wall/candidate/scenario caps |
| `search_common.py` | Lexicographic incumbent |
| `star_optimizer.py` | STaR_v1 + ablation flags |
| `baseline_optimizers.py` | B0–B3 fair baselines |

## Incumbent policy

1. Deterministic feasibility  
2. Target reliability on optimization estimate  
3. Minimize `E[T]`; else maximize `R`, then min `E[T]`

## Baselines

- **B0** NoRepair  
- **B1** MeanWait-Greedy  
- **B2** UniformQuantile  
- **B3** FullScenario-LS (SA note in docstring; no fake ALNS)

Configs: `configs/phase2_smoke.yaml`, `phase2_dev.yaml`, `phase2_ablation.yaml`. Holdout remains sealed (`development_only: true`).