# Source traceability

Reviewed base `d17616177b61cb98e11c1cd5408d7c981fae2b21`. Frozen executable `c657aa69d55178c85b4759475933b36d1bcc2181`.
Phase 7 reads Phases 1–6 as immutable inputs. Figure 1 uses the original Phase 3 ZIP member, matching frozen validation/plan bundles and actual benchmark coordinates.

## Fig01

- `results/phase6/data/route_features.csv` — `39f95e2d1ebaa065930c02f3ef19be95adf2136bcfd2f153853b2c3f04a31027`
- `results/phase3/con_bundles.zip` — `99b42e4e46f4a19f288ead588b36fcc43d499f025d5fc828d49b4ca7627c2d03`
- `results/phase3/processed/provenance.json` — `4ef492c10a55006aa5ed6571217992b773fdb6d43c630d0d6978648a2f8766e6`
- `results/phase5/data/route_results.csv` — `d503619a9e3a3c0e05e71ee17fa418b48e907e2c7d38cbb87384b3902d239aae`
- `dataset/EVRPTW_ChargingStations_Dataset/variant_A_original_TW/C1_10_3.txt` — `fa036cb93c7c476233262d1a0de652a11c9383b5bde0eff4120f9424212e3ec4`
- `dataset/EVRPTW_ChargingStations_Dataset/variant_A_original_TW/C1_10_3_stations.csv` — `d7a67285c17a39851c4bf2506098518ff98c03dafdb7863ba8ff76da571ba584`
- `results/phase3/raw/c64/C1_10_3__A__0000.json.gz` — `b4f8fbf65ec1212808ae992803c275fdbf771bb0be8382ea1ab24e4bc2382efb`
- `results/phase3/plans/c64/C1_10_3__A__0000.json.gz` — `ce1fdd67868aaa97b608f18d0dc5e34ac8de875d39ccf6fbb9b40e3804653b80`

## Fig02

- `src/star_evrp/competitive_search.py` — `e7f4b0418731fd148427a78165529e7e09654a425481ca5e5e599d41e0d815b2`
- `src/star_evrp/route_evaluator.py` — `e200768063617a0bae793f196393fcb9ddcb357cb34ef22ea22695126493e07a`
- `src/star_evrp/timing.py` — `19ebf9fc826da579c3256e32fef7220103389c4ad26ac657ed4e27c3e4f2e3c3`
- `src/star_evrp/budget.py` — `211b7651e7f1da828ace531d6039222940187fb2c47df68855afab08ca448c67`
- `src/star_evrp/search_common.py` — `eec9012af31351d875ab73d9ad81a3c858d30c06b1d9df700c95edc1c1769ad4`
- `src/star_evrp/charge_plan.py` — `553e83a6961c4cb7a8dcccf6f50dcd7a134f3023bc25f09b47061f1b18236173`
- `src/star_evrp/deterministic_simulator.py` — `8e226e99dd94fa2691f97bf237e1b651b822ba7324b6e9178f6005d94ca1c01d`
- `src/star_evrp/scenario_tapes.py` — `e5928078589263c413578ca19f34cf2ed27e85afcaba0856209bd4a8c104d9dc`
- `configs/phase3_frozen.yaml` — `f55ab289ac935e65193ed455e48ec2e27112df117cd409dba2339439dde2ede4`
- `docs/PHASE6_MATHEMATICAL_AUDIT.md` — `7b4b983db6176d9ba6a7a01ee0ef675146a83b14bb67ee2284845d3c22a43d8e`

## Fig03

- `results/phase5/data/paired_effects.csv` — `d2f1581ecb85c5e422c34429ebde6e365e376bbef0ae2f6548b39d848190a9c5`
- `results/phase5/data/route_results.csv` — `d503619a9e3a3c0e05e71ee17fa418b48e907e2c7d38cbb87384b3902d239aae`
- `results/phase3/tables/parent_effects.csv` — `55b2657d9e2cba09d7aa7d34b32317b5b2a9adb086149babd0ffd1d77cfbf98f`
- `results/phase6/data/paired_directions.csv` — `58d03c7f72209fd513c5ed54d3e24c8874f6fcc0f4067fe58c37be7f33518d92`

## Fig04

- `results/phase6/data/mechanism_strata.csv` — `bbae08e24cecfd0a282096ce78aa086d85174085145408b67bb49e8c3a5e9141`
- `results/phase6/data/route_features.csv` — `39f95e2d1ebaa065930c02f3ef19be95adf2136bcfd2f153853b2c3f04a31027`
- `results/phase6/data/paired_routes.csv` — `f4a05d0f49b4330b66f94e8fbaad85b9e6e419d9023db47444684166528d6161`
- `results/phase6/data/attainment_transitions.csv` — `4e36c3fc2ba26d12bf3579ec99999bdd5c97b6a46670fc31575c7e109577edd9`
- `results/phase6/data/parent_influence.csv` — `f4f805ea5d26a444a9ea0cbf0f6fb3ded91415f771bf236e85a418cf5cedf2eb`
- `results/phase5/data/route_results.csv` — `d503619a9e3a3c0e05e71ee17fa418b48e907e2c7d38cbb87384b3902d239aae`

## Fig05

- `results/phase6/data/timing_route_results.csv` — `c01b3473be180ebdba3cf46f338e363253e3617d19fa12fa37ec42209c57ae8b`
- `results/phase6/data/timing_route_aggregates.csv` — `c6cc9bfdac0abd649b61fbe191e3e622471b4e47dc25be23d5eeb93dfe2a6988`
- `results/phase6/data/timing_summary.csv` — `84ac3c10b67fda1a336b010e7566c7ffd2fff4ffe5aae2ae39179c7c22beeb26`
- `results/phase6/data/timing_paired_routes.csv` — `5d1d1dc6c243bd7be1baedf259fe1ab124feaf293fc0ca59bb0a8c49947e2924`
- `results/phase6/data/timing_paired_effects.csv` — `8fde7c63c3600e9f33a58545a86e867c841780a395ed0c4697fc00856dd834e2`
- `results/phase6/manifests/comparator_panel.csv` — `e86ac2d2f3feedeb67e44fb844de1d987028f7c7bbd98e632f3bf09d93f616cd`
- `results/phase6/manifests/protocol.json` — `db3aa864f59443190a1535f60172dddda17a0c158f17b9e4bc0c1904cf96b3be`
- `results/phase6/tables/T06-05_controlled_runtime.csv` — `44d61882018e6e3bad1739bb09046990aec07c78c5dfbee6dde3c8637d67ba04`

## Tab01

- `configs/phase3_frozen.yaml` — `f55ab289ac935e65193ed455e48ec2e27112df117cd409dba2339439dde2ede4`
- `results/phase3/manifests/freeze.json` — `51c6b61a3c81e5dc9a02b922eb2d988d80a91dd807d374f8ca07a23ed52d8ca7`
- `results/manifests/dataset_inventory.json` — `0ed25b73defe40189666ceec7a830e83ca51130eff4afa53ee766a46f065ce80`
- `results/phase5/data/population_by_instance.csv` — `6a51ddf58a51b1add475daff0cbc71566cc62181d0f580966d16a30c3a7ce6e9`

## Tab02

- `results/phase5/data/route_results.csv` — `d503619a9e3a3c0e05e71ee17fa418b48e907e2c7d38cbb87384b3902d239aae`
- `results/phase5/data/summary.json` — `d370a0bd456ded8b3ebd1e5495e5e07e486b9548b21b225e22ba3fbce9f4242b`
- `results/phase5/tables/supplementary/S01_complete_benchmark.csv` — `42b88da3116e8b4c50655101f93d0cd8b91483d7a11140ff2b11a21df3545ae8`

## Tab03

- `results/phase5/data/route_results.csv` — `d503619a9e3a3c0e05e71ee17fa418b48e907e2c7d38cbb87384b3902d239aae`
- `results/phase5/data/paired_effects.csv` — `d2f1581ecb85c5e422c34429ebde6e365e376bbef0ae2f6548b39d848190a9c5`
- `results/phase5/tables/main/T04_ablation_quality.csv` — `1976814ec1ab7b5c4970dd8794e7d6c6be41eab31104416cee0fb72e6bf92ec0`
- `results/phase5/tables/main/T05_ablation_work.csv` — `4f614adea0515b9f1717938d21b8695596b0928b072554786be3c99fb708b164`

## Diagram semantics

- Rank visits by increasing marginal upper bound and prioritize gaps near the most critical visit.
- The analytical screen uses the minimum marginal true-reliability bound and rejects below target minus 1e-12.
- At prefix k = 128 out of S = 512, optimistic reliability is (m + S − k) / S. Lower completion is (C_k + (S − k) C_0) / S. Here m counts prefix successes, C_k sums prefix completion, and C_0 is zero-wait return. The frozen optimistic score subtracts a 1e-8 completion cushion.
- Strict improvements restart the neighborhood. Independent validation follows search without feedback.

## Companion archives

- `results/phase5/STaR_EVRP_FINAL_RESULTS_HANDOFF.zip`
- `results/phase6/STaR_EVRP_PHASE6_SCIENTIFIC_SUPPLEMENT.zip`
