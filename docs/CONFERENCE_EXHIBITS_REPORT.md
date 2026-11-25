# Conference exhibits release

**Decision.** The five figures and three tables are ready for the paper-writing agent at 178 mm double-column width. STaR remains the proposed algorithm. The venue template and final pagination are outside this package.

The build used the immutable Phase 3 freeze `c657aa69d55178c85b4759475933b36d1bcc2181`, the reviewed Phase 5 and Phase 6 releases, and the original benchmark. The preflight began at `d17616177b61cb98e11c1cd5408d7c981fae2b21`. All 5,297 protected paths matched their preflight hashes. No new optimization, stochastic evaluation, solver campaign or manuscript work was performed. The release commit identifies the final package.

## Canonical exhibits

| Stem | Purpose and provenance |
| --- | --- |
| `Fig01_spatial_charging_repair` | Whole benchmark instance and two matched route details from original coordinates and archived ordered plans. |
| `Fig02_star_framework` | Frozen incumbent, proposal, screening, prefix and first-improvement control flow, with source-line map. |
| `Fig03_paired_reliability` | Registered holdout comparison and scenario-search context, with parent-cluster intervals and observed paired directions. |
| `Fig04_charging_complexity` | Holdout effect and residual nonattainment by original station-visit count. |
| `Fig05_quality_simulation_effort` | Separate exploratory Phase 6 timing panel, six observed work/quality points and paired reliability intervals. |
| `Tab01_experimental_configuration` | Benchmark, partition, model, budgets and statistical protocol. |
| `Tab02_method_comparison` | Six archived holdout methods; all time measurements are from the original c64 cohort. |
| `Tab03_component_ablation` | Full STaR and the four component removals under matched holdout denominators. |

The [exhibit index](../results/conference/EXHIBIT_INDEX.csv) points to the final files. PNGs are 400 DPI with 2,803 px width. PDFs use embedded TrueType fonts and retain extractable text. SVGs retain editable text and paths. The LaTeX fragments use booktabs and legible native-size alignment. Table CSVs retain full-precision values; Markdown and TeX use shared display rounding. Figures use a common DejaVu Sans visual system with redundant marker/line encodings.

## Numerical cross-checks

- The flagship map chose **C1_10_3/A/106**, the first by customer count, case and route ID among 274 eligible restorations. The ordered customers are 851 then 731. The old visit to 1253 charged 447.4601742508004 units and the new visit to 1248 charged 69.07831527821554. Archived successes were **3,063/10,000** and **10,000/10,000**. Mean full return was **1,826.22** and **1,394.79** native units. This is an outcome-selected example.
- The primary cohort holds **96 instances, 48 parents and 2,321 exposed routes**. The complete benchmark has **120 instances, 60 parents, 8,606 routes and 2,891 exposed**. The registered reliability fraction reproduced **0.012420292977165015**, with interval **[0.008630955453232267, 0.016503459913289817]**. Matched FSPC direction counts were **160 higher, 2,050 ties, 111 lower**. The primary comparison keeps the actual work imbalance visible.
- The holdout source-visit bins contain 1,587, 159 and 575 routes, with 4, 4 and 102 STaR nonattainments. The 3+ bin contributes 89.0% of the signed overall reliability gain. This is an observed association.
- The separate 118-route timing panel contains 2,124 archived repeats. At 50 ms, STaR used 44.52% fewer draws than scenario search. Paired reliability and elapsed intervals include zero. Cooperative overshoots and the 20 ms wall-time result are disclosed.
- Per-route joint checks confirmed identical reliability, attainment and mean full return for full STaR and the no-progressive-evaluation ablation. STaR uses about 5,903 fewer draws per holdout route. The AS1 and FT-SAA results remain in the preserved supplementary evidence.

## Acceptance and verification

| Gate | Evidence |
| --- | --- |
| C7-G0 | Preflight and preservation records; exact baseline and freeze; protected historical hashes |
| C7-G1 | Archive reconciliation, full-precision data, recorded bootstraps, split and repeat keys |
| C7-G2 | Independently checked CON ZIP and frozen selected plan, real coordinates, common zoom and diagram checklist |
| C7-G3 | Audited raster and vector structure plus inspected native, reduced and grayscale proof renders |
| C7-G4 | Three matching table bundles and a Tectonic compile at 178 mm, with PDF print proofs inspected |
| C7-G5 | Seven focused and 99 full-suite tests, two clean byte-identical rebuilds, and missing-input rejection |
| C7-G6 | Sorted portable ZIP, manifest, verified safe extraction, source-linked captions and writer disclosure |

See [final audit](../results/conference/audit/final_gates.json), [visual record](../results/conference/audit/visual.json) and [ZIP envelope](../results/conference/audit/zip_envelope.json). Initial visual reviews shortened a clipped direction header, separated the STaR workflow boxes and connected the retry loop, moved spatial annotations away from the route legs and made zero lines visible. Tectonic's local cache lacked the default bold font. The proof harness uses the bundled DejaVu Sans font files inside scratch. A subsequent paragraph-width warning was resolved by suppressing indentation on the fragments and using ragged-right configuration cells. The failed compiler transcripts are retained. Publication proof PDFs and images were rendered independently with PDFium.

## Reproduction

Run from the repository root with Python 3.12.10 and the versions recorded in the Phase 7 preflight. Build uses the existing environment. PDF inspection uses `pypdfium2==5.15.2` and Tectonic 0.16.9. The renderer is an audit tool, separate from the frozen dependencies. These commands regenerate outputs from archived evidence.

```powershell
python -B scripts/build_conference_exhibits.py build --output results/conference_rebuild
python -B -m pip install --target results/conference_pdf_tools pypdfium2==5.15.2
python -B scripts/build_conference_exhibits.py audit --output results/conference_rebuild --pdf-tools results/conference_pdf_tools
python -B scripts/build_conference_exhibits.py proofs --output results/conference_rebuild --pdf-tools results/conference_pdf_tools --scratch results/conference_proofs
python -B -m pytest -p no:cacheprovider -q
```

Build and audit support separate output folders with `--output`. Proof or package extraction uses `--scratch` outside the release directory. The packaging command expects passed test, rebuild, visual and compilation evidence. The committed [conference handoff](../results/conference/STaR_EVRP_CONFERENCE_EXHIBITS.zip) contains the five figures, three tables, writer notes and exact sources. Use it with the existing Phase 5 and Phase 6 handoffs.
