# STaR-EVRP Phase 1 Final Scientific Report

**Project:** Slack-Targeted Stochastic Charging Repair for Large-Scale Electric Vehicle Routing with Time Windows  
**Phase:** Foundation (Prompt 1 of 3)  
**Primary configuration:** \(Q=700\), \(h=1.0\), development set = 24 instances (12 parents × variants A/B)  
**Date:** 2026-11-22  

---

## 1. Executive summary

Phase 1 built a reproducible experimental foundation for STaR-EVRP and answered the four foundation research questions on the official EVRPTW heterogeneous charging-station dataset.

**What was completed**

- Full Python package `star_evrp` with dataset discovery/parsing, independent route validation, deterministic + stochastic simulation, safe isolated-wait reliability upper bounds, CON baseline generation (deposited solver), limited repair-opportunity probe, experiment runners, figures, and tables.
- Automated tests: **41 passed**.
- Development pilot: **24/24** baselines feasible; **24/24** stochastic audits; **1,742** routes evaluated with **2,000** Monte Carlo scenarios per charging-exposed route.
- Six publication-quality PNG figures and six paper-ready tables (CSV / MD / TeX).

**Key measured findings (development set, Q=700, CON)**

| Quantity | Value |
|----------|-------|
| Routes | 1,742 |
| Charging-exposed routes | 570 (**32.7%**) |
| Mean reliability (all routes) | **0.9185** |
| Mean reliability (exposed) | **0.7509** |
| Exposed routes below 95% target | **197 / 570 (34.6%)** |
| Dominant exposed failure modes | customer TW (134), depot return (56) |
| Repair probe | 40 unreliable routes examined; 36 with ≥1 det. alternative; 67 improving candidates; 17 candidates meeting 95% |

**Gate decisions:** **G0 PASS**, **G1 PASS (strong evidence)**, **G2 PASS (limited but positive headroom)**. Proceeding to Prompt 2 is scientifically justified.

---

## 2. Dataset inventory and integrity

**Source:** Hanif et al. EVRPTW Heterogeneous Charging Stations dataset  
`dataset/EVRPTW_ChargingStations_Dataset/` (DOI data descriptor + Zenodo deposit).

| Component | Status |
|-----------|--------|
| Instances | 120 (60 parents × variants A/B), 1,000 customers each |
| Stations per instance | 333 (from `params.json`) |
| Families | C1, C2, R1, R2, RC1, RC2 (10 parents each) |
| Structural validation | 0 malformed instances in loader audit |
| Split | Lexicographic first 2 parents/family → development (24); remainder holdout (96) |
| Provenance | SHA-256 of instance + station files recorded in baselines / inventory |

Frozen inventory: `results/manifests/dataset_inventory.json`.  
Development parents (lexicographic): `*_10_1` and `*_10_10` for each family (e.g. `C1_10_1`, `C1_10_10`).

**Honesty note:** Waiting-time and price parameters are **synthetic** lognormal attributes for benchmarking; they are **not** measured Moroccan (or other real) charging queues.

---

## 3. Deterministic baseline methodology and reproducibility

Baselines use the **deposited CON constructive solver** in `dataset/.../code/evrptw_solvers.py`, wrapped by `star_evrp.baseline`:

1. Convert typed `Instance` → deposited NumPy instance dict.
2. Run `constructive_solve_with_routes` at \(Q=700\), \(h=1.0\).
3. Expand customer sequences to **explicit** depot–customer–station–depot stop lists via nearest-station full-recharge expansion matching deposited `_simulate_route`.
4. Independently validate with `route_validator.validate_solution`.

**Label:** method `CON` / `CON_deposited` — **not** claimed as bit-exact paper table replication without published route files.

**Development results:** 24/24 solutions independently feasible; mean ~72.6 vehicles; mean ~45.3 charging stops per solution; mean runtime ~12.0 s/instance.

Artifacts: `results/baselines/*__{A,B}.json`.

Regenerate:

```bash
python scripts/generate_baselines.py --config configs/pilot.yaml
```

---

## 4. Published-baseline parity assessment

| Claim | Assessment |
|-------|------------|
| Paper: CON/HC feasible for 60/60 at Q=700 | Our CON is **feasible on all 24 development instances** at Q=700 |
| Exact distance / vehicle counts vs paper CSV | **Not demonstrated** — deposited `run_baseline_solvers.py` aggregates only; no serialized official routes were imported |
| HC | Implemented wrapper exists; pilot primary method is **CON** for speed/transparency |

`ev_specs.json` lists `battery_capacity: 600`; Phase 1 **primary protocol uses Q=700** as specified in Prompt 1. This difference is intentional and documented.

---

## 5. Model assumptions and simulation semantics

Documented in `docs/MATHEMATICAL_MODEL.md` and `docs/SIMULATION_CONTRACT.md`.

- Travel time = Euclidean distance (native units).
- Energy \(e_{ij}=h\,d_{ij}\) with \(h=1\).
- Full recharge at stations in baseline expansion; explicit plans store `energy_charged`.
- Visit order: travel → arrival → (optional station ready wait, default **off** to match deposited code) → **stochastic queue wait** → charge → depart.
- Customer service start \(B_i=\max(a_i,A_i)\), hard due dates.
- Stochastic waits: independent lognormal draws per charging **visit** (same physical station on different visits = independent draws).
- Route success = all customer TW + depot closing satisfied under the sampled waits.
- Reliability is **route-level**, not fleet-level.

---

## 6. Stochastic reliability findings

Configuration: 2,000 scenarios/route, seed `20261122`, Wilson 95% CIs.

Raw: `results/raw/*__audit.json`, `results/raw/aggregate_routes.csv`.

| Population | N | Mean reliability | Frac. below 0.95 |
|------------|---|------------------|------------------|
| A — all routes | 1,742 | 0.9185 | ~11% (mostly from exposed) |
| B — charging-exposed | 570 | 0.7509 | **34.6%** |
| C — exposed & <0.95 | 197 | (by definition below) | 100% |

Zero-charge routes (1,172) have reliability = deterministic feasibility indicator (=1.0 here). Averaging all routes **hides** substantial risk in Population B — reporting separates populations as required.

Safe upper bound \(U(p)\): among exposed routes, mean \(U\approx 0.758\); **197** routes have `safe_reject=True` (\(U<0.95\)), matching the count below the MC target in this pilot (bound is a necessary-condition screen, not a certificate of success).

---

## 7. Charging-exposure findings (RQ0.1 / RQ0.3)

Overall exposure: **32.7%** of routes visit ≥1 station.

By family (see Fig. 1):

- **C1:** almost no charging (~2% exposed) at Q=700.
- **C2 / R1 / RC1:** moderate exposure (mostly 0–1 charge).
- **R2 / RC2:** **high** exposure; majority of routes have **2+** charges.

Failure modes (mutually exclusive classification):

| Mode | Count |
|------|------:|
| no_stochastic_exposure | 1,172 |
| high_reliability_charging | 373 |
| customer_time_window_failures | 134 |
| depot_return_failures | 56 |
| customer_and_depot_failures | 5 |
| uncertainty_near_threshold | 2 |

R2 shows the lowest mean exposed reliability (~0.50–0.55). Variant B (relaxed due dates) often improves exposed reliability vs A for the same family, but R2 remains fragile.

---

## 8. Repair-opportunity findings (RQ0.4 / Gate G2)

Limited probe (not STaR): up to 5 geographic neighbor station replacements per visit + optional charge removal; customer order fixed; diagnostic N=500 scenarios.

Aggregated over 9 instances with unreliable charging routes:

| Metric | Value |
|--------|------:|
| Unreliable routes examined | 40 |
| With ≥1 deterministic alternative | 36 (90%) |
| Improving candidate evaluations | 67 |
| Candidates meeting 95% | 17 |
| Best observed reliability gain (instance max) | up to 1.0 |

Interpretation:

- Basic charging changes **often** improve reliability on Type-1 / mixed families.
- On **R2**, many candidates improve reliability but **none of the probed candidates met 95%** within the fixed budget — headroom exists but is harder; full STaR search is warranted.
- Absence of a better candidate in this probe **does not** prove irreparability.

Artifacts: `results/raw/*__repair_probe.json`, Fig. 6, Table 5.

---

## 9. Mathematical screening validation

See `docs/SAFE_SCREENING_MATHEMATICS.md`.

- Isolated wait \(\tau_j\): conservative binary/exponential search (returns feasible `lo`, never overestimates \(\tau\)).
- \(U(p)=\min_j F_j(\tau_j)\) with published lognormal CDF.
- Unit tests (`test_risk_bounds.py`) verify toy cases and no unsafe rejection near the 95% threshold under constructed examples.
- Passing \(U\ge 0.95\) is **not** a reliability certificate; failing \(U<0.95\) **is** a valid necessary-condition rejection under the independence/marginal wait model.

---

## 10. Runtime and computational environment

See `results/reports/environment.json`.

| Item | Value |
|------|-------|
| OS | Windows 11 (10.0.26200) |
| Python | 3.12.10 |
| NumPy / SciPy / Matplotlib | 2.5.3 / 1.18.1 / 3.11.2 |
| Pilot wall time (resume run) | ~207 s for remaining baselines + audits |
| Scenarios | 2,000 / charging route |
| Seeds | scenario `20261122`; baseline seed `20261122` |

---

## 11. Figure and table inventory

**Figures (PNG only):**

1. `results/figures/fig01_charging_exposure_by_family_variant.png`
2. `results/figures/fig02_baseline_route_reliability.png`
3. `results/figures/fig03_slack_vs_reliability.png`
4. `results/figures/fig04_station_waiting_time_risk.png`
5. `results/figures/fig05_failure_modes.png`
6. `results/figures/fig06_repair_headroom.png`

Index: `docs/FIGURE_INDEX.md`.

**Tables (CSV + MD + TeX):**

1. `table01_dataset_characteristics.*`
2. `table02_deterministic_baseline.*`
3. `table03_stochastic_reliability.*`
4. `table04_reliability_by_family_variant.*`
5. `table05_repair_probe.*`
6. `table06_validation.*`

---

## 12. Statistical and scientific limitations

1. Development set only (24 instances); holdout reserved for future confirmatory work.
2. CON baselines — not HC/ILS quality; charging plans inherit nearest-station greedy insertion.
3. Independent visit waits (no queue coupling across fleet vehicles).
4. Station time windows not enforced in deposited baseline semantics (matched here).
5. Repair probe is exploratory with a fixed budget — not an optimality claim.
6. Monte Carlo estimates are sampling noise-aware via Wilson CIs; near-threshold routes (n=2) left unclassified as confident.
7. Primary battery Q=700; lower Q (e.g. 600) would increase exposure but was not substituted into the primary protocol.

---

## 13. Research gates G0 / G1 / G2

### Gate G0 — Reproducible foundation — **PASS**

Evidence:

- Dataset loads (120/120).
- CON routes generated + independently validated (24/24 feasible).
- Stochastic simulator + risk bounds operational.
- **41/41 tests passed** (`results/reports/pytest_summary.txt`).
- Raw JSON/CSV artifacts regenerable via scripts.

### Gate G1 — Meaningful stochastic risk — **PASS (strong)**

Evidence:

- Non-trivial charging exposure (**32.7%** of routes; extreme on R2/RC2).
- **34.6%** of exposed routes below 95% reliability.
- Clear family structure (R2 worst; C1 nearly unexposed at Q=700).
- Failures are timing (TW / depot), not fabricated energy noise.

Classification: **strong** evidence that stochastic waiting materially hurts charging-exposed routes under this dataset and Q=700 CON baselines.

### Gate G2 — Charging repair headroom — **PASS (limited but positive)**

Evidence:

- 90% of examined unreliable routes had ≥1 deterministic charging alternative.
- Multiple reliability-improving candidates; 17 met the 95% target under the probe.
- R2 shows improvement headroom without easy 95% attainment → motivates a smarter slack-targeted search (STaR).

Not a claim that STaR already outperforms literature methods.

---

## 14. Exact reproduction commands

From the project root `STaR-EVRP/`:

```bash
pip install -e .
python scripts/inspect_dataset.py
python scripts/generate_baselines.py --config configs/pilot.yaml
python scripts/run_pilot.py --config configs/pilot.yaml
python scripts/run_repair_probe.py --config configs/pilot.yaml
python scripts/generate_figures.py
python scripts/generate_tables.py
python scripts/audit_results.py
python -m pytest -q
```

Runs are resume-safe (existing baseline/audit JSON files are skipped).

---

## 15. Known unresolved problems

1. Table 1 currently emphasizes partition counts; richer per-family station TW/wait summaries can be expanded further for the paper draft.
2. HC full development sweep was not the primary pilot method (CON only).
3. Repair probe CRN across station replacements uses related seeds rather than shared Z with remapped \((\mu,\sigma)\); sufficient for exploratory diagnosis, refine in Prompt 2.
4. Exact numerical parity with published CON/HC aggregate CSV was not pursued as a hard gate.

---

## 16. Recommendations for Prompt 2 (STaR algorithm)

1. **Focus search on charging-exposed, low-\(U(p)\) / low-MC-reliability routes**, especially R2/RC2.
2. Use **safe rejection** (\(U(p)<0.95\)) to prune hopeless plans before expensive MC.
3. Prioritize **slack-targeted** insertion/relocation of charges near critical visits (isolated \(\tau_j\) / downstream slack).
4. Support **partial charging** (simulator already accepts explicit `energy_charged`).
5. Keep customer sequences fixed; evaluate with **CRN** and a held-out confirmatory seed stream.
6. Do **not** tune on the holdout set; freeze development decisions first.
7. Report Populations A/B/C separately in all method comparisons.
8. Treat C1 at Q=700 as a near-zero-exposure control family, not the primary repair benchmark.

---

## Bottom line

Phase 1 establishes that, on this dataset at \(Q=700\), stochastic station waiting creates **real route-level unreliability** concentrated in charging-exposed routes, and that **charging-only edits can improve reliability** on a meaningful fraction of those routes. The software foundation is tested, auditable, and ready for Prompt 2 algorithm development.
