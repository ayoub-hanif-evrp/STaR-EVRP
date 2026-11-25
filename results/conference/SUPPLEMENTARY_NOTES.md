# Physical and timing details

## Fig01 physical ledger

The archived original fills at station 1253 and returns with 368.71 units remaining. The saved repair charges at station 1248 and returns with 0.00 units. The reduction in charge is explained by reduced final residual and the change in travel energy. With consumption of 1 unit per distance unit, the charge change -378.38 equals the travel energy change -9.67 plus the residual change -368.71. There is no additional energy reserve in the validator.

The deterministic return changes by -418.92 time units. Its components are -9.67 travel, -310.24 charging time at heterogeneous rates, -99.01 readiness-floor waiting and +0.00 service. The archived means 1,826.22 and 1,394.79 include stochastic waits and late returns. The deterministic decomposition explains the physical change and cannot attribute the stochastic difference to any single component.

| Plan | Visit | Station ID | After customer | Charge | Rate | Charging time |
| --- | --- | --- | --- | --- | --- | --- |
| Original route | S1 | 1253 | 2 | 447.46 | 1.0934 | 409.24 |
| STaR | S1 | 1248 | 0 | 69.08 | 0.6978 | 98.99 |

## Sup01 complex route

The charging-event sequence is separate from the fixed customer order. A zero in the after-customer column identifies a pre-customer station visit. All quantities are native. Exact event times, distances, battery arrivals and departures, rates, source keys and digests are in the corresponding source CSV and JSON files.

| Plan | Visit | Station ID | After customer | Charge | Rate | Charging time |
| --- | --- | --- | --- | --- | --- | --- |
| Original route | S1 | 1242 | 17 | 632.36 | 1.3571 | 465.96 |
| Original route | S2 | 1148 | 30 | 571.12 | 1.2418 | 459.91 |
| Original route | S3 | 1033 | 35 | 446.12 | 0.9890 | 451.08 |
| Original route | S4 | 1319 | 40 | 534.04 | 1.5165 | 352.15 |
| STaR | S1 | 1242 | 17 | 503.48 | 1.3571 | 370.99 |
| STaR | S2 | 1148 | 30 | 446.12 | 1.2418 | 359.25 |
| STaR | S3 | 1033 | 35 | 683.39 | 0.9890 | 690.99 |
| STaR | S4 | 1074 | 40 | 457.17 | 1.5549 | 294.02 |

## Sup02 adverse example

The archived validation difference is -99.31 percentage points. Fixed-station repair recorded 64 customer-only, 0 depot-only and 0 joint failures. STaR recorded 9,995, 0 and 0, respectively. The deterministic slack is a check on the saved routes with zero station waits. It provides context for possible delay sensitivity. The aggregate observations cannot establish which realized waits drove the difference.

| Plan | Visit | Station ID | After customer | Charge | Rate | Charging time |
| --- | --- | --- | --- | --- | --- | --- |
| Fixed-station repair | S1 | 1103 | 17 | 625.97 | 0.7692 | 813.80 |
| Fixed-station repair | S2 | 1150 | 25 | 556.21 | 1.5000 | 370.81 |
| Fixed-station repair | S3 | 1193 | 32 | 628.25 | 1.2802 | 490.74 |
| Fixed-station repair | S4 | 1102 | 42 | 292.55 | 1.6648 | 175.73 |
| STaR | S1 | 1103 | 17 | 625.97 | 0.7692 | 813.80 |
| STaR | S2 | 1150 | 25 | 606.65 | 1.5000 | 404.43 |
| STaR | S3 | 1193 | 32 | 628.25 | 1.2802 | 490.74 |
| STaR | S4 | 1102 | 42 | 242.11 | 1.6648 | 145.43 |

## Separate guard panel

Paired STaR minus scenario search, with pointwise 95% parent-cluster intervals. Guards are cooperative. The 50 ms row includes zero for both outcomes. The 44.52% draw reduction at 50 ms measures simulation work. The archived 20 ms elapsed contrast favored scenario search. Neither panel supports a general runtime superiority or equivalence claim.

| Guard | Reliability difference (pp) | Route-median elapsed difference (ms) |
| --- | --- | --- |
| 20 ms | +0.384 [-0.320, +1.180] | +0.986 [+0.665, +1.320] |
| 50 ms | -0.134 [-0.510, +0.087] | +0.233 [-1.018, +1.461] |
| 100 ms | -0.178 [-0.540, +0.020] | +1.952 [+0.420, +3.513] |
