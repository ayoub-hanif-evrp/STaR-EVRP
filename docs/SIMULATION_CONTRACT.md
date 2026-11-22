# Simulation contract

## Independence

Each charging visit receives an **independent** lognormal wait sample. Repeated visits to the same physical station are separate draws. There is no fleet-wide queue state and no intentional spatial correlation.

## Route-level reliability

Reliability is the empirical success rate over scenarios for **one route** under the fixed stop sequence. It is not a fleet guarantee and not a confidence certificate unless Wilson intervals are reported explicitly.

Energy is treated as deterministic given the planned charging amounts; stochastic failures are **timing** failures (customer TW, depot closing) unless energy was already infeasible in the deterministic trace (`det_feasible` flag).

## Common random numbers (CRN)

- `make_rng(master_seed, "sim", instance_key, route_id)` derives deterministic sub-streams.
- `crn_wait_matrix(...)` pre-draws waits for scenario-aligned comparisons (e.g. repair probe baseline vs alternatives).

## Deterministic reference

With all `wait_extra = 0`, stochastic evaluation must coincide with deterministic timing on feasible zero-charge routes; charging routes match when waits are injected identically in `simulate_route_fixed`.