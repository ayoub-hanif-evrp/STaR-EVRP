# STaR-EVRP audited results package

**Read first:** 96 paired A/B holdout problems from 48 parents; 6,864 total CON routes, 2,321 initially exposed and 4,543 no-charge. All c64 methods use the same exposed routes. The only confirmatory contrast is STaR minus B4 c64 mean reliability: +1.24 pp [0.86, 1.65]. B4 completed fewer candidate trials despite the same maximum. STaR used 34.59% fewer search draws than B3 but was slower. It is a narrow benefit, not general dominance.

## Use the package

Start with T01–T03 and F01–F03; use F04/F05 together when discussing effort. T04 gives both caps and the second seed; it does not increase the parent sample. F06 and T05 show hard-family limitations; F07/T06 distinguish topology strata from the separate no-partial ablation. F08/T07 are synthetic, fixed-plan stresses. Supplementary plots show the registered hard route, Wilson uncertainty and the consumed-trial distribution.

Use EXHIBIT_INDEX, FIGURE_CAPTIONS, TABLE_NOTES, CLAIMS_MATRIX and NUMBERS_TO_CITE as the writing interface. See LIMITATIONS_FOR_WRITER before using any statistic. Dataset citation pointers are in the original benchmark README and Phase 3 documentation; no new bibliographic claims are made here.

## Provenance and reproduction

Frozen executable `c657aa69d55178c85b4759475933b36d1bcc2181`; source publication `149d9f4d8f616d78ce0c295696515f1bbc342967`. The audit uses the dataset SHA-256 inventory, archived JSON-gzip plan/validation records and the frozen analysis design. No new optimization or random stress setup. Reported Phase 3 runtime is archived, not measured again in Phase 4.

Run `python -B scripts/run_phase4_results.py all` from the repository root; options `--project-root` and `--output` support a clean external replay. Directly use the archived CON zip; no patch or extraction to Phase 3 is needed. Use the same software versions for bytewise PNG reproduction. See MANIFEST for exact source references. Main/supplementary figures are already rendered at 400 DPI and intended physical width; the table fragments use booktabs, graphicx, and longtable for long appendices.
