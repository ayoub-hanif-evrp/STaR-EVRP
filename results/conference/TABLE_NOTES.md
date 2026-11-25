# Table notes

## Tab01_experimental_configuration

Frozen benchmark and registered holdout settings. The 4,543 no-charge holdout routes are unchanged and excluded from exposed metrics. There are no endogenous queues or wait-dependent decisions. Attainment means the one-sided 95% Wilson lower bound reaches 0.95. With 64 trials and 512 draws per trial the 131,072 scenario ceiling cannot bind. The STaR–FSPC reliability contrast is the sole confirmatory endpoint.

## Tab02_method_comparison

Six methods on 2,321 exposed holdout routes from the archived six-worker, 64-candidate cohort. R is reliability. Attained is a count out of 2,321. Full return uses native time units and includes late trajectories. Higher reliability and attainment and lower return, work and time are favorable. Search draws exclude validation. ᵃ Original route has no optimization. 0.22 ms is observed setup/evaluator time. Trials count the initial check and distinct examined candidates. STaR consumed 62.67 trials versus 20.18 for fixed-station repair. STaR used 34.59% fewer draws than scenario search with mean wall 29.69 versus 27.51 ms. Mean-wait repair finished 2.01 native units sooner than STaR on average. Quantile repair had similar mean completion. CSV values retain full precision.

## Tab03_component_ablation

Exploratory component removals on 2,321 exposed holdout routes. Reliability loss is full STaR minus ablation. Draw difference is ablation minus full STaR. Partial charging removes quantity-only moves and partial allocation on new topologies while retaining the original incumbent. Slack prioritization changes order only. Analytical screening removes analytical rejection while retaining ranking and prefix evaluation. Removing progressive evaluation fully scores admitted candidates. STaR used 5,903 fewer draws than this ablation, with identical recorded reliability, attainment and completion on every route. Effects are nonadditive. Timing is omitted because measurements span separate cohorts. The modest slack result reverses sign in development. Exact effects and intervals are in data/Tab03_exact.csv.
