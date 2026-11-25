"""Extract a self-contained Prompt-09 publication input snapshot.

Reads Phase 3/5/6 archives through existing loaders while those folders still exist,
then writes compact immutable CSVs/JSON under results/conference/data/inputs/.
Does not modify the STaR optimizer or delete phase folders.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from statistics import fmean

for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_var] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from star_evrp.conference_physics import route_example  # noqa: E402
from star_evrp.phase4_results import (  # noqa: E402
    bootstrap,
    file_sha,
    git,
    grouped,
    indexed,
    read_json,
    require,
    require_keys,
    strata,
)
from star_evrp.phase6_archive import (  # noqa: E402
    csv_rows,
    freeze_context,
    key,
    load_archive,
    roster,
    write_csv,
    write_json,
)

OUT_REL = Path("results/conference/data/inputs")
METHODS = {
    "CON": "Original route",
    "MWR": "Mean-wait repair",
    "QBR": "Quantile repair",
    "STaR": "STaR",
}
ABLATIONS = {
    "STaR": "None (full STaR)",
    "STaR-NPC": "Partial charging",
    "STaR-NSP": "Slack prioritization",
    "STaR-NAS": "Analytical screening",
    "STaR-NPP": "Progressive evaluation",
}
PUBLICATION_METHODS = ("CON", "MWR", "QBR", "STaR")
HOLD_METHODS = ("CON", "MWR", "QBR", "STaR", "STaR-NPC", "STaR-NSP", "STaR-NAS", "STaR-NPP")
PLOT_COMPARATORS = ("CON", "MWR", "QBR")
ARCHIVE_COMMIT = "1ad987a328679263e5d8ba40330ffe1a11409db1"
ARCHIVE_TAG = "star-research-archive-v1"
FREEZE_COMMIT = "c657aa69d55178c85b4759475933b36d1bcc2181"
FREEZE_TAG = "star-phase3-freeze-v1"

SOURCE_PATHS = (
    "results/phase5/data/route_results.csv",
    "results/phase5/data/paired_effects.csv",
    "results/phase5/data/summary.json",
    "results/phase5/data/population_by_instance.csv",
    "results/phase5/tables/main/T04_ablation_quality.csv",
    "results/phase5/tables/main/T05_ablation_work.csv",
    "results/phase5/tables/supplementary/S01_complete_benchmark.csv",
    "results/phase6/data/route_features.csv",
    "results/phase6/data/mechanism_strata.csv",
    "results/phase6/data/as1_paired_effects.csv",
    "results/phase6/data/fixed-topology_paired_effects.csv",
    "results/phase3/manifests/freeze.json",
    "results/manifests/dataset_inventory.json",
    "configs/phase3_frozen.yaml",
)


def near(value, expected, label, atol=2e-10):
    from math import isclose
    require(isclose(float(value), float(expected), rel_tol=0, abs_tol=atol),
            f"{label}: {value!r} differs from {expected!r}")


def round_check(value, expected, label, ndigits=2):
    require(round(float(value), ndigits) == expected,
            f"{label}: {value!r} rounds to {round(float(value), ndigits)}, expected {expected}")


def census(root, cfg):
    roster_rows = roster(root)
    case_ids = {(x["parent_key"], x["variant"]): x for x in roster_rows}
    population = indexed(
        csv_rows(root / "results/phase5/data/population_by_instance.csv"),
        lambda r: (r["parent"], r["variant"]),
    )
    require_keys(population, case_ids, "Instance census")
    breakdown = []
    for partition in ("development", "holdout"):
        relevant = [r for r in population.values() if r["partition"] == partition]
        selected = [r for r in roster_rows if r["partition"] == partition]
        require(
            {(r["parent"], r["variant"]) for r in relevant}
            == {(r["parent_key"], r["variant"]) for r in selected}
            and all(r["family"] == case_ids[r["parent"], r["variant"]]["family"] for r in relevant),
            "Census split mismatch",
        )
        require(all(int(r["all_routes"]) == int(r["exposed"]) + int(r["zero_charge"]) for r in relevant),
                "Invalid route census")
        breakdown.append(dict(
            partition=partition,
            instances=len(relevant),
            parents=len(strata(selected)),
            **{k: sum(int(r[k]) for r in relevant) for k in ("all_routes", "exposed", "zero_charge")},
        ))
    require(
        [(r["instances"], r["parents"], r["all_routes"], r["exposed"]) for r in breakdown]
        == [(24, 12, 1742, 570), (96, 48, 6864, 2321)],
        "Unexpected frozen split or denominators",
    )
    hashes = {r["stations_sha256"] for r in roster_rows}
    require(
        len(hashes) == 4
        and all({r["partition"] for r in roster_rows if r["stations_sha256"] == item} == {"development", "holdout"}
                for item in hashes),
        "Station table reuse mismatch",
    )
    counts = {field: sum(r[field] for r in breakdown)
              for field in ("instances", "parents", "all_routes", "exposed", "zero_charge")}
    frozen = cfg["profiles"]["c64"]
    spec = counts | {
        "partitions": breakdown,
        "distinct_station_tables": len(hashes),
        "customers_per_instance": 1000,
        "target": cfg["target"],
        "battery_capacity": cfg["battery_capacity"],
        "energy_consumption": cfg["energy_consumption_rate"],
        "station_windows": cfg["station_windows"],
        "work_limits": frozen["limits"],
        "search_draws": cfg["opt_samples"],
        "prefix_draws": cfg["opt_samples"] // 4,
        "nearby_count": cfg["nearby_stations"],
        "validation_draws": cfg["validation_samples"],
        "search_seed": frozen["seed"],
        "validation_seed": cfg["validation_seed"],
        "bootstrap_seed": cfg["statistical_seed"],
        "bootstrap_replicates": cfg["bootstrap_draws"],
        "archive_workers": cfg["workers"],
    }
    require(
        spec["search_draws"] * frozen["limits"]["max_candidate_evals"] < frozen["limits"]["max_scenario_evals"],
        "Scenario cap statement no longer applies",
    )
    return spec


def holdout_records(root, records, cfg):
    selected = {k[1:]: v for k, v in records.items() if k[0] == "holdout"}
    parents = strata([r for r in roster(root) if r["partition"] == "holdout"])
    groups = grouped(selected, lambda k: k[-1])
    keys = {k[:3] for k in groups["STaR"]}
    require(len(keys) == 2321 and len(parents) == 48 and {k[0] for k in keys} == set(parents),
            "Bad primary matched sample")
    require_keys(groups, set(METHODS) | set(ABLATIONS) | {"FSPC", "SLS"}, "Expected frozen c64 methods")
    for method, ks in groups.items():
        require_keys((k[:3] for k in ks), keys, method)
    for balance in keys:
        vals = [selected[*balance, m]["validation"] for m in groups]
        require({v["n"] for v in vals} == {cfg["validation_samples"]} and len({v["tape_seed"] for v in vals}) == 1,
                "Validation count, seed or key mismatch")
        require(all(v["successes"] / v["n"] == v["reliability"] for v in vals), "Success proportion mismatch")
    return selected, parents, sorted(keys)


def signed_pairs(rows, keys, comparator):
    result = []
    for p, v, r in keys:
        one, two = (rows[p, v, r, m]["validation"] for m in ("STaR", comparator))
        result.append(dict(
            parent=p, variant=v, route=r, family=rows[p, v, r, "STaR"]["family"], comparator=comparator,
            star_successes=one["successes"], control_successes=two["successes"], scenarios=one["n"],
            delta_pp=100 * (one["successes"] - two["successes"]) / one["n"],
        ))
    return result


def map_candidates(rows, keys, plans, features):
    from star_evrp.phase4_results import canonical
    from collections import Counter

    all_options = []
    for k in keys:
        parent, variant, rid = k
        source, selected = plans["holdout", *k, "CON"], plans["holdout", *k, "STaR"]
        v0, v1 = (rows[*k, m]["validation"] for m in ("CON", "STaR"))
        original = features["holdout", *k]
        original_topology, final_topology = (p["station_positions"] for p in (source, selected))
        require(canonical(original_topology).decode() == original["source_topology"]
                and canonical(final_topology).decode() == original["selected_topology"],
                "Topology does not match archive")
        require(source["customer_sha256"] == selected["customer_sha256"], "Customer order changed")
        customers = sum(event[1] == "customer" for event in source["events"])
        require(customers == int(original["customers"]), "Source customer count mismatch")
        changed = original_topology != final_topology
        gain = v1["successes"] - v0["successes"]
        tier = (1 if changed and not v0["attained"] and v1["attained"] and gain > 0 else
                2 if changed and gain > 0 else 3 if changed else None)
        all_options.append(dict(
            parent=parent, variant=variant, route=rid, customers=customers, tier=tier,
            topology_changed=changed, con_attained=v0["attained"], star_attained=v1["attained"],
            gain_successes=gain,
            con_topology=canonical(original_topology).decode(),
            star_topology=canonical(final_topology).decode(),
        ))
    all_options.sort(key=lambda r: (r["customers"], r["parent"], r["variant"], r["route"]))
    eligible = [r for r in all_options if r["tier"] is not None]
    require(bool(eligible), "No physical topology change in archive")
    chosen = min(eligible, key=lambda r: r["tier"])
    require((chosen["parent"], chosen["variant"], chosen["route"]) == ("C1_10_3", "A", 106),
            "The Phase 7 main example must remain fixed")
    return dict(
        chosen=chosen,
        eligible_tier_counts=dict(Counter(str(r["tier"]) for r in all_options)),
        rule="First by original customer count, parent, variant, route ID within first nonempty tier",
        fallback=chosen["tier"] != 1,
        example_scope="Outcome-selected holdout illustration",
    ), all_options


def boot_pp(pairs, parents, seed=312406, replicates=9999):
    return bootstrap([(r["parent"], r["delta_pp"]) for r in pairs], parents, seed=seed, replicates=replicates)


def aggregate_method(rows, keys, method):
    subset = [rows[p, v, r, method] for p, v, r in keys]
    vals = [rec["validation"] for rec in subset]
    return dict(
        method=method,
        n=len(vals),
        reliability=fmean(v["reliability"] for v in vals),
        reliability_pct=100 * fmean(v["reliability"] for v in vals),
        attained=sum(bool(v["attained"]) for v in vals),
        completion=fmean(v["completion"] for v in vals),
        candidates_evaluated=fmean(rec["work"]["candidates_evaluated"] for rec in subset),
        scenarios_evaluated=fmean(rec["work"]["scenarios_evaluated"] for rec in subset),
        elapsed_seconds=fmean(rec["work"]["elapsed_seconds"] for rec in subset),
        wall_ms=1000 * fmean(rec["work"]["elapsed_seconds"] for rec in subset),
    )


def extract(root: Path, out: Path):
    records, plans, prior = load_archive(root)
    freeze = freeze_context(root)
    cfg = freeze["config"]
    rows, parents, keys = holdout_records(root, records, cfg)
    config = census(root, cfg)
    config = dict(
        config,
        population=dict(
            instances=config["instances"],
            parents=config["parents"],
            all_routes=config["all_routes"],
            exposed=config["exposed"],
            zero_charge=config["zero_charge"],
            partitions=config["partitions"],
        ),
        Q=config["battery_capacity"],
        battery_capacity=config["battery_capacity"],
        seeds=dict(
            search=config["search_seed"],
            validation=config["validation_seed"],
            bootstrap=config["bootstrap_seed"],
        ),
        budgets=dict(
            work_limits=config["work_limits"],
            search_draws=config["search_draws"],
            prefix_draws=config["prefix_draws"],
            validation_draws=config["validation_draws"],
            nearby_count=config["nearby_count"],
        ),
        archive_commit=ARCHIVE_COMMIT,
        archive_tag=ARCHIVE_TAG,
        freeze_commit=FREEZE_COMMIT,
        freeze_tag=FREEZE_TAG,
        frozen_optimizer=FREEZE_COMMIT,
    )
    write_json(out / "config.json", config)

    features = indexed(csv_rows(root / "results/phase6/data/route_features.csv"), key)
    require(all(("holdout", *k) in features for k in keys), "Missing holdout route features")

    metric_rows = []
    for parent, variant, route in keys:
        for method in HOLD_METHODS:
            rec = rows[parent, variant, route, method]
            val = rec["validation"]
            work = rec["work"]
            metric_rows.append(dict(
                parent=parent,
                variant=variant,
                route=route,
                method=method,
                family=rec["family"],
                reliability=val["reliability"],
                successes=val["successes"],
                n=val["n"],
                attained=bool(val["attained"]),
                completion=val["completion"],
                candidates_evaluated=work["candidates_evaluated"],
                scenarios_evaluated=work["scenarios_evaluated"],
                elapsed_seconds=work["elapsed_seconds"],
                source_visits=int(features["holdout", parent, variant, route]["source_visits"]),
            ))
    write_csv(
        out / "holdout_route_metrics.csv",
        metric_rows,
        fields=[
            "parent", "variant", "route", "method", "family", "reliability", "successes", "n",
            "attained", "completion", "candidates_evaluated", "scenarios_evaluated", "elapsed_seconds",
            "source_visits",
        ],
    )

    npp_equal = all(
        all(
            rows[p, v, r, "STaR"]["validation"][field] == rows[p, v, r, "STaR-NPP"]["validation"][field]
            for field in ("reliability", "successes", "attained", "completion")
        )
        for p, v, r in keys
    )
    require(npp_equal and len(keys) == 2321, "NPP outcomes differ from STaR")

    archive_effects = indexed(
        [
            r for r in csv_rows(root / "results/phase5/data/paired_effects.csv")
            if (r["cohort"], r["metric"], r["profile"]) == ("holdout", "reliability", "c64")
        ],
        lambda r: r["comparison"],
    )
    paired_summaries = []
    con_pairs = None
    for comparator in PLOT_COMPARATORS:
        pairs = signed_pairs(rows, keys, comparator)
        write_csv(out / f"paired_routes_{comparator}.csv", pairs)
        if comparator == "CON":
            con_pairs = pairs
        mean, lo, hi, pmean, plo, phi = boot_pp(pairs, parents)
        saved = archive_effects[comparator]
        for label, got, expected in (
            ("mean", mean / 100, float(saved["mean"])),
            ("lo95", lo / 100, float(saved["lo95"])),
            ("hi95", hi / 100, float(saved["hi95"])),
        ):
            near(got, expected, f"{comparator} paired {label}")
        paired_summaries.append(dict(
            cohort="holdout",
            profile="c64",
            metric="reliability",
            comparison=comparator,
            n=len(pairs),
            parents=len(parents),
            mean_pp=mean,
            lo95_pp=lo,
            hi95_pp=hi,
            parent_mean_pp=pmean,
            parent_lo95_pp=plo,
            parent_hi95_pp=phi,
            status=saved["status"],
            higher=sum(r["delta_pp"] > 0 for r in pairs),
            equal=sum(r["delta_pp"] == 0 for r in pairs),
            lower=sum(r["delta_pp"] < 0 for r in pairs),
        ))
    write_csv(out / "paired_effects_holdout.csv", paired_summaries)

    require(con_pairs is not None, "Missing CON paired sample")
    visit_rows = []
    for pair in con_pairs:
        k = pair["parent"], pair["variant"], pair["route"]
        source = int(features["holdout", *k]["source_visits"])
        require(source > 0, f"Non-exposed route in holdout sample: {k}")
        visit_rows.append(dict(
            **pair,
            source_visits=source,
            bin="3+" if source >= 3 else str(source),
            nonattained=not rows[*k, "STaR"]["validation"]["attained"],
        ))
    write_csv(out / "visit_bin_routes.csv", visit_rows)
    visit_bins = []
    expected_bins = {"1": (1587, 4), "2": (159, 4), "3+": (575, 102)}
    for level in ("1", "2", "3+"):
        part = [r for r in visit_rows if r["bin"] == level]
        n = len(part)
        nonattained = sum(r["nonattained"] for r in part)
        require((n, nonattained) == expected_bins[level], f"Visit bin {level} anchors differ")
        mean, lo, hi, pmean, plo, phi = boot_pp(part, parents)
        visit_bins.append(dict(
            bin=level,
            n=n,
            parents=len({r["parent"] for r in part}),
            nonattained=nonattained,
            nonattainment_rate=nonattained / n,
            mean_pp=mean,
            lo95_pp=lo,
            hi95_pp=hi,
            parent_mean_pp=pmean,
            parent_lo95_pp=plo,
            parent_hi95_pp=phi,
            comparison="CON",
            metric="STaR-CON_reliability_pp",
            bootstrap_seed=312406,
            bootstrap_replicates=9999,
        ))
    write_csv(out / "visit_bin_effects.csv", visit_bins)

    selection, _ = map_candidates(rows, keys, plans, features)
    require(
        (selection["chosen"]["parent"], selection["chosen"]["variant"], selection["chosen"]["route"])
        == ("C1_10_3", "A", 106),
        "Fig01 route selection drifted",
    )
    example = route_example(root, rows, plans, freeze, selection, ("CON", "STaR"))
    write_json(out / "fig01_route.json", example["selection"])
    write_csv(out / "fig01_nodes.csv", example["nodes"])
    write_csv(out / "fig01_stops.csv", example["stops"])
    write_csv(out / "fig01_metrics.csv", example["metrics"])
    write_csv(out / "fig01_charging_events.csv", [r for r in example["stops"] if r["type"] == "station"])
    write_csv(out / "fig01_physical_summary.csv", example["totals"])
    charges = {
        (r["plan"], int(r["node"])): float(r["charged"])
        for r in example["stops"]
        if r["type"] == "station"
    }
    require(set(charges) == {("CON", 1253), ("STaR", 1248)}, f"Unexpected Fig01 stations: {sorted(charges)}")
    near(charges["CON", 1253], 447.4601742508004, "Fig01 CON charge", atol=1e-8)
    near(charges["STaR", 1248], 69.07831527821554, "Fig01 STaR charge", atol=1e-8)
    by_method = {m["method"]: m for m in example["metrics"]}
    require(by_method["CON"]["successes"] == 3063 and by_method["STaR"]["successes"] == 10000, "Fig01 successes")

    method_summary = []
    for method in PUBLICATION_METHODS:
        agg = aggregate_method(rows, keys, method)
        method_summary.append(dict(
            method=method,
            label=METHODS[method],
            mean_R_pct=agg["reliability_pct"],
            attained=agg["attained"],
            attained_of=agg["n"],
            full_return=agg["completion"],
            mean_trials=agg["candidates_evaluated"],
            search_draws=agg["scenarios_evaluated"],
            wall_ms=agg["wall_ms"],
        ))
    write_csv(out / "method_summary.csv", method_summary)
    for row, expected in zip(method_summary, (80.97, 95.29, 95.21, 97.31), strict=True):
        round_check(row["mean_R_pct"], expected, f"{row['method']} mean R")

    star = next(r for r in method_summary if r["method"] == "STaR")
    ablation_summary = []
    for method in ABLATIONS:
        agg = aggregate_method(rows, keys, method)
        loss = None if method == "STaR" else (star["mean_R_pct"] - agg["reliability_pct"])
        draw_diff = None if method == "STaR" else (agg["scenarios_evaluated"] - star["search_draws"])
        ablation_summary.append(dict(
            method=method,
            removal=ABLATIONS[method],
            mean_R_pct=agg["reliability_pct"],
            attained=agg["attained"],
            attained_of=agg["n"],
            search_draws=agg["scenarios_evaluated"],
            draw_difference=draw_diff,
            reliability_loss_pp=loss,
            mean_trials=agg["candidates_evaluated"],
            wall_ms=agg["wall_ms"],
            full_return=agg["completion"],
        ))
    write_csv(out / "ablation_summary.csv", ablation_summary)

    pool = read_json(root / "results/phase5/data/summary.json")["pool"]
    all120 = [dict(r) for r in pool if r["cohort"] == "all120" and r["method"] in HOLD_METHODS]
    require(len(all120) == len(HOLD_METHODS), "Missing all-120 descriptive pool rows")
    write_json(out / "all120_descriptive.json", all120)

    npp = next(r for r in ablation_summary if r["method"] == "STaR-NPP")
    display = dict(
        mean_R={r["method"]: round(r["mean_R_pct"], 2) for r in method_summary},
        contrasts_pp={
            r["comparison"]: [round(r["mean_pp"], 2), round(r["lo95_pp"], 2), round(r["hi95_pp"], 2)]
            for r in paired_summaries
        },
        visit_bins_n=[visit_bins[0]["n"], visit_bins[1]["n"], visit_bins[2]["n"]],
        visit_bins_nonattained=[visit_bins[0]["nonattained"], visit_bins[1]["nonattained"], visit_bins[2]["nonattained"]],
        fig01_successes=[3063, 10000],
        ablation_R={r["method"]: round(r["mean_R_pct"], 2) for r in ablation_summary},
        npp_draw_delta=npp["draw_difference"],
    )
    write_json(out / "display_anchors.json", display)

    fspc = archive_effects["FSPC"]
    sls = archive_effects["SLS"]
    fspc_trials = aggregate_method(rows, keys, "FSPC")["candidates_evaluated"]
    sls_agg = aggregate_method(rows, keys, "SLS")
    as1 = next(
        r for r in csv_rows(root / "results/phase6/data/as1_paired_effects.csv")
        if (r["cohort"], r["subset"], r["tape"], r["challenger"], r["reference"], r["metric"])
        == ("all120", "all", "phase6", "AS1", "STaR", "R_pp")
    )
    as1_completion = next(
        r for r in csv_rows(root / "results/phase6/data/as1_paired_effects.csv")
        if (r["cohort"], r["subset"], r["tape"], r["challenger"], r["reference"], r["metric"])
        == ("all120", "all", "phase6", "AS1", "STaR", "completion")
    )
    ft = next(
        r for r in csv_rows(root / "results/phase6/data/fixed-topology_paired_effects.csv")
        if (r["cohort"], r["subset"], r["tape"], r["challenger"], r["reference"], r["metric"])
        == ("all120", "all", "phase6", "STaR", "FT-SAA", "R_pp")
    )
    ft_completion = next(
        r for r in csv_rows(root / "results/phase6/data/fixed-topology_paired_effects.csv")
        if (r["cohort"], r["subset"], r["tape"], r["challenger"], r["reference"], r["metric"])
        == ("all120", "all", "phase6", "STaR", "FT-SAA", "completion")
    )
    disclosure = dict(
        schema=1,
        purpose="Text-only archival disclosure for methods excluded from Prompt-09 figures/tables",
        archive=dict(commit=ARCHIVE_COMMIT, tag=ARCHIVE_TAG, freeze_commit=FREEZE_COMMIT, freeze_tag=FREEZE_TAG),
        registered_primary=dict(
            comparison="STaR-FSPC",
            cohort="holdout",
            profile="c64",
            metric="reliability",
            n=2321,
            parents=48,
            mean_pp=100 * float(fspc["mean"]),
            lo95_pp=100 * float(fspc["lo95"]),
            hi95_pp=100 * float(fspc["hi95"]),
            display="+1.24 pp [0.86, 1.65]",
            status="confirmatory",
            source="results/phase5/data/paired_effects.csv",
            archive_tag_ref=f"{ARCHIVE_TAG}:results/phase5/data/paired_effects.csv",
        ),
        sls_exploratory=dict(
            comparison="STaR-SLS",
            mean_pp=100 * float(sls["mean"]),
            lo95_pp=100 * float(sls["lo95"]),
            hi95_pp=100 * float(sls["hi95"]),
            display="+0.32 pp",
            status=sls["status"],
            search_draws=dict(
                star=star["search_draws"],
                sls=sls_agg["scenarios_evaluated"],
                relative_reduction_pct=100 * (1 - star["search_draws"] / sls_agg["scenarios_evaluated"]),
            ),
            wall_ms=dict(star=star["wall_ms"], sls=sls_agg["wall_ms"]),
            wall_display="29.69 vs 27.51",
            source="results/phase5/data/paired_effects.csv",
            archive_tag_ref=f"{ARCHIVE_TAG}:results/phase5/data/paired_effects.csv",
        ),
        trial_workload=dict(
            star_mean_trials=star["mean_trials"],
            fspc_mean_trials=fspc_trials,
            display="62.67 vs 20.18",
            note="Common archived c64 maximum of 64 distinct trials",
        ),
        phase6_as1=dict(
            panel="113-route Phase 6 one-visit panel",
            contrast="AS1 minus STaR",
            mean_pp=float(as1["mean"]),
            lo95_pp=float(as1["lo95"]),
            hi95_pp=float(as1["hi95"]),
            completion_mean=float(as1_completion["mean"]),
            note="AS1 restricted to at most one visit; reliability interval crosses zero; exploratory",
            source="results/phase6/data/as1_paired_effects.csv",
            archive_tag_ref=f"{ARCHIVE_TAG}:results/phase6/data/as1_paired_effects.csv",
        ),
        phase6_ft_saa=dict(
            panel="118-route Phase 6 fixed-topology panel",
            contrast="STaR minus FT-SAA",
            mean_pp=float(ft["mean"]),
            lo95_pp=float(ft["lo95"]),
            hi95_pp=float(ft["hi95"]),
            completion_mean=float(ft_completion["mean"]),
            note="Five of 22 multi-visit cases obtained complete MILP certificates; valid fallbacks remain; exploratory",
            source="results/phase6/data/fixed-topology_paired_effects.csv",
            archive_tag_ref=f"{ARCHIVE_TAG}:results/phase6/data/fixed-topology_paired_effects.csv",
        ),
        npp_identity=dict(
            routes=len(keys),
            identical_fields=("reliability", "successes", "attained", "completion"),
            verified=True,
        ),
        fig01=dict(
            parent="C1_10_3",
            variant="A",
            route=106,
            stations={"CON": 1253, "STaR": 1248},
            charges={"CON": charges["CON", 1253], "STaR": charges["STaR", 1248]},
            successes={"CON": 3063, "STaR": 10000},
        ),
    )
    write_json(out / "archival_disclosure.json", disclosure)

    by_cmp = {r["comparison"]: r for r in paired_summaries}
    for name, mean_e, lo_e, hi_e in (
        ("CON", 16.35, 14.57, 18.12),
        ("MWR", 2.02, 1.60, 2.43),
        ("QBR", 2.10, 1.36, 2.91),
    ):
        round_check(by_cmp[name]["mean_pp"], mean_e, f"{name} contrast mean")
        round_check(by_cmp[name]["lo95_pp"], lo_e, f"{name} contrast lo")
        round_check(by_cmp[name]["hi95_pp"], hi_e, f"{name} contrast hi")
    round_check(disclosure["registered_primary"]["mean_pp"], 1.24, "FSPC mean")
    round_check(disclosure["registered_primary"]["lo95_pp"], 0.86, "FSPC lo")
    round_check(disclosure["registered_primary"]["hi95_pp"], 1.65, "FSPC hi")
    round_check(disclosure["sls_exploratory"]["mean_pp"], 0.32, "SLS mean")
    round_check(star["mean_trials"], 62.67, "STaR trials")
    round_check(fspc_trials, 20.18, "FSPC trials")
    round_check(star["wall_ms"], 29.69, "STaR wall")
    round_check(sls_agg["wall_ms"], 27.51, "SLS wall")
    require(
        [round(100 * r["nonattainment_rate"], 2) for r in visit_bins] == [0.25, 2.52, 17.74],
        "Visit nonattainment display rates",
    )

    head = git(root, "rev-parse", "HEAD").decode().strip()
    freeze_tip = git(root, "rev-parse", f"{FREEZE_TAG}^{{}}").decode().strip()
    archive_tip = git(root, "rev-parse", f"{ARCHIVE_TAG}^{{}}").decode().strip()
    require(freeze_tip == FREEZE_COMMIT, "Freeze tag moved")
    require(archive_tip == ARCHIVE_COMMIT, "Archive tag tip unexpected")

    produced = sorted(p for p in out.iterdir() if p.is_file() and p.name != "snapshot_manifest.json")
    file_hashes = {p.name: file_sha(p) for p in produced}
    source_hashes = {path: file_sha(root / path) for path in SOURCE_PATHS if (root / path).exists()}
    manifest = dict(
        schema=1,
        created_by="scripts/extract_publication_inputs.py",
        commit=head,
        archive_commit=ARCHIVE_COMMIT,
        archive_tag=ARCHIVE_TAG,
        freeze_commit=FREEZE_COMMIT,
        freeze_tag=FREEZE_TAG,
        frozen_optimizer=FREEZE_COMMIT,
        holdout_exposed_routes=len(keys),
        holdout_parents=len(parents),
        methods=list(HOLD_METHODS),
        plot_comparators=list(PLOT_COMPARATORS),
        input_sha256=file_hashes,
        files=file_hashes,
        source_archive_paths=list(SOURCE_PATHS),
        source_archive_sha256=source_hashes,
        fig01_paths=example["paths"],
        verified=dict(
            mean_R_pct=[round(r["mean_R_pct"], 2) for r in method_summary],
            contrasts_pp={
                name: [
                    round(by_cmp[name]["mean_pp"], 2),
                    round(by_cmp[name]["lo95_pp"], 2),
                    round(by_cmp[name]["hi95_pp"], 2),
                ]
                for name in PLOT_COMPARATORS
            },
            visit_bins={r["bin"]: [r["n"], r["nonattained"]] for r in visit_bins},
            npp_identical_outcomes=True,
            fig01_successes={"CON": 3063, "STaR": 10000},
            fig01_stations={"CON": 1253, "STaR": 1248},
        ),
        prior_archive=dict(
            phase3_batches=prior["phase3_batches"],
            phase5_release_hashes=prior["phase5_release_hashes"],
            primary_estimate=prior["primary"]["estimate"],
        ),
    )
    write_json(out / "snapshot_manifest.json", manifest)

    return {
        "mean_R": [round(r["mean_R_pct"], 2) for r in method_summary],
        "contrasts": {
            name: {
                "mean": round(by_cmp[name]["mean_pp"], 2),
                "lo": round(by_cmp[name]["lo95_pp"], 2),
                "hi": round(by_cmp[name]["hi95_pp"], 2),
            }
            for name in PLOT_COMPARATORS
        },
        "visit_bins": {r["bin"]: {"n": r["n"], "nonattained": r["nonattained"]} for r in visit_bins},
        "npp_identical": True,
        "fig01_successes": {"CON": 3063, "STaR": 10000},
        "files": sorted(p.name for p in out.iterdir() if p.is_file()),
    }


def main():
    root = ROOT
    out = root / OUT_REL
    if out.exists():
        for path in out.iterdir():
            if path.is_file():
                path.unlink()
    out.mkdir(parents=True, exist_ok=True)
    checks = extract(root, out)
    print("Publication input snapshot written to", out.as_posix())
    print("Verified anchors:", checks)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - surface exact extraction failure
        sys.exit(f"extract_publication_inputs failed: {exc}")
