# Phase 6 writing-agent handoff

Use the [Phase 5 full benchmark](../results/phase5/STaR_EVRP_FINAL_RESULTS_HANDOFF.zip) and the [Phase 6 scientific supplement](../results/phase6/STaR_EVRP_PHASE6_SCIENTIFIC_SUPPLEMENT.zip) together. The former remains the authority for 120-instance performance, the original registered endpoint, surrogate baselines, ablations and archived competition. The latter adds five candidate figures, five table bundles, complete panel CSVs, mathematical verification, solver statuses and controlled timing.

## Claims and exhibits

- Keep the original STaR–FSPC primary and the original SLS reliability, work and elapsed caveats in the text. The Phase 6 FT-SAA comparison describes a different fixed panel with limited multi-visit certification and no new independent charging environments.
- F06-01 and F06-02 show route count transitions and pre-repair strata, with full signed effects, Wilson transition counts and parent influence in `data/`. Treat selected topology as descriptive.
- F06-03 shows restricted AS1 and empirical-versus-analytical reproducibility. Use the [mathematical audit](PHASE6_MATHEMATICAL_AUDIT.md) for theorem conditions.
- F06-04 discloses fixed-topology solver outcomes and the difference between completion and estimated reliability. F06-05 discloses the 50 ms primary and both sensitivity guards, including timing/work differences and overshoot.

Use [the exhibit index](../results/phase6/handoff/EXHIBIT_INDEX.csv), [claim matrix](../results/phase6/handoff/CLAIMS_MATRIX.csv), [numbers to cite](../results/phase6/handoff/NUMBERS_TO_CITE.csv), and [limitations](../results/phase6/handoff/LIMITATIONS_FOR_WRITER.md). All results and estimates added in Phase 6 are exploratory. No hybrid or separate prefix experiment was run.

## Reproduce or verify

Run from the repository root. `python -B scripts/run_phase6.py production --output <fresh-path>` records the prospective manifest, diagnostics, mathematical pretests, panel outcomes and independent replay. It intentionally takes fresh machine-dependent timings. To regenerate figures and tables without rerunning search, follow the root README's clean-rebuild commands. `audit` verifies inputs, figures and table formats. Final packaging also requires the actual proof, compilation, tests and cleanup evidence. The published `MANIFEST.json` and `audit/final_gate.json` bind the package to the frozen sources and actual output hashes.

See the [final report](PHASE6_FINAL_REPORT.md) and [cleanup report](PHASE6_REPOSITORY_CLEANUP.md). The full raw outcomes and ordered plan bundles live in the repository and are linked from the supplemental manifest.
