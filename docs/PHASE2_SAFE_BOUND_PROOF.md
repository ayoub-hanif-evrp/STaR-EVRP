# Phase 2 safe bound proof sketch

## Event

Route success requires all customer latest-service-start deadlines and depot return under stochastic waits `W_j` at charging visits `j = 1..K`.

## Isolated wait upper bracket

For visit `j`, let `tau*` be the supremum wait such that the route remains deterministic-time feasible when only visit `j` waits. Bisection maintains feasible `lo` and infeasible `hi`. The **safe upper** is `tau_upper = hi + epsilon` so `tau* <= tau_upper`.

For lognormal waits, `P(W_j <= tau*) <= P(W_j <= tau_upper) = F_j(tau_upper)`.

## Dependence-robust bound

Joint success requires all visits simultaneously tolerable; a necessary condition is each visit below its threshold:

`R(p) <= min_j F_j(tau_upper_j) = U_min`.

Under independence, `R(p) <= prod_j F_j(tau_upper_j) = U_indep <= U_min`.

## Safe rejection

If `U_min < target`, no policy with the same charging plan can reach target reliability under the isolated-wait model. This is **never** an acceptance certificate.

## P0-A correction

Phase 1 returned feasible `lo` as `tau`, yielding `F(lo) <= F(tau*)` (too small) and false rejection. Phase 2 returns infeasible `hi` (upper bracket).

## Tests

`tests/test_phase2_safe_bound_upper.py` contrasts `isolated_wait_threshold_legacy_lower` with `reliability_upper_bound`.