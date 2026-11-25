# Figure captions

## Fig01_spatial_charging_repair

Outcome-selected holdout example C1_10_3/A, route 106. The original and repaired maps share the same ordered customers. STaR removed station 1253 after the last customer and inserted a visit to 1248 before the first. Observed reliability is 3,063 and 10,000 successes on the same 10,000-scenario archived validation tape. Mean full return includes late scenarios. Coordinates, charge and time use native benchmark units.

## Fig02_star_framework

Frozen Slack-Targeted Stochastic Charging Repair (STaR) with a fixed customer sequence. The analytical screen uses a true-reliability necessary condition when the incumbent attains the empirical target. Prefix pruning tests the best possible score on the same tape. A strict gain restarts the neighborhood. Independent final validation follows search.

## Fig03_paired_reliability

Paired reliability on 2,321 exposed holdout routes from 48 parents under the 64-plan budget. Panel (a) shows route-weighted STaR-minus-comparator means with pointwise 95% family-stratified parent bootstrap intervals (9,999 resamples, A/B siblings and routes retained together). Fixed-station repair is confirmatory, scenario search exploratory. Panel (b) compares STaR with fixed-station repair. Ties have equal success counts out of 10,000.

## Fig04_charging_complexity

Holdout routes stratified by original constructive-plan station visits. Panel (a) shows STaR minus fixed-station repair in percentage points with exploratory pointwise 95% parent-cluster intervals. Panel (b) gives the count and share whose one-sided 95% Wilson lower bound after STaR is below 0.95. The signed contribution of the 3+ group is its mean times its route share. Parents may appear in more than one bin.

## Fig05_quality_simulation_effort

Separate exploratory timing panel of 118 routes from 60 parents (23 development, 95 holdout). The 20, 50 and 100 ms cooperative guards each used three serial repeats per method and route. Panel (a) shows route-mean independent validation reliability and incremental search draws, excluding validation. Panel (b) shows paired differences with pointwise 95% family-by-partition parent intervals after averaging repeats. At 50 ms, STaR exceeded the guard on 122/354 runs and scenario search on 117/354. Reliability and elapsed-time difference intervals include zero at 50 ms.
