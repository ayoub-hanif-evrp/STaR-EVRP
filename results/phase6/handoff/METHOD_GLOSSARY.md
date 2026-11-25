# Method dictionary

| Frozen/internal key | Acronym | Meaning |
| --- | --- | --- |
| B0 | CON | Deposited constructive solution without repair |
| B1 | MWR | Mean-Wait Repair using deterministic mean waits |
| B2 | QBR | Quantile-Based Repair using deterministic independent-visit lognormal risk quantiles |
| B3 | SLS | Scenario-Based Local Search scoring a fixed common scenario batch |
| B4 | FSPC | Fixed-Station Partial Charging adjusting amounts only |
| STaR | STaR | Slack-Targeted Stochastic Charging Repair |
| STaR_NAS | STaR-NAS | No Analytical Screening with prefix pruning retained |
| STaR_NPP | STaR-NPP | No Progressive Prefix with full evaluation of admitted plans |
| STaR_NSP | STaR-NSP | No Slack Prioritization with natural station and gap order |
| STaR_no_partial | STaR-NPC | No Partial Charging quantity neighborhood or partial allocation for new topology moves |

SLS and FSPC are project-implemented benchmarks, not claimed reproductions of published algorithms. STaR-NPC removes amount-only moves and uses full charging for new topology moves; it starts from the original plan. STaR-NAS still computes marginal risks to rank moves; STaR-NPP changes search prefixing only, not validation.

| Phase 6 method | Definition |
| --- | --- |
| AS1 | Analytical optimizer over zero or one station visit and all customer gaps. |
| FT-SAA | Fixed-Topology Sample-Average optimizer of charge quantities. |
