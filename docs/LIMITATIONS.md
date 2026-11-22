# Limitations (honest scope)

1. **Waits are synthetic parameters**, not empirical Moroccan (or other) queue traces.
2. **Independent lognormal waits** omit spatial, temporal, and cross-vehicle queue coupling.
3. **Route-level 95% reliability** does not imply fleet-level 95% service quality.
4. **`U(p)` safe screen** provides necessary infeasibility only; high \(U(p)\) does not certify success.
5. **Repair probe** tries single-station edits; it is diagnostic, not the final STaR optimizer.
6. **Baseline parity** reuses deposited CON/HC; exact reproduction of published numbers is **not** claimed.
7. **Q=700 vs Q=600** mismatch between pilot runs and `ev_specs.json` must be tracked in metadata.
8. **Station TW enforcement** is off by default to match deposited simulator behavior.
9. **Synthetic unit-test instances** must never be mixed into benchmark result tables.
10. **Figure/table scripts** require populated `results/raw/`; empty pilots yield empty or skipped charts.