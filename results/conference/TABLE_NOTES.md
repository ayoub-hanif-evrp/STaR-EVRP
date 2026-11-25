# Table notes

## Tab01_experimental_configuration

Frozen benchmark and registered holdout settings. No-charge holdout routes are excluded from exposed metrics. Attainment means the one-sided 95% Wilson lower bound reaches 0.95. Station hours disabled; native units. The sole confirmatory endpoint remains STaR−FSPC (see ARCHIVAL_EVIDENCE.md).

## Tab02_method_comparison

Four methods on 2,321 exposed holdout routes. R is mean reliability (%). Attained is count/2,321. Full return uses native time units including late trajectories. Search draws exclude validation. ᵃ CON wall 0.22 ms is observed setup/evaluator time, not optimization. MWR/QBR report 0 stochastic search draws because they use surrogate scores. STaR trials 62.67; MWR completion is shorter than STaR by 2.01 native units. CSV retains full precision.

## Tab03_component_ablation

Five component rows (full STaR plus four removals). Loss is full minus ablation (pp). Draw difference is ablation minus full. Progressive prefix saved ≈5,903 draws (31.2%) with identical per-route outcomes. Effects are exploratory and nonadditive; slack prioritization reverses sign on development. NPC bundles quantity moves and new-topology allocation.
