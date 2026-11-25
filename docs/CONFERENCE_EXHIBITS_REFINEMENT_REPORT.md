
# Conference exhibits refinement and cleanup

Phase 8 refines the publication handoff from `f243297cd60206b7ab75dcd52d38faf8bee73d5e`. The optimizer remains at `star-phase3-freeze-v1` (`c657aa69d55178c85b4759475933b36d1bcc2181`). STaR is the sole proposed method. All six archived primary-display methods and all four component removals are retained. The analytical single-visit and fixed-topology comparisons remain supplementary.

[Exhibit index](../results/conference/EXHIBIT_INDEX.csv) · [Writer ZIP](../results/conference/STaR_EVRP_CONFERENCE_EXHIBITS.zip) · [Captions](../results/conference/FIGURE_CAPTIONS.md) · [Table notes](../results/conference/TABLE_NOTES.md) · [Source traceability](../results/conference/SOURCE_TRACEABILITY.md)

## Revised exhibits

- **Figure 1.** The existing outcome-selected `C1_10_3/A/106` route keeps customers 851 and 731 in order. The maps use original coordinates and a shared zoom. Two battery profiles use the same scales and accumulate distance separately. The original charges 447.46 units at 1253 after its last customer and returns with 368.71 energy units. STaR charges 69.08 units at 1248 before its first customer and returns at zero within the frozen tolerance. The 378.38-unit charge reduction decomposes into 9.67 less travel energy and 368.71 less residual energy. The archived observed reliability is 3,063/10,000 and 10,000/10,000. The observed 100% is a finite-sample estimate. The full-return means are 1,826.22 and 1,394.79.
- **Figure 2.** The shorter workflow distinguishes guard termination, candidate retry, incumbent restart and independent validation. Six editable operator sketches keep customer order fixed. The source map records the analytical screen's incumbent condition, the finite-tape prefix bound, trial accounting and the actual lexicographic comparison.
- **Figures 3–5.** The registered holdout contrast is +1.24 pp [0.86, 1.65] over 2,321 exposed routes from 48 parents. Figure 3 names the fixed-station comparator for 160 higher, 2,050 equal and 111 lower recorded success counts. Figure 4 labels the descriptive complexity effects and the remaining routes below the Wilson attainment threshold. The 575 routes with 3+ original visits account for 89.0% of the net signed gain and 102/110 remaining nonattainments. Figure 5 distinguishes cooperative guards on the separate 118-route panel. At 50 ms, STaR used 44.52% fewer draws and the paired reliability and elapsed intervals both include zero.
- **Tables.** The setup gives both partition and parent counts. The main method table adds consumed candidate trials, including 62.67 for STaR and 20.18 for fixed-station repair at the same maximum of 64. The ablation table adds signed draw differences. The progressive-evaluation ablation has identical recorded route outcomes and uses about 5,903 more draws per route.
- **Supplementary figures.** `Sup01` shows `RC2_10_3/B/15`, selected at the lower-median eligible customer count from 149 improving, attaining R2/RC2 routes with changed topology. Its 44 customers keep their order. Both plans have four charging visits and observed reliability goes from 81.01% to 100.00%. `Sup02` shows the most adverse observed fixed-station comparison, `RC2_10_9/B/14`. STaR records 5 successes and fixed-station repair records 9,936 on the same tape. Customer-only failures account for both shortfalls. A deterministic paired slack profile shows where the saved charge reallocations change the schedule. It cannot identify which stochastic waits drove the outcome. Both examples are outcome-selected exploratory demonstrations. [Physical and timing notes](../results/conference/SUPPLEMENTARY_NOTES.md)

The full 120-instance benchmark includes development and remains descriptive. The model uses fixed customer order, deterministic travel and energy, linear charging, independent synthetic lognormal waits and disabled station hours. The same four station-attribute tables are reused across partitions. The results support neither a fleet guarantee nor claims of causal subgroup effects, global superiority, wall-time superiority or formal noninferiority. [Claims and limitations](../results/conference/CLAIMS_AND_LIMITATIONS.md)

## Cleanup and preservation

Four ignored directories contained no files: `results/phase6_pytest/` and its three abandoned test subdirectories. They were enumerated under temporary approval, checked for registered paths and junctions, and deleted individually. This removed **0 bytes of persistent file payload**. Nine ignored notebook checkpoints differ from their corresponding benchmark files and were retained. The inventory records each removal and retention, with separate checkout counters. The one new ignore rule applies only to the local Phase 8 proof and rebuild directory. No historical release, frozen result, dataset file or history object was deleted.

The 5,297-path Phase 7 baseline was reproduced before editing. After cleanup, 5,296 protected paths matched SHA-256 byte-for-byte and the remaining path, `.gitignore`, was verified against its exact expected one-rule addition. The Phase 5 and Phase 6 release manifests and all 21 original Phase 7 audit files also matched. The current audit is in `audit/phase8/`. The prior figures and table release can be recovered from the starting Git revision. [Cleanup inventory](../results/conference/audit/phase8/cleanup_inventory.csv) · [Preservation audit](../results/conference/audit/phase8/preservation.json)

Phase 8 also removed its own working copies, proofs, temporary installs and test fixtures after verification. These 1,657 generated files occupied 121,212,514 bytes and are counted separately from the persistent cleanup. [Scratch cleanup](../results/conference/audit/phase8/scratch_cleanup.json)

## Verification and reproduction

The build uses the archived Phase 1–6 evidence. Its only executed route computations are deterministic checks of the six saved plans across the three examples, with no new optimizer or stochastic validation campaign. Both clean builds must reproduce the same derived file hashes. The proof harness uses the bundled DejaVu Sans fonts and compiles the three fragments at 178 mm. All artwork uses the same 178 mm design width and remains legible in reduced and grayscale proofs. Figure 5 is the first candidate for supplementary placement if space is tight. The ten-page plan assumes references count toward the limit. Final pagination was not tested because no venue template was supplied.

Run from the repository root with the versions in the preflight. Use a fresh subdirectory under the local scratch root for each build.

```powershell
python -B scripts/build_conference_exhibits.py build --output results/conference_p8_work/rebuild
python -B -m pip install --target results/conference_p8_work/pdf_tools pypdfium2==5.15.2
python -B scripts/build_conference_exhibits.py audit --output results/conference_p8_work/rebuild --pdf-tools results/conference_p8_work/pdf_tools
python -B scripts/build_conference_exhibits.py proofs --output results/conference_p8_work/rebuild --pdf-tools results/conference_p8_work/pdf_tools
python -B -m pytest -p no:cacheprovider -q
```

Nine focused tests and all 101 tests passed. Two clean builds matched 88 derived files byte for byte. The three LaTeX proofs compiled without overfull boxes or missing characters, and each of the seven figures was reviewed as a PNG, PDF and SVG. The safe ZIP extraction check verified each member by SHA-256. The Git commit containing this report identifies the release. [Final gates](../results/conference/audit/phase8/final_gates.json) · [ZIP envelope](../results/conference/audit/phase8/zip_envelope.json)
