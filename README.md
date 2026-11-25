# STaR-EVRP

Slack-Targeted Stochastic Charging Repair (STaR) optimizes station visits and charge amounts on fixed customer routes. The model uses deterministic travel and energy, linear charging and synthetic lognormal waits. Reliability is the chance of meeting all customer service-start and depot deadlines on a route. Completion includes late trajectories. Station operating hours, endogenous queues, fleet reassignment and dynamic recourse are outside the model.

## Results

| Evidence | Where to start |
| --- | --- |
| **Conference figures and tables** | [Exhibit index](results/conference/EXHIBIT_INDEX.csv) · [Publication handoff ZIP](results/conference/STaR_EVRP_CONFERENCE_EXHIBITS.zip) |
| **Phase 5 authoritative 120-instance comparison and ablations** | [Report](docs/PHASE5_FINAL_REPORT.md) · [Figures](results/phase5/figures) · [Tables](results/phase5/tables) · [Handoff ZIP](results/phase5/STaR_EVRP_FINAL_RESULTS_HANDOFF.zip) |
| **Phase 6 supplementary mathematics and experiments** | [Report](docs/PHASE6_FINAL_REPORT.md) · [Mathematical audit](docs/PHASE6_MATHEMATICAL_AUDIT.md) · [Figures](results/phase6/figures) · [Tables](results/phase6/tables) · [Supplement ZIP](results/phase6/STaR_EVRP_PHASE6_SCIENTIFIC_SUPPLEMENT.zip) |
| **Phase 3 registered evidence** | [Analysis plan](docs/PHASE3_PRE_REGISTERED_ANALYSIS.md) · [Results](docs/PHASE3_FINAL_REPORT.md) · [Reproduction](docs/PHASE3_REPRODUCIBILITY.md) |
| **Phase 4 independent reconciliation** | [Audit report](docs/PHASE4_FINAL_REPORT.md) |
| **Historical foundation and development** | [Phase 1](docs/PHASE1_FINAL_REPORT.md) · [Phase 2](docs/PHASE2_FINAL_REPORT.md) · [Phase 2.5](docs/PHASE25_FINAL_REPORT.md) |

The registered comparison is STaR versus FSPC on the original holdout. Phase 5 also reports SLS, ablations and the combined benchmark. Phase 6 comparisons are exploratory and reuse the existing parents and waiting model.

**Method acronyms.** CON is the deposited constructive baseline, MWR is mean-wait repair, QBR is quantile-based repair, SLS is scenario-based local search, and FSPC is fixed-station partial charging. AS1 is the Phase 6 zero/one-visit analytical optimizer and FT-SAA is its fixed-topology sample-average comparator. See the [full glossary](results/phase5/handoff/METHOD_GLOSSARY.md) for ablations and internal IDs.

## Reproduce results

Use Python 3.12.10 and the dependency versions in the [Phase 3 freeze](results/phase3/manifests/freeze.json) and [Phase 6 protocol manifest](results/phase6/manifests/protocol.json) for archive equivalence. Install with `python -m pip install -e .`. Use a clean scratch directory for each rebuild. The following PowerShell commands regenerate derived exports from archived outcomes. They retain archived times.

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -B -m pytest -p no:cacheprovider -q

New-Item -ItemType Directory results/phase5_repeat
Copy-Item results/phase5/raw,results/phase5/plans,results/phase5/manifests,results/phase5/audit results/phase5_repeat -Recurse
python -B scripts/run_phase5.py analyze --output results/phase5_repeat
python -B scripts/run_phase5.py build-exhibits --output results/phase5_repeat

New-Item -ItemType Directory results/phase6_rebuild
Copy-Item results/phase6/raw,results/phase6/plans,results/phase6/manifests,results/phase6/audit results/phase6_rebuild -Recurse
Remove-Item -LiteralPath results/phase6_rebuild/audit/diagnostics.json
python -B scripts/run_phase6.py diagnose --output results/phase6_rebuild
python -B scripts/run_phase6.py replay --output results/phase6_rebuild
python -B scripts/run_phase6.py analyze --output results/phase6_rebuild
python -B scripts/run_phase6.py build-exhibits --output results/phase6_rebuild
```

For a frozen Phase 3 optimization reproduction, check out `star-phase3-freeze-v1` in a separate worktree and follow the Phase 3 instructions. The historical replay CLI expects the extracted `raw/con` bundles. For Phase 4 onward the verified readers open [the CON archive](results/phase3/con_bundles.zip) directly. To restore it for the old CLI in a scratch copy, use `python -m zipfile -e results/phase3/con_bundles.zip DESTINATION`. On Windows use an absolute `\\?\`-prefixed destination if the reserved directory name prevents extraction. Never stage the extracted folder. See the [Phase 6 handoff](docs/PHASE6_RESULTS_HANDOFF.md) for execution and audit commands.

## Repository map

- [dataset](dataset/EVRPTW_ChargingStations_Dataset) contains the original benchmark and metadata.
- [src](src/star_evrp), [configs](configs), [scripts](scripts) and [tests](tests) contain implementations, study settings, entry points and verification.
- [docs](docs), [prompts](prompts) and [results](results) contain study protocols, research records and immutable released outcomes.
