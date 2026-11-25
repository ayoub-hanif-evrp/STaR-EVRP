"""Load Prompt-09 conference exhibits from the self-contained publication snapshot.

Reads ONLY results/conference/data/inputs/ (or a copied inputs/ under the build
output). Does not call load_archive or read results/phase*.
"""

from __future__ import annotations

from math import isclose
from pathlib import Path

from star_evrp.phase4_results import file_sha, read_json, require
from star_evrp.phase6_archive import csv_rows, write_json

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
DISPLAY = ("CON", "MWR", "QBR", "STaR")
FROZEN = "c657aa69d55178c85b4759475933b36d1bcc2181"
ARCHIVE_TAG = "star-research-archive-v1"
ARCHIVE_COMMIT = "1ad987a328679263e5d8ba40330ffe1a11409db1"
PRIMARY = (0.012420292977165015, 0.008630955453232267, 0.016503459913289817)
INPUTS = Path("results/conference/data/inputs")
REQUIRED_INPUTS = (
    "ablation_summary.csv",
    "all120_descriptive.json",
    "archival_disclosure.json",
    "config.json",
    "display_anchors.json",
    "fig01_charging_events.csv",
    "fig01_metrics.csv",
    "fig01_nodes.csv",
    "fig01_physical_summary.csv",
    "fig01_route.json",
    "fig01_stops.csv",
    "holdout_route_metrics.csv",
    "method_summary.csv",
    "paired_effects_holdout.csv",
    "paired_routes_CON.csv",
    "paired_routes_MWR.csv",
    "paired_routes_QBR.csv",
    "snapshot_manifest.json",
    "visit_bin_effects.csv",
    "visit_bin_routes.csv",
)


def near(value, expected, label, atol=2e-10):
    require(
        isclose(float(value), float(expected), rel_tol=0, abs_tol=atol),
        f"{label}: {value!r} differs from {expected!r}",
    )


def inputs_dir(root: Path, out: Path | None = None) -> Path:
    candidates = []
    if out is not None:
        candidates.append(out / "data" / "inputs")
    candidates.extend((root / INPUTS, root / "results" / "conference" / "data" / "inputs"))
    for path in candidates:
        if (path / "snapshot_manifest.json").is_file():
            return path
    raise FileNotFoundError(
        "Missing publication inputs under results/conference/data/inputs/. "
        "Restore from tag star-research-archive-v1 and run "
        "scripts/extract_publication_inputs.py."
    )


def _num(row, field):
    value = row.get(field)
    if value in (None, "", "NA"):
        return None
    return float(value)


def _truth(value):
    return value in (True, "True", "true", "1", 1)


def load_snapshot(root: Path, out: Path | None = None) -> dict:
    base = inputs_dir(root, out)
    for name in REQUIRED_INPUTS:
        require((base / name).is_file(), f"Missing snapshot input: {name}")

    manifest = read_json(base / "snapshot_manifest.json")
    require(manifest["archive_commit"] == ARCHIVE_COMMIT, "Snapshot archive commit mismatch")
    freeze = manifest.get("frozen_optimizer") or manifest.get("freeze_commit")
    require(freeze == FROZEN, "Snapshot freeze mismatch")
    file_map = manifest.get("files") or manifest.get("input_sha256") or {}
    for relative, digest in file_map.items():
        path = base / relative
        require(path.is_file(), f"Missing snapshot file {relative}")
        require(file_sha(path) == digest, f"Snapshot hash mismatch: {relative}")

    config = read_json(base / "config.json")
    anchors = read_json(base / "display_anchors.json")
    disclosure = read_json(base / "archival_disclosure.json")

    raw_methods = csv_rows(base / "method_summary.csv")
    methods = []
    for row in raw_methods:
        methods.append(dict(
            method=row["method"],
            label=row.get("label") or METHODS[row["method"]],
            reliability_pct=_num(row, "mean_R_pct"),
            attained=int(_num(row, "attained")),
            n=int(_num(row, "attained_of")),
            completion=_num(row, "full_return"),
            trials=_num(row, "mean_trials"),
            draws=_num(row, "search_draws"),
            wall_ms=_num(row, "wall_ms"),
        ))
    require([r["method"] for r in methods] == list(DISPLAY), "Method order")
    require(
        {r["method"]: round(r["reliability_pct"], 2) for r in methods} == anchors["mean_R"],
        "Mean R anchors",
    )
    require([r["attained"] for r in methods] == [1686, 2052, 2183, 2211], "Attainment counts")
    require(all(r["n"] == 2321 for r in methods), "Method denominator")

    raw_abl = csv_rows(base / "ablation_summary.csv")
    ablations = []
    for row in raw_abl:
        ablations.append(dict(
            method=row["method"],
            component=row.get("removal") or ABLATIONS[row["method"]],
            reliability_pct=_num(row, "mean_R_pct"),
            attained=int(_num(row, "attained")),
            n=int(_num(row, "attained_of")),
            draws=_num(row, "search_draws"),
            draw_delta=_num(row, "draw_difference"),
            loss_pp=_num(row, "reliability_loss_pp"),
            trials=_num(row, "mean_trials"),
            wall_ms=_num(row, "wall_ms"),
            completion=_num(row, "full_return"),
        ))
    require([r["method"] for r in ablations] == list(ABLATIONS), "Ablation order")
    require(
        {r["method"]: round(r["reliability_pct"], 2) for r in ablations} == anchors["ablation_R"],
        "Ablation R anchors",
    )
    full = ablations[0]
    for reduced in ablations[1:]:
        near(
            full["reliability_pct"] - reduced["reliability_pct"],
            reduced["loss_pp"],
            f"{reduced['method']} loss convention",
            atol=1e-12,
        )
        near(
            reduced["draws"] - full["draws"],
            reduced["draw_delta"],
            f"{reduced['method']} draw difference",
            atol=1e-9,
        )

    paired = []
    for row in csv_rows(base / "paired_effects_holdout.csv"):
        if row["comparison"] not in ("CON", "MWR", "QBR"):
            continue
        require(
            (row["cohort"], row["profile"], row["metric"]) == ("holdout", "c64", "reliability"),
            "Paired filter",
        )
        paired.append(dict(
            comparison=row["comparison"],
            n=int(row["n"]),
            parents=int(row["parents"]),
            mean_pp=_num(row, "mean_pp"),
            lo95_pp=_num(row, "lo95_pp"),
            hi95_pp=_num(row, "hi95_pp"),
            parent_mean_pp=_num(row, "parent_mean_pp"),
            parent_lo95_pp=_num(row, "parent_lo95_pp"),
            parent_hi95_pp=_num(row, "parent_hi95_pp"),
            status=row["status"],
            higher=int(row["higher"]),
            equal=int(row["equal"]),
            lower=int(row["lower"]),
        ))
    require([r["comparison"] for r in paired] == ["CON", "MWR", "QBR"], "Paired order")
    for row in paired:
        expected = anchors["contrasts_pp"][row["comparison"]]
        require(
            [round(row["mean_pp"], 2), round(row["lo95_pp"], 2), round(row["hi95_pp"], 2)] == expected,
            f"{row['comparison']} display contrast",
        )
        require(row["n"] == 2321 and row["parents"] == 48, f"{row['comparison']} denominator")

    bins = []
    for row in csv_rows(base / "visit_bin_effects.csv"):
        n = int(row["n"])
        nonattained = int(row["nonattained"])
        rate = _num(row, "nonattainment_rate")
        bins.append(dict(
            bin=row["bin"],
            n=n,
            parents=int(row["parents"]),
            nonattained=nonattained,
            nonattainment_rate=rate,
            nonattainment_pct=100.0 * rate,
            mean_pp=_num(row, "mean_pp"),
            lo95_pp=_num(row, "lo95_pp"),
            hi95_pp=_num(row, "hi95_pp"),
        ))
    require([r["bin"] for r in bins] == ["1", "2", "3+"], "Visit bin order")
    require([r["n"] for r in bins] == anchors["visit_bins_n"], "Visit bin n")
    require([r["nonattained"] for r in bins] == anchors["visit_bins_nonattained"], "Visit nonattainment")
    require(
        [round(r["nonattainment_pct"], 2) for r in bins] == [0.25, 2.52, 17.74],
        "Visit nonattainment display rates",
    )

    metrics = csv_rows(base / "holdout_route_metrics.csv")
    by_key = {}
    for row in metrics:
        key = (row["parent"], row["variant"], int(row["route"]), row["method"])
        by_key[key] = row
    star_keys = {(p, v, r) for (p, v, r, m) in by_key if m == "STaR"}
    require(len(star_keys) == 2321, "Holdout exposed denominator")
    for parent, variant, route in star_keys:
        a = by_key[parent, variant, route, "STaR"]
        b = by_key[parent, variant, route, "STaR-NPP"]
        require(
            all(a[field] == b[field] for field in ("reliability", "successes", "completion", "attained")),
            "NPP outcome mismatch",
        )

    selection = read_json(base / "fig01_route.json")
    chosen = selection["chosen"]
    require(
        (chosen["parent"], chosen["variant"], chosen["route"]) == ("C1_10_3", "A", 106),
        "Fig01 route",
    )
    fig_metrics = []
    for row in csv_rows(base / "fig01_metrics.csv"):
        fig_metrics.append(dict(
            method=row["method"],
            successes=int(row["successes"]),
            scenarios=int(row["scenarios"]),
            reliability=float(row["reliability"]),
            completion=float(row["completion"]),
            wilson_lower=float(row["wilson_lower"]),
            attained=_truth(row["attained"]),
            customer_only=int(row["customer_only"]),
            depot_only=int(row["depot_only"]),
            joint=int(row["joint"]),
            tape_seed=int(float(row["tape_seed"])),
            fingerprint=row.get("fingerprint"),
            plan_digest=row.get("plan_digest"),
            source=row.get("source"),
        ))
    require([r["successes"] for r in fig_metrics] == anchors["fig01_successes"], "Fig01 successes")

    stops = []
    for row in csv_rows(base / "fig01_stops.csv"):
        item = dict(row)
        for field in (
            "x", "y", "leg_distance", "distance", "consumed", "charged", "battery_arrival",
            "battery_departure", "arrival", "service_start", "departure", "ready", "due",
            "readiness_wait", "service_duration", "charging_rate", "charging_duration",
            "deadline_slack",
        ):
            item[field] = _num(row, field)
        for field in ("index", "node", "customer_order", "station_order", "customers_served"):
            item[field] = None if row.get(field) in (None, "", "NA") else int(float(row[field]))
        stops.append(item)

    nodes = []
    for row in csv_rows(base / "fig01_nodes.csv"):
        nodes.append(dict(node=int(float(row["node"])), type=row["type"],
                          x=float(row["x"]), y=float(row["y"])))

    charges = [r for r in stops if r["type"] == "station"]
    require({(r["plan"], r["node"]) for r in charges} == {("CON", 1253), ("STaR", 1248)}, "Fig01 stations")
    near(next(r["charged"] for r in charges if r["plan"] == "CON"), 447.4601742508004, "CON charge")
    near(next(r["charged"] for r in charges if r["plan"] == "STaR"), 69.07831527821554, "STaR charge")

    npp_row = next(r for r in ablations if r["method"] == "STaR-NPP")
    saved = npp_row["draws"] - full["draws"]
    near(saved, anchors["npp_draw_delta"], "NPP draw delta", atol=1e-9)
    reduction = 100.0 * saved / npp_row["draws"]

    registered = disclosure["registered_primary"]
    near(registered["mean_pp"] / 100.0, PRIMARY[0], "Registered primary mean", atol=1e-14)
    near(registered["lo95_pp"] / 100.0, PRIMARY[1], "Registered primary lo", atol=1e-14)
    near(registered["hi95_pp"] / 100.0, PRIMARY[2], "Registered primary hi", atol=1e-14)

    totals = []
    for row in csv_rows(base / "fig01_physical_summary.csv"):
        totals.append(dict(
            method=row["method"],
            capacity=_num(row, "capacity"),
            consumption_rate=_num(row, "consumption_rate"),
            tolerance=_num(row, "tolerance"),
            customers=int(_num(row, "customers")),
            visits=int(_num(row, "visits")),
            total_distance=_num(row, "total_distance"),
            energy_consumed=_num(row, "energy_consumed"),
            energy_added=_num(row, "energy_added"),
            initial_battery=_num(row, "initial_battery"),
            final_battery=_num(row, "final_battery"),
            depot_start=_num(row, "depot_start"),
            zero_wait_return=_num(row, "zero_wait_return"),
            charging_duration=_num(row, "charging_duration"),
            readiness_wait=_num(row, "readiness_wait"),
            service_duration=_num(row, "service_duration"),
        ))

    example = dict(
        selection=selection,
        nodes=nodes,
        stops=stops,
        metrics=fig_metrics,
        totals=totals,
        charges=charges,
    )
    data = dict(
        inputs=base,
        config=config,
        comparison=methods,
        ablation=ablations,
        paired=paired,
        complexity=bins,
        example=example,
        disclosure=disclosure,
        anchors=anchors,
        all120=read_json(base / "all120_descriptive.json"),
        npp=dict(
            full_draws=full["draws"],
            npp_draws=npp_row["draws"],
            saved_draws=saved,
            reduction_pct=reduction,
        ),
        sources={p.name: file_sha(p) for p in sorted(base.iterdir()) if p.is_file()},
        manifest=manifest,
        exact_routewise_npp_equality=True,
    )
    if out is not None:
        (out / "audit").mkdir(parents=True, exist_ok=True)
        write_json(out / "audit" / "numerical.json", dict(
            status="pass",
            holdout_exposed=2321,
            holdout_parents=48,
            methods=list(DISPLAY),
            ablations=list(ABLATIONS),
            visit_bins=[r["n"] for r in bins],
            registered_primary=PRIMARY,
            exact_routewise_npp_equality=True,
            snapshot_files=len(REQUIRED_INPUTS),
            panel_counts={"Fig01": 2, "Fig02": 2, "Fig03": 2, "Fig04": 1},
        ))
    return data


def gather(root: Path, out: Path) -> dict:
    """Build entry used by the exhibit package."""
    return load_snapshot(root, out)
