# Figure Index — Phase 1

All figures are PNG at 400 DPI, generated from `results/raw/aggregate_routes.csv` and repair-probe JSON via:

```bash
python scripts/generate_figures.py
```

| Figure | File | Source data | Suggested caption |
|--------|------|-------------|-------------------|
| 1 | `results/figures/fig01_charging_exposure_by_family_variant.png` | `aggregate_routes.csv` (`num_charging_visits`, family, variant) | Fraction of CON baseline routes with 0, 1, or ≥2 charging visits by Homberger family and TW variant (Q=700, development set). |
| 2 | `results/figures/fig02_baseline_route_reliability.png` | `aggregate_routes.csv` (`reliability`) | ECDF of Monte Carlo route-success probability (N=2000 scenarios) for all routes vs charging-exposed routes; dashed line marks the 95% target. |
| 3 | `results/figures/fig03_slack_vs_reliability.png` | `aggregate_routes.csv` (`min_customer_slack`, `reliability`) | Minimum deterministic customer TW slack vs estimated reliability for charging-exposed routes. |
| 4 | `results/figures/fig04_station_waiting_time_risk.png` | station attributes via inventory / aggregate | Analytical lognormal expected wait and 95th percentile across stations (parameters from `*_stations.csv`). |
| 5 | `results/figures/fig05_failure_modes.png` | `aggregate_routes.csv` (`failure_mode`) | Relative frequencies of mutually exclusive failure-mode classifications. |
| 6 | `results/figures/fig06_repair_headroom.png` | `*__repair_probe.json` | Exploratory diagnostic: baseline vs best single-station replacement reliability under a fixed probe budget (not the final STaR algorithm). |
