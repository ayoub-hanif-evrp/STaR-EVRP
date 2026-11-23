# Phase 4 exhibit captions and notes

The definitive stand-alone figure captions are in `results/phase4/handoff/FIGURE_CAPTIONS.md`. The table notes and definitions are in `results/phase4/handoff/TABLE_NOTES.md`. Use `results/phase4/handoff/EXHIBIT_INDEX.csv` to associate captions with exact files, audited data sources, methods, counts and required caveats.

- **Confirmatory F01/T03:** paired STaR–B4 c64 route-weighted reliability difference only. Resample parents with both A/B variants and all their routes together within family. A parent-balanced mean changes the weighting, not the population, and is sensitivity analysis only.
- **F02/F06/T01/T02:** probability is not the fraction of routes meeting the individual criterion; LB is a pointwise one-sided 95% Wilson lower limit of at least 0.95. Two-sided Wilson target-straddling is a separate diagnostic.
- **F03:** native full-completion time includes late trajectories. Paired clouds represent saved route estimates, not confidence intervals.
- **F04/F05/T04:** report plan and scenario ceilings for every profile and absolute consumed work; no interpolation across mixed constraints or seeds. Timing reflects the archived six-worker configuration.
- **F07/F08:** no-partial ablation and topology strata address distinct questions; numerical contributions are not causal. Synthetic stresses preserve all selected plans without reoptimization.
- **Registered route S01:** chosen by frozen parent/route ordering, not by performance. Include the overlap between B4 and STaR rather than describing the example as a topology success.
