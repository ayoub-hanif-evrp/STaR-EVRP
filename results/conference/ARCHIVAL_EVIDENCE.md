# Archival evidence (text-only disclosures)

These comparisons are **not** plotted or tabulated in the active four-method publication package.
They remain part of the scientific record and must be cited in prose with links to the archive.

Archive tag `star-research-archive-v1` · commit `1ad987a328679263e5d8ba40330ffe1a11409db1` · freeze `c657aa69d55178c85b4759475933b36d1bcc2181` (`star-phase3-freeze-v1`).

## Registered confirmatory contrast (STaR − FSPC)

- Holdout, profile c64, reliability: **+1.24 pp [0.86, 1.65]** on 2,321 exposed routes / 48 parents.
- Exact: +1.242029 pp [+0.863096, +1.650346].
- Status: confirmatory.
- Actual mean trials: 62.67 vs 20.18 (common maximum 64).
- Source: `results/phase5/data/paired_effects.csv` · `star-research-archive-v1:results/phase5/data/paired_effects.csv`.

## Exploratory scenario search (STaR − SLS)

- Holdout reliability contrast: **+0.32 pp** (exact +0.318798 pp [+0.133384, +0.492799]).
- Search draws: STaR 13,024 vs SLS 19,911
  (34.59% fewer for STaR).
- Wall time: 29.69 vs 27.51 ms (STaR vs SLS).
- Source: `results/phase5/data/paired_effects.csv` · `star-research-archive-v1:results/phase5/data/paired_effects.csv`.

## Phase 6 restricted / uncertain comparisons

### AS1 (113-route one-visit panel)

- Contrast: AS1 minus STaR.
- Reliability: -0.0176 pp [-0.0589, +0.0217] (crosses zero).
- Completion difference: -14.0398 native units.
- Note: AS1 restricted to at most one visit; reliability interval crosses zero; exploratory.
- Source: `results/phase6/data/as1_paired_effects.csv` · `star-research-archive-v1:results/phase6/data/as1_paired_effects.csv`.

### FT-SAA (118-route fixed-topology panel)

- Contrast: STaR minus FT-SAA.
- Reliability: -0.3844 pp [-1.1827, +0.0497].
- Completion difference: -44.4527 native units.
- Note: Five of 22 multi-visit cases obtained complete MILP certificates; valid fallbacks remain; exploratory.
- Source: `results/phase6/data/fixed-topology_paired_effects.csv` · `star-research-archive-v1:results/phase6/data/fixed-topology_paired_effects.csv`.

## Scope reminders

Do not assert superiority over optimal fixed topology, a general runtime advantage, noninferiority, or causal
subgroup mechanisms. Do not present CON/MWR/QBR/STaR as the only methods ever tested. Recover full Phase 1–8
trees via `docs/ARCHIVE_AND_REPRODUCTION.md`.
