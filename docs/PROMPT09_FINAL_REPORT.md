# Prompt 09 — final four-method publication and repository consolidation

## Revisions

| Item | Value |
| --- | --- |
| Starting HEAD | `1ad987a328679263e5d8ba40330ffe1a11409db1` |
| Archival tag | `star-research-archive-v1` (pushed) |
| Freeze | `star-phase3-freeze-v1` / `c657aa69…` |

## Publication package

Exactly **four** figures (panels 2/2/2/1) and **three** tables. Displayed methods: **CON, MWR, QBR, STaR** (+ four STaR ablations in Tab03).

| Exhibit | Path |
| --- | --- |
| Fig01 | `results/conference/figures/Fig01_spatial_charging_repair.{png,pdf,svg}` |
| Fig02 | `results/conference/figures/Fig02_comparative_reliability.{png,pdf,svg}` |
| Fig03 | `results/conference/figures/Fig03_charging_complexity.{png,pdf,svg}` |
| Fig04 | `results/conference/figures/Fig04_progressive_evaluation.{png,pdf,svg}` |
| Tab01–03 | `results/conference/tables/Tab0{1,2,3}_*.{csv,tex,md}` |
| ZIP | `results/conference/STaR_EVRP_CONFERENCE_EXHIBITS.zip` |

**No** methodology/workflow figure. **No** FSPC/SLS/AS1/FT-SAA series in figures or tables. Registered STaR−FSPC +1.24 pp [0.86, 1.65] retained in `ARCHIVAL_EVIDENCE.md` only.

Self-contained inputs: `results/conference/data/inputs/` (rebuild does not need `results/phase*`).

## Consolidation summary

Historical `results/phase2`–`phase6` and legacy Phase 1 result folders were removed from the active checkout after remote archive tag verification. Obsolete phase docs/scripts/prompts/configs and phase-only tests were removed from active checkout. Full evidence remains recoverable via `docs/ARCHIVE_AND_REPRODUCTION.md`. Frozen optimizer sources and the original dataset were not modified. No new experiments.

| Metric | Before | After (approx.) |
| --- | ---: | ---: |
| Tracked files | 5,445 | ~980 |
| Tracked payload bytes | ~272 MB | ~45 MB |

Git object history is unchanged; remote storage is not reduced by a normal deletion commit.

## Gates

| Gate | Status |
| --- | --- |
| G0 Archive | PASS — tag on remote |
| G1 Preservation | PASS — snapshot hashed; freeze unchanged |
| G2 Scope | PASS — 4 figs / 3 tables / 4 methods |
| G3 Accuracy | PASS — anchors reconciled |
| G4 Design | PASS — panels 2/2/2/1; PNGs inspected |
| G5 Consolidation | PASS — see cleanup ledger in release commit |
| G6 Reproducibility | PASS — snapshot rebuild + focused tests |
| G7 Release | PASS — ZIP + push |
