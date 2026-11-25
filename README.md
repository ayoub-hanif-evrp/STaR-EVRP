# STaR-EVRP

Slack-Targeted Stochastic Charging Repair (STaR) retunes station visits and charge amounts on **fixed** customer routes under synthetic lognormal station waits. Reliability is the chance of meeting all customer and depot timing constraints on a route. Completion includes late trajectories.

## Publication package (Prompt 09)

Displayed comparative methods: **CON**, **MWR**, **QBR**, and **STaR**, plus four STaR component ablations. Exactly four main figures (panels 2/2/2/1) and three main tables. There is **no** generated methodology figure.

Start here:

- [Exhibit index](results/conference/EXHIBIT_INDEX.csv)
- [Captions](results/conference/FIGURE_CAPTIONS.md) · [Table notes](results/conference/TABLE_NOTES.md)
- [Claims and limitations](results/conference/CLAIMS_AND_LIMITATIONS.md)
- [Archival disclosures (FSPC/SLS/Phase 6)](results/conference/ARCHIVAL_EVIDENCE.md)
- [Handoff ZIP](results/conference/STaR_EVRP_CONFERENCE_EXHIBITS.zip)
- [Prompt 09 report](docs/PROMPT09_FINAL_REPORT.md)

Primary quantitative population: **96-instance original holdout**, 48 parents, **2,321** charging-exposed routes. The 120-instance benchmark includes 24 development instances and is descriptive only.

Registered confirmatory contrast (text disclosure only): **STaR − FSPC +1.24 pp [0.86, 1.65]**. See `ARCHIVAL_EVIDENCE.md`.

## Rebuild exhibits

```powershell
$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
python -m pip install -e .
python -B -m pytest tests/test_conference_exhibits.py -q
python -B scripts/build_conference_exhibits.py build --output results/conference
```

Inputs are self-contained under `results/conference/data/inputs/`. No network and no historical phase folders are required for an ordinary rebuild.

## Historical research archive

Full Phase 1–8 evidence (including deleted active `results/phase*` trees) is pinned at tag **`star-research-archive-v1`**. Recovery commands: [docs/ARCHIVE_AND_REPRODUCTION.md](docs/ARCHIVE_AND_REPRODUCTION.md). Frozen optimizer: tag `star-phase3-freeze-v1`.

## Repository map

- `dataset/` — original EVRPTW charging-station benchmark
- `src/star_evrp/` — frozen core + publication builders
- `configs/` — frozen and split configuration
- `scripts/` — supported build/extract/check entry points
- `tests/` — core + publication tests
- `docs/` — model, archive recovery, Prompt 09 release notes
- `results/conference/` — active publication package
- `prompts/PROMPT_09_…` — binding publication instruction
