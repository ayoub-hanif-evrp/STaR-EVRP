| Parameter | Configuration |
| --- | --- |
| Benchmark | Extended Homberger, 1,000 customers/instance; 120 instances from 60 A/B parents. |
| Split and coverage | 24 development / 96 holdout instances (12 / 48 parents). 8,606 routes / 2,891 exposed overall; holdout 6,864 / 2,321 (4,543 unchanged no-charge). |
| Route and energy | Fixed customers/order; Q = 700; h = 1; Euclidean travel; linear heterogeneous charging; native units. |
| Waits and stations | Independent synthetic lognormal visit waits; 4 reused station tables; station hours disabled. |
| Search and target | 95% individual reliability target; max 64 distinct trials (including start); 131,072 search-draw ceiling; 5 s cooperative guard. |
| Evaluation | 512 full stochastic draws; 128-draw STaR prefix; up to 3 nearby stations; 10,000 independent validation draws. |
| Inference | One-sided 95% Wilson attainment; 9,999 family-stratified parent bootstrap resamples (seed 312406). |
