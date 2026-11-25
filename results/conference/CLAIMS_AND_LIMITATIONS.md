# Claims and limitations for the writer

## Main evidence

- **Registered result (Fig03, Tab02).** STaR minus FSPC +1.24 [+0.86, +1.65] pp over 2,321 exposed routes and 48 parents. Actual mean trials were 62.67 versus 20.18 at a common maximum of 64. The contrast estimates a difference against the implemented heuristic under the frozen budget. It does not isolate the role of topology or establish an advantage over optimal fixed-topology quantities. Parent-equal sensitivity was +1.12 pp [0.79, 1.47].
- **Scenario search (Fig03, Tab02, Fig05).** Archived STaR minus SLS +0.32 [+0.13, +0.49] pp, exploratory. STaR used 34.59% fewer draws and took 29.69 versus 27.51 ms. In the 118-route panel, STaR used 44.52% fewer draws at 50 ms. Reliability was -0.134 [-0.510, +0.087] pp and paired route-median wall was +0.233 [-1.018, +1.461] ms. Overshoot reached 22.18/19.96 ms on 122/117 of 354 repeats per method. At 20 ms, paired wall was +0.986 [+0.665, +1.320] ms. Keep work and elapsed results distinct across cohorts.
- **Full benchmark (Phase 5).** The pooled 120-instance values of 97.06% STaR mean reliability and 2,742/2,891 attainment are descriptive. Use the 96-instance holdout as the primary population.
- **Mechanisms (Fig01, Fig04).** Fig01 is an outcome-selected example using the recorded selection rule. Three-plus original visits contribute 89.0% of the net signed difference and account for 102 residual failures. R2/RC2 account for 109/110 holdout nonattainments. Phase 6 associates tighter source slack and higher complexity with failure. Draw causal conclusions from none of these strata.
- **Components (Tab03, Phase 5).** Partial charging bundles two changes. Slack prioritization has a modest holdout difference and reverses sign in development. The analytical screen bounds true fixed-plan reliability, while the finite empirical score can exceed this bound. Prefix pruning compares with the same incumbent on the same tape subject to numerical tolerance. Binding budgets can change later search.

## Supplementary disclosure

- **AS1, 113-route Phase 6 one-visit panel.** AS1 minus STaR -0.018 [-0.059, +0.022] pp and -14.04 native completion units. The reliability interval crosses zero. AS1 is restricted to at most one visit. The hybrid was excluded.
- **FT-SAA, 118-route Phase 6 panel.** STaR minus FT-SAA -0.384 [-1.183, +0.050] pp and -44.45 native completion units. Five of 22 multi-visit cases obtained complete MILP certificates. Valid fallbacks remain in the panel. See the Phase 6 report and handoff for every status and paired result.

## Scope

Station laws are synthetic. Four station-attribute tables were reused and all appeared in development. Customer assignment and order are fixed, charging is linear, and station hours are disabled. The study has no live queues, fleet congestion, routing recourse or fleet-wide chance guarantee. Intervals are pointwise, unadjusted and conditional on archived validation. Except for the registered FSPC contrast, the comparisons are exploratory. The study does not establish global optimality, universal superiority, a general wall-time speedup or literature priority.
