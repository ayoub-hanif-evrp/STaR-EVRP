# Mathematical model (Phase 1)

## Physics

- Planar Euclidean distances; energy per leg \(h \cdot d\).
- Battery capacity \(Q\); consumption rate \(h\) from `ev_specs.json` (benchmark default \(Q=600\), \(h=1\)).
- Charging at station \(s\): add energy \(q\) at rate \(r_s\) from CSV → duration \(q/r_s\).
- Load capacity enforced at customers; fleet size caps route count.

## Visit order (explicit routes)

1. Travel leg (energy deducted).
2. Arrival clock update.
3. Early wait to station ready time (optional, `enforce_station_time_windows`).
4. Exogenous wait `wait_extra` (stochastic draws in Monte Carlo).
5. Charging to `energy_charged` or full if `None`.
6. Customer service: \(\max(\text{arrival}, \text{ready})\), then service time; check due date and depot closing.

Baseline CON expansion inserts nearest reachable stations with full recharge between customers (deposited parity).

## Stochastic layer

Lognormal waits \(W_{j} = \exp(\mu_j + \sigma_j Z_j)\), independent across visits. Route reliability is the fraction of scenarios with no timing violation under the fast timing evaluator (`stochastic_simulator`).