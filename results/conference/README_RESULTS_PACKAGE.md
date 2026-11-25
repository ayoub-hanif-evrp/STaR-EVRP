# STaR-EVRP conference exhibits (Prompt 09)

Exactly **four** main figures (panels 2/2/2/1) and **three** main tables. No methodology artwork.
Active comparison methods: CON, MWR, QBR, STaR only.

| Stem | Panels |
| --- | ---: |
| Fig01_spatial_charging_repair | 2 |
| Fig02_comparative_reliability | 2 |
| Fig03_charging_complexity | 2 |
| Fig04_progressive_evaluation | 1 |

Build from the immutable snapshot in `data/inputs/` (no Phase 3/5/6 tree required for ordinary rebuild):

```text
python -B scripts/build_conference_exhibits.py build --output results/conference
```

Start with `EXHIBIT_INDEX.csv`, `FIGURE_CAPTIONS.md`, `TABLE_NOTES.md`, `CLAIMS_AND_LIMITATIONS.md`,
and `ARCHIVAL_EVIDENCE.md`. Figures: 400 DPI PNG, vector PDF (embedded fonts), editable SVG (live text).
Width 178 mm. Font: DejaVu Sans (`FONT_LICENSE.txt`).

Holdout primary population: 96 instances / 48 parents / 2,321 exposed routes. The 120-instance descriptive
coverage is retained for writer context only. Archive recovery: `docs/ARCHIVE_AND_REPRODUCTION.md`.
Snapshot archive commit `1ad987a328679263e5d8ba40330ffe1a11409db1`; freeze `c657aa69d55178c85b4759475933b36d1bcc2181`.
