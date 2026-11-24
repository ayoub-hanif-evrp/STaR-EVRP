# Final writing-agent results handoff

Start with `results/phase5/handoff/README_RESULTS_PACKAGE.md` and `results/phase5/STaR_EVRP_FINAL_RESULTS_HANDOFF.zip`. Use T01–T06 for the streamlined CON/MWR/QBR/STaR presentation and ablations; **include T07 or its numeric claims in the main text**. T07 discloses the archived original primary STaR–FSPC contrast, the SLS trade-off and actual trial imbalance. The supplementary methods were not excluded from the evaluation. No manuscript is part of this handoff.

- `results/phase5/data/instance_results.csv`: all 1,200 instance-method records, original route counts, matched exposed outcomes, uncertainty, work distributions and runtime cohort. See `population_by_instance.csv` for original five-way coverage (partition, parent, variant, family, instance).
- `results/phase5/data/paired_effects.csv`, `paired_routes.csv`, `route_results.csv`, `family_ablation.csv` and `failure_modes.csv`: complete full-precision comparisons, including losses and ties.
- `results/phase5/handoff/METHOD_GLOSSARY.md`, `FIGURE_CAPTIONS.md`, `TABLE_NOTES.md`, `CLAIMS_MATRIX.csv`, `NUMBERS_TO_CITE.csv` and `EXHIBIT_INDEX.csv`: acronym and statistical contract.
- `results/phase5/manifests/protocol.json` describes the pre-execution method, hardware and source checks. The source map hashes the archive links and new batches. The audit separates archived holdout controls from new measurements. Only the original holdout STaR–FSPC reliability is confirmatory.

## Reproduce and validate

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B scripts/run_phase5.py all
python -B -m pytest -q -p no:cacheprovider tests/test_phase5_ablations.py tests/test_phase5_results.py
python -B -m pytest -q -p no:cacheprovider
```

The CLI also accepts `preflight`, `run-development`, `run-ablations`, `replay`, `analyze`, `build-exhibits`, `audit`, and `package`. Use the matching six-worker setting if replaying execution; Windows may require access to multiprocessing pipes. The packaged source CON ZIP is read directly; there is no need to extract or modify Phase 3. Resumption validates the protocol and exact keys, never reoptimizes already saved controls. Working-tree text hashes record exact producer bytes.

For a clean derived rebuild, copy only Phase 5 `raw/`, `plans/`, `manifests/` and `audit/` to an empty `results/phase5_repeat`, then run `analyze --output results/phase5_repeat` and `build-exhibits --output results/phase5_repeat`. With the captured test logs and hash-bound visual review, `python -B scripts/finalize_phase5.py` compares both derived trees and publishes the release envelope and writer ZIP. Archived timing is not recomputed during exhibit builds. Tables use booktabs, graphicx and longtable in a one-column appendix where applicable.
