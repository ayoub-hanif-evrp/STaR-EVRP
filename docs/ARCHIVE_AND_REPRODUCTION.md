# Archive recovery and reproduction

## Immutable research archive

| Reference | Value |
| --- | --- |
| Archival tag | `star-research-archive-v1` |
| Archival commit | `1ad987a328679263e5d8ba40330ffe1a11409db1` |
| Frozen optimizer tag | `star-phase3-freeze-v1` |
| Frozen optimizer commit | `c657aa69d55178c85b4759475933b36d1bcc2181` |

Recover the full Phase 1–8 tree (including historical `results/phase*` folders) in a separate worktree:

```powershell
git fetch --tags
git worktree add --detach ../STaR-EVRP-research-archive star-research-archive-v1
```

Exact optimizer reruns use the freeze tag in another worktree:

```powershell
git worktree add --detach ../STaR-EVRP-freeze star-phase3-freeze-v1
```

## Active package rebuild (no phase folders required)

Publication inputs live in `results/conference/data/inputs/` (extracted once from the archive before consolidation). Rebuild exhibits:

```powershell
$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
python -B scripts/build_conference_exhibits.py build --output results/conference
python -B scripts/build_conference_exhibits.py package --scratch results/conference_p9_work/zip_check
python -B -m pytest tests/test_conference_exhibits.py -q
```

To re-extract inputs, check out the archival worktree (phase folders present) and run `python -B scripts/extract_publication_inputs.py`.

## Historical reports at the archive revision

- `docs/PHASE3_FINAL_REPORT.md`, `docs/PHASE3_PRE_REGISTERED_ANALYSIS.md`
- `docs/PHASE5_FINAL_REPORT.md`, `docs/PHASE6_FINAL_REPORT.md`
- `docs/PHASE4_FINAL_REPORT.md`, conference refinement reports
- Result ZIPs under `results/phase5/`, `results/phase6/`, prior `results/conference/`

## Intentionally archived active tests

The following tests target historical phase trees and were removed from the active checkout after archive verification. Recover them from `star-research-archive-v1`:

- `tests/test_phase3.py`, `tests/test_phase4_results.py`
- `tests/test_phase5_results.py`, `tests/test_phase5_ablations.py`
- `tests/test_phase6_results.py`, `tests/test_phase6_math.py`
- `tests/test_phase25.py`
