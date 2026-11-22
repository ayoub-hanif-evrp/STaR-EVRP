# Safe screening mathematics

## Setting

Consider a fixed explicit route \(p\) that is **deterministically feasible** under zero exogenous charging wait. For each charging visit \(j\), let \(W_j \sim \mathrm{LogNormal}(\mu_j, \sigma_j)\) be an independent exogenous wait inserted before recharging at station \(j\).

Let \(\tau_j\) be the **isolated wait threshold**: the largest \(w \ge 0\) such that the route remains timing-feasible when wait is placed only at visit \(j\) and zero elsewhere. We compute \(\tau_j\) by monotone bisection on deterministic simulation (conservative lower envelope).

## Necessary condition

If the route succeeds under stochastic waits, then for each visit \(j\) we must have \(W_j \le \tau_j\) (otherwise that isolated perturbation already fails). Hence

\[
\mathbb{P}(\text{success}) \le \mathbb{P}\bigl(W_j \le \tau_j \text{ for all } j\bigr)
\le \prod_j \mathbb{P}(W_j \le \tau_j)
\]

when waits are independent across visits. Define

\[
U(p) = \min_j F_j(\tau_j),
\]

where \(F_j\) is the lognormal CDF at station \(j\). Then \(U(p)\) is an **upper bound** on route-level reliability (never a certificate of success).

## Assumptions

1. Independent waits across charging visits (no cross-route queue coupling).
2. Deterministic energy feasibility is unchanged by waiting (energy leg is not re-optimized).
3. Timing failure is monotone in each wait: larger wait cannot repair a violated downstream deadline.
4. Station time-window enforcement follows the deterministic simulator contract (off by default for deposited baseline parity).

## Numerical conservatism

- \(\tau_j\) bisection uses a fixed tolerance; reported \(\tau_j\) is a conservative **lower** estimate of the true breakpoint.
- CDF evaluation uses SciPy `lognorm` with \(\mathrm{scale}=\exp(\mu_j)\).
- `safe_reject` fires only when \(U(p) < \text{target}\); near-threshold routes are not rejected when \(U \ge \text{target}\).

## Toy verification

Unit tests on synthetic one-station routes compare `reliability_upper_bound` against \(\min_j F_j(\tau_j)\) and check Monte Carlo empirical reliability does not exceed \(U(p)\) by more than sampling slack. See `tests/test_risk_bounds.py`.