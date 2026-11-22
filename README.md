# STaR-EVRP

**STaR-EVRP** (Slack-Targeted Stochastic Charging Repair) studies whether changing charging decisions—without changing customer sequences—can improve route-level reliability of electric delivery routes under stochastic charging-station waiting times.

Phase 1 (this codebase state) builds the reproducible scientific foundation: dataset ingestion, deposited CON baselines, deterministic/stochastic simulation, safe reliability upper bounds, a limited repair-opportunity probe, tests, PNG figures, and paper tables.

Primary protocol: **Q = 700**, **h = 1.0**, development set = 24 instances. See `docs/PHASE1_FINAL_REPORT.md` for gate decisions and measured results.

## Dataset

Place / keep the published archive at:

`dataset/EVRPTW_ChargingStations_Dataset/`

Do not modify original dataset files. Citation details are in that folder’s `README.md`.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e .
```

Requires Python 3.11+.

## Reproduction

From the project root:

```bash
python scripts/inspect_dataset.py
python scripts/generate_baselines.py --config configs/pilot.yaml
python scripts/run_pilot.py --config configs/pilot.yaml
python scripts/run_repair_probe.py --config configs/pilot.yaml
python scripts/generate_figures.py
python scripts/generate_tables.py
python scripts/audit_results.py
python -m pytest -q
```

Runs are resume-safe (completed JSON artifacts are skipped).

## Layout

- `src/star_evrp/` — core library
- `configs/` — experiment YAML (`pilot.yaml`)
- `scripts/` — CLI entry points
- `tests/` — automated tests (41 passing)
- `results/` — baselines, raw audits, figures, tables, reports
- `docs/` — model, protocol, limitations, Phase 1 final report

## Phase 1 gates (summary)

| Gate | Decision |
|------|----------|
| G0 Reproducible foundation | **PASS** |
| G1 Meaningful stochastic risk | **PASS** (strong) |
| G2 Charging repair headroom | **PASS** (limited but positive) |

Full evidence: `docs/PHASE1_FINAL_REPORT.md`.
