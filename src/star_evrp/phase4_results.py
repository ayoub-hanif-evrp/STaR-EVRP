"""Independent, read-only reconciliation of frozen Phase 3 outcomes (schema 1)."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist, fmean
from zipfile import ZipFile

import numpy as np
import yaml

from star_evrp.data_loader import load_instance
from star_evrp.deterministic_simulator import SimulatorConfig, simulate_route_fixed
from star_evrp.types import Route, RouteStop

VERSION = "4.0.0"
PHASE3 = "results/phase3"
FREEZE = "c657aa69d55178c85b4759475933b36d1bcc2181"
PUBLISHED = "149d9f4d8f616d78ce0c295696515f1bbc342967"
PROFILES = ("c64", "c24", "s8192", "c64_seed2")
METHODS = ("B0", "B1", "B2", "B3", "B4", "STaR", "STaR_no_partial")
FAMILIES = ("C1", "C2", "R1", "R2", "RC1", "RC2")
ROUND_RTOL = 5.1e-8
ROUND_ATOL = 1e-11
COMPLETION_TIE = 1e-8


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def git(root, *arguments):
    return subprocess.check_output(["git", *arguments], cwd=root)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False, indent=2) + "\n", encoding="utf-8")


def indexed(rows, key):
    result = {}
    for row in rows:
        item = key(row)
        require(item not in result, f"Duplicate record: {item}")
        result[item] = row
    return result


def grouped(rows, key):
    result = defaultdict(list)
    for row in rows:
        result[key(row)].append(row)
    return result


def require_keys(actual, expected, label):
    require(set(actual) == set(expected), f"{label}: missing {len(set(expected)-set(actual))}; extra {len(set(actual)-set(expected))}")


def wilson(successes, total, *, one_sided):
    proportion = successes / total
    quantile = NormalDist().inv_cdf(.95 if one_sided else .975)
    square = quantile ** 2
    margin = quantile * math.sqrt(total * proportion * (1 - proportion) + square / 4)
    center = successes + square / 2
    return max(0., (center - margin) / (total + square)), min(1., (center + margin) / (total + square))


def route_key(row):
    return row["parent"], row["variant"], row["route"]


def observed_counts(source):
    nodes = [stop["node_id"] for stop in source["stops"]]
    customers = tuple(node for node in nodes if 0 < node <= 1000)
    gap, topology = 0, []
    require(nodes[0] == nodes[-1] == 0 and 0 not in nodes[1:-1], "Invalid depot placement")
    for node in nodes[1:-1]:
        if node <= 1000:
            gap += 1
        else:
            topology.append((gap, node))
    return customers, tuple(topology)


def plan_link(raw, plan, source):
    require(raw["plan_sha256"] == sha(canonical(plan)), "Wrong selected-plan hash")
    customers, stations = observed_counts(plan)
    original, old_stations = observed_counts(source)
    require(customers == original and sha(canonical(list(customers))) == plan["customer_sha256"], "Changed customer sequence")
    require([list(item) for item in stations] == plan["station_positions"], "Misencoded ordered station-gap sequence")
    require(plan["method"] != "B4" or stations == old_stations, "B4 changed station topology")
    require(plan["method"] != "B0" or plan["stops"] == source["stops"], "B0 changed original plan")


def strata(cases):
    result = {}
    for parent, siblings in grouped(cases, lambda row: row["parent_key"]).items():
        families = {item["family"] for item in siblings}
        require(len(siblings) == 2 and {row["variant"] for row in siblings} == {"A", "B"} and len(families) == 1,
                f"Broken parent block: {parent}")
        result[parent] = families.pop()
    return dict(sorted(result.items()))


def bootstrap(values, parents, seed=312406, replicates=9999):
    """Return route-weighted and equally weighted nonempty-parent percentile intervals."""
    by_parent = grouped(values, lambda pair: pair[0])
    names = sorted(parents)
    require(set(by_parent) <= set(names), "Foreign parent in paired sample")
    sample = np.array([sum(value for _, value in by_parent[name]) for name in names])
    number = np.array([len(by_parent[name]) for name in names])
    if not number.sum():
        return (None,) * 6
    rng = np.random.default_rng(seed)
    indices = grouped(range(len(names)), lambda index: parents[names[index]])
    draws = np.concatenate([rng.choice(group, (replicates, len(group)), replace=True)
                            for group in indices.values()], axis=1)
    nonempty = number[draws].sum(axis=1) > 0
    averages = np.divide(sample, number, out=np.zeros_like(sample, dtype=float), where=number != 0)
    weighted_draws = sample[draws].sum(axis=1)[nonempty] / number[draws].sum(axis=1)[nonempty]
    balanced_draws = averages[draws].sum(axis=1)[nonempty] / (number[draws] != 0).sum(axis=1)[nonempty]
    return (float(sample.sum() / number.sum()), *map(float, np.quantile(weighted_draws, (.025, .975))),
            float(averages[number > 0].mean()), *map(float, np.quantile(balanced_draws, (.025, .975))))


def probability_to_pp(value):
    return 100 * value


def audit_validation(value, seed, key, cfg, zero_time):
    successes, total = value["successes"], value["n"]
    require(total == cfg["validation_samples"] == 10000 and type(successes) is int and 0 <= successes <= total, "Invalid validation counts")
    rate = successes / total
    require(value["reliability"] == rate, "Validation reliability not successes/n")
    lower = wilson(successes, total, one_sided=True)[0]
    bounds = wilson(successes, total, one_sided=False)
    require(math.isclose(value["wilson95_lower_one_sided"], lower, abs_tol=2e-14), "Incorrect one-sided Wilson")
    require(all(math.isclose(actual, expected, abs_tol=2e-14) for actual, expected
                in zip(value["wilson95_two_sided"], bounds, strict=True)), "Incorrect two-sided Wilson")
    require(value["attained"] == (lower >= cfg["target"]), "Wrong lower-bound attainment")
    expected = int(sha("|".join(map(str, (seed, *key, "holdout", "scenario_z"))).encode())[:16], 16) % (2**31-1)
    require(value["tape_seed"] == expected, "Incorrect independent holdout tape key")
    cust, depot, both = (value[name] for name in ("late_customer", "late_depot", "late_both"))
    require(0 <= both <= min(cust, depot) and cust + depot - both == total - successes and value["late_station"] == 0,
            "Timing failure counts incompatible with joint success")
    quantiles = value["completion_quantiles"]
    require(len(quantiles) == 21 and list(quantiles) == sorted(quantiles) and math.isfinite(value["completion"])
            and zero_time - 1e-8 <= quantiles[0] <= value["completion"] + 1e-8 <= quantiles[-1] + 2e-8,
            "Completion distribution incompatible with full zero-wait baseline")
    require(0 <= value["mean_customer_tardiness"] <= value["max_customer_tardiness"], "Invalid tardiness summary")


def scope_files(root):
    paths = set(git(root, "ls-tree", "-r", "--name-only", "HEAD", "--",
                    PHASE3, "docs/PHASE3", "configs/phase3_frozen.yaml").decode().splitlines())
    paths.update(path.relative_to(root).as_posix() for path in (root / "docs").glob("PHASE3_*.md"))
    paths.update(path.relative_to(root).as_posix() for path in (root / PHASE3).rglob("*") if path.is_file())
    return {name: file_sha(root / name) for name in sorted(paths)}


def unchanged_scope(root, lineage):
    require(scope_files(root)==lineage["published_artifacts_sha256"],"Original Phase 3 files changed")
    for name, expected in lineage["dataset_sha256"].items():
        require(file_sha(root/name)==expected, f"Dataset changed: {name}")
    for name, expected in lineage["frozen_git_blobs_sha256"].items():
        data=(root/name).read_bytes()
        require(expected in (sha(data),sha(data.replace(b"\r\n",b"\n"))),f"Frozen code changed: {name}")


def check_lineage(root):
    base = root / PHASE3
    freeze = read_json(base / "manifests/freeze.json")
    require(freeze["schema"] == 1 and freeze["commit"] == FREEZE and
            git(root, "rev-list", "-n1", freeze["tag"]).decode().strip() == FREEZE, "Wrong frozen revision")
    for name, expected in freeze["git_blob_sha256"].items():
        tagged = git(root, "show", f"{FREEZE}:{name}")
        local = (root / name).read_bytes()
        require(sha(tagged) == expected and tagged in (local, local.replace(b"\r\n", b"\n")), f"Frozen source changed: {name}")
    for name, expected in freeze["dataset_sha256"].items():
        require(file_sha(root / name) == expected, f"Dataset file hash mismatch: {name}")
    provenance = read_json(base / "processed/provenance.json")
    token = sha(canonical(freeze))
    require(provenance["freeze"] == token, "Phase 3 derived provenance has wrong freeze")
    for name, expected in provenance["generated"].items():
        require(file_sha(base / name) == expected, f"Phase 3 derived file changed: {name}")
    for name, expected in provenance["reports"].items():
        require(file_sha(base / f"reports/{name}.json") == expected, f"Phase 3 report changed: {name}")
    marker = {name: read_json(base / f"manifests/{name}.json") for name in ("preflight", "smoke", "started")}
    require(marker["preflight"]["status"] == "pass" and marker["preflight"]["head"] == FREEZE
            and not marker["preflight"]["holdout_outcomes_accessed"] and marker["preflight"]["source_blobs"] == freeze["git_blob_sha256"]
            and file_sha(base / "manifests/preflight.json") == freeze["preflight_sha256"], "Preflight proof mismatch")
    require(marker["smoke"]["freeze"] == marker["started"]["freeze"] == token
            and marker["started"]["tag"] == freeze["tag"], "Freeze/smoke/start markers mismatch")
    cfg = freeze["config"]
    require(yaml.safe_load((root / freeze["config_path"]).read_text(encoding="utf-8")) == cfg
            and not cfg["station_windows"] and cfg["target"] == .95 and cfg["primary"] == "c64"
            and cfg["statistical_seed"] == 312406 and cfg["bootstrap_draws"] == 9999, "Unsupported frozen configuration")
    require_keys(cfg["profiles"], PROFILES, "Frozen profiles")
    for profile, rule in cfg["profiles"].items():
        require(tuple(rule["methods"]) == (METHODS if profile == "c64" else ("B3", "B4", "STaR")), "Wrong frozen method set")
    original = read_json(root / "results/manifests/dataset_inventory.json")["instances"]
    require(len(original) == 120, "Wrong inventory size")
    parents = strata(freeze["holdout"])
    development = [row for row in original if row["partition"] == "development"]
    dev_parents = strata(development)
    allow = yaml.safe_load((root / "configs/experiment_splits.yaml").read_text(encoding="utf-8"))
    require(len(dev_parents) == 12 and not set(dev_parents) & set(parents)
            and Counter(parents.values()) == {family: 8 for family in FAMILIES}
            and dev_parents == {name: family for family, names in allow["development_parents"].items() for name in names}
            and freeze["holdout"] == sorted((row for row in original if row["partition"] == "holdout"),
                                          key=lambda row: (row["instance_key"], row["variant"])), "Frozen parent split mismatch")
    station = grouped(original, lambda row: row["stations_sha256"])
    frozen_station_files = Counter(value for name, value in freeze["dataset_sha256"].items() if name.endswith("_stations.csv"))
    require(frozen_station_files == {key: len(items) for key, items in station.items()}, "Station content inventory mismatch")
    for path, expected in scope_files(root).items():
        if "/raw/con/" in path:
            continue
        original_bytes = git(root, "show", f"{PUBLISHED}:{path}")
        require(expected in (sha(original_bytes), sha(original_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))),
                f"Published Phase 3 artifact changed: {path}")
    return freeze, provenance, token, parents, station


@dataclass
class Study:
    freeze: dict
    parents: dict
    station_tables: dict
    cases: list
    rows: dict
    plans: dict
    lineage: dict
    summary: dict


def bundle(data, expected, context):
    require(sha(data) == expected, "Compressed byte hash mismatch")
    loaded = json.loads(gzip.decompress(data))
    require(loaded["context"] == context and sha(canonical(loaded["rows"])) == loaded["digest"], "Invalid batch context or body")
    return loaded["rows"]


def audit(root: Path) -> Study:
    base = root / PHASE3
    freeze, provenance, token, parents, station = check_lineage(root)
    cfg = freeze["config"]
    execution, replay = (read_json(base / f"reports/{action}.json") for action in ("execution", "replay"))
    prior_audit = read_json(base / "reports/audit.json")
    for log in (execution, replay):
        require(not log["errors"] and log["freeze"] == token and len(log["cases"]) == 96, "Incomplete archived run/replay")
    require(prior_audit["status"] == "pass" and prior_audit["commit"] == FREEZE and prior_audit["tag"] == freeze["tag"],
            "Archived audit did not pass")
    exec_cases, replay_cases = (indexed(log["cases"], lambda case: case["case"]) for log in (execution, replay))
    sources, rows, plans, cases, physically_checked = {}, {}, {}, [], 0
    config = SimulatorConfig(cfg["battery_capacity"], cfg["energy_consumption_rate"], cfg["station_windows"])
    raw_hashes = provenance["raw"]
    collisions = {"validation_route_distinct_seed": {}, "stress_route_distinct_seed": {}}

    with ZipFile(base / "con_bundles.zip") as archive:
        def read(name, context):
            path = base / name
            if name.startswith("raw/con/"):
                data = archive.read(name)
                if path.is_file():
                    require(path.read_bytes() == data, f"Local CON differs from archived bytes: {name}")
            else:
                data = path.read_bytes()
            sources[name] = {"sha256": sha(data), "bytes": len(data)}
            return bundle(data, raw_hashes[name], context)

        for case in freeze["holdout"]:
            parent, variant, family = case["parent_key"], case["variant"], case["family"]
            stem = f"{parent}__{variant}"
            context = {"schema": 1, "freeze": token, "case": stem,
                       "instance_sha256": case["instance_sha256"], "stations_sha256": case["stations_sha256"]}
            con = read(f"raw/con/{stem}.json.gz", context)
            instance = load_instance(root, parent, variant)
            originals = indexed(con["routes"], lambda row: row["route_id"])
            served, exposed = [], []
            for rid, original in originals.items():
                customers, topology = observed_counts(original)
                served.extend(customers)
                if topology:
                    exposed.append(rid)
                route = Route(rid, original["customer_indices"], [RouteStop(**stop) for stop in original["stops"]])
                require(simulate_route_fixed(instance, route, config).feasible, f"Infeasible CON: {stem}/{rid}")
            require(sorted(served) == sorted(instance.customer_node_ids) and len(originals) <= instance.fleet_size, "CON coverage/fleet disagreement")
            exposed.sort()
            expect = {"parent": parent, "variant": variant, "family": family, "case": stem,
                      "routes": len(originals), "exposed": len(exposed), "zero_charge": len(originals)-len(exposed),
                      "eligible_route_ids": exposed, "con_runtime_seconds": con["runtime"]}
            require(all(exec_cases[stem][key] == replay_cases[stem][key] == value for key, value in expect.items()), "Baseline coverage/log discrepancy")
            cases.append(expect)
            case_records = 0
            for profile in PROFILES:
                definition = cfg["profiles"][profile]
                for start in range(0, len(exposed), cfg["batch_routes"]):
                    names = f"{stem}__{start:04d}.json.gz"
                    keys = [(rid, method) for rid in exposed[start:start + cfg["batch_routes"]]
                            for method in definition["methods"]]
                    part = {**context, "profile": profile, "keys": [list(key) for key in keys],
                            "con_digest": sha(canonical(con))}
                    get_key = lambda row: (row["route_id"], row["method"])
                    raw = indexed(read(f"raw/{profile}/{names}", part), get_key)
                    saved = indexed(read(f"plans/{profile}/{names}", part), get_key)
                    require_keys(raw, keys, names)
                    require_keys(saved, keys, names)
                    for rid, method in keys:
                        record, plan = raw[(rid, method)], saved[(rid, method)]
                        key = profile, parent, variant, rid, method
                        require(key not in rows, f"Duplicate canonical key: {key}")
                        plan_link(record, plan, originals[rid])
                        hex_stops = [[stop["node_id"], None if stop["energy_charged"] is None else float(stop["energy_charged"]).hex(),
                                      float(stop["wait_extra"]).hex()] for stop in plan["stops"]]
                        fingerprint = sha(json.dumps(hex_stops, separators=(",", ":")).encode())
                        require(fingerprint == plan["fingerprint"] and all(isinstance(event, list) for event in plan["events"]),
                                "Saved fingerprint or event encoding differs")
                        route = Route(rid, originals[rid]["customer_indices"], [RouteStop(**stop) for stop in plan["stops"]])
                        trace = simulate_route_fixed(instance, route, config)
                        require(trace.feasible and abs(trace.end_clock - plan["zero_wait_completion"]) < 1e-8
                                and abs(trace.total_distance - plan["distance"]) < 1e-8 and len(trace.stops) == len(plan["events"]),
                                f"Selected plan fails deterministic replay: {key}")
                        for trace_stop, event, saved_stop in zip(trace.stops, plan["events"], plan["stops"], strict=True):
                            require(trace_stop.node_id == event[0] and trace_stop.node_type.value == event[1]
                                    and saved_stop["wait_extra"] == 0
                                    and all(abs(a-b) < 1e-8 for a, b in zip(
                                        (trace_stop.service_start_time, trace_stop.departure_time, trace_stop.energy_charged,
                                         instance.node(event[0]).due_date), event[2:])), f"Plan schedule differs: {key}")
                        require(abs(sum(stop.energy_charged for stop in trace.stops) - plan["energy_added"]) < 1e-8, "Wrong plan energy total")
                        physically_checked += 1
                        value = record["validation"]
                        audit_validation(value, cfg["validation_seed"], (parent, variant, rid), cfg, trace.end_clock)
                        collisions["validation_route_distinct_seed"].setdefault(value["tape_seed"], set()).add((parent, variant, rid))
                        expected_stress = cfg["stress"] if profile == "c64" and method in cfg["stress_methods"] else {}
                        require_keys(record["stress"], expected_stress, "Stress membership")
                        for stress in record["stress"].values():
                            audit_validation(stress, cfg["stress_seed"], (parent, variant, rid), cfg, trace.end_clock)
                            collisions["stress_route_distinct_seed"].setdefault(stress["tape_seed"], set()).add((parent, variant, rid))
                        work = record["work"]
                        limits = definition["limits"]
                        step = cfg["opt_samples"] // (4 if method.startswith("STaR") else 1)
                        require(1 <= work["candidates_evaluated"] == work["deterministic_checks"] <= limits["max_candidate_evals"]
                                and 0 <= work["scenarios_evaluated"] <= min(limits["max_scenario_evals"],
                                                                          work["candidates_evaluated"] * cfg["opt_samples"])
                                and work["scenarios_evaluated"] % step == 0
                                and (method not in ("B0","B1","B2") or work["scenarios_evaluated"] == 0)
                                and work["generated"] <= 10 * limits["max_candidate_evals"]
                                and 0 <= record["screen_rejections"] <= work["screen_checks"]
                                and all(work[field] >= 0 and math.isfinite(work[field]) for field in (
                                    "elapsed_seconds", "generation_seconds", "deterministic_seconds", "screening_seconds",
                                    "simulation_seconds")) and record["cpu_seconds"] >= 0, "Invalid candidate/MC/time accounting")
                        rows[key] = {"profile": profile, "parent": parent, "variant": variant, "family": family, "route": rid,
                                     "source": f"raw/{profile}/{names}", **record}
                        plans[key] = plan
                        case_records += 1
            require(replay_cases[stem]["replayed"] == case_records, "Replayed count does not match exact route/method coverage")
    require_keys(sources, raw_hashes, "Raw and plan provenance")
    require_keys({path.relative_to(base).as_posix() for scope in ("raw", "plans") for path in (base / scope).glob("*/*.json.gz")
                  if path.parent.name != "con"}, {name for name in sources if not name.startswith("raw/con/")}, "Physical batch filenames")
    require(physically_checked == prior_audit["plans"] == len(rows) and len(sources) == prior_audit["raw_plan_files"], "Prior audit quantities differ")
    require(all(len(routes) == 1 for space in collisions.values() for routes in space.values()), "Unexpected within-stream seed collision")
    lineage = {"phase4_version": VERSION, "head": git(root, "rev-parse", "HEAD").decode().strip(), "frozen_commit": FREEZE,
               "published_source_commit": PUBLISHED, "tag": freeze["tag"], "freeze_digest": token, "schema": freeze["schema"],
               "frozen_git_blobs_sha256": freeze["git_blob_sha256"], "dataset_sha256": freeze["dataset_sha256"],
               "published_artifacts_sha256": scope_files(root), "batches": sources,
               "phase25_context": {name: file_sha(root / f"results/phase25/{name}") for name in ("manifest.json", "analysis_manifest.json")},
               "aggregation": "phase4_results.audit -> phase4_results.derive -> phase4_results.reconcile",
               "validation": "successes/n and standard-library Wilson; deterministic replay, not new Monte Carlo"}
    study = Study(freeze, parents, station, cases, rows, plans, lineage, {})
    study.summary = derive(study)
    study.summary["reconciliation"] = reconcile(base, root / "docs/PHASE3_FINAL_REPORT.md", study)
    study.summary["validation_checked"] = len(rows)
    study.summary["stored_stress_records_checked"] = sum(len(row["stress"]) for row in rows.values())
    return study


def value(row, metric):
    fields = {
        "reliability": lambda: row["validation"]["successes"] / row["validation"]["n"],
        "attained": lambda: int(row["validation"]["attained"]),
        "full_completion": lambda: row["validation"]["completion"],
        "search_scenarios": lambda: row["work"]["scenarios_evaluated"],
        "candidate_evaluations": lambda: row["work"]["candidates_evaluated"],
        "wall_ms": lambda: 1000 * row["work"]["elapsed_seconds"],
        "cpu_ms": lambda: 1000 * row["cpu_seconds"],
    }
    return fields[metric]()


def paired(rows, profile, competitor):
    star = {key[1:4]: row for key, row in rows.items() if key[0] == profile and key[4] == "STaR"}
    control = {key[1:4]: row for key, row in rows.items() if key[0] == profile and key[4] == competitor}
    require_keys(star, control, "Paired denominators")
    return [(row, control[key]) for key, row in star.items()]


def differences(pairs, metric):
    result = []
    for star, control in pairs:
        require(route_key(star) == route_key(control), "Unmatched route")
        if metric == "full_completion_common_attained":
            if not (value(star, "attained") and value(control, "attained")):
                continue
            delta = value(star, "full_completion") - value(control, "full_completion")
        elif metric == "relative_full_completion_percent":
            denominator = value(control, "full_completion")
            if denominator <= 0:
                continue
            delta = 100 * (value(star, "full_completion") / denominator - 1)
        else:
            delta = value(star, metric) - value(control, metric)
        result.append((star["parent"], delta))
    return result


def summarize(rows):
    records = [row["validation"] for row in rows]
    return {
        "n": len(rows), "mean_R": fmean(value(row, "reliability") for row in rows),
        "point_at_target": sum(record["successes"] >= 9500 for record in records),
        "lower_bound_attained": sum(record["attained"] for record in records),
        "two_sided_CI_contains_target": sum(record["wilson95_two_sided"][0] <= .95 <=
                                             record["wilson95_two_sided"][1] for record in records),
        "full_completion_time": fmean(value(row, "full_completion") for row in rows),
        "search_scenarios": fmean(value(row, "search_scenarios") for row in rows),
        "search_wall_ms": fmean(value(row, "wall_ms") for row in rows),
        "search_cpu_ms": fmean(value(row, "cpu_ms") for row in rows),
    }


def failure_reason(record):
    if record["attained"]:
        return "attained"
    if record["successes"] >= 9500:
        return "point_only"
    both = record["late_both"]
    return max(("customer_only", "depot_only", "joint"), key={
        "customer_only": record["late_customer"]-both, "depot_only": record["late_depot"]-both, "joint": both,
    }.get)


def stop_proxy(row, limits):
    work = row["work"]
    if row["method"] == "B0":
        return "not_searched"
    if work["candidates_evaluated"] >= limits["max_candidate_evals"]:
        return "plan_cap"
    if work["scenarios_evaluated"] >= limits["max_scenario_evals"]:
        return "scenario_cap"
    if work["elapsed_seconds"] >= limits["wall_seconds"]:
        return "wall_guard"
    if work["generated"] >= 10 * limits["max_candidate_evals"]:
        return "proposal_cap"
    return "no_limit_logged"


def case_plan(study):
    first = min(route_key(row) for row in study.rows.values() if row["profile"] == "c64" and
                row["family"] == "R2" and row["variant"] == "A")
    result = []
    for method in ("B0", "B4", "STaR"):
        record = study.rows["c64", *first, method]["validation"]
        plan = study.plans["c64", *first, method]
        for position, event in enumerate(plan["events"]):
            node, kind, service, departure, charge, deadline = event
            result.append(dict(parent=first[0], variant=first[1], route=first[2], method=method,
                               stop=position, node=node, kind=kind, zero_wait_service=service,
                               zero_wait_departure=departure, charged_energy=charge, deadline=deadline,
                               validated_route_R=record["reliability"], expected_full_completion=record["completion"]))
    return list(first), result


def derive(study):
    rows, plans = study.rows, study.plans
    cfg = study.freeze["config"]
    main = [row for row in rows.values() if row["profile"] == "c64"]
    batches = grouped(rows.values(), lambda row: (row["profile"], row["method"]))
    budget, work, quality = [], [], []
    work_fields = ("generated", "deterministic_checks", "screen_checks", "generation_seconds",
                   "deterministic_seconds", "screening_seconds", "simulation_seconds")
    for profile in PROFILES:
        rule = cfg["profiles"][profile]
        limits = rule["limits"]
        for method in rule["methods"]:
            records = batches[profile, method]
            budget.append(dict(profile=profile, method=method, unique_plan_cap=limits["max_candidate_evals"],
                               scenario_cap=limits["max_scenario_evals"], cooperative_wall_limit_s=limits["wall_seconds"],
                               **summarize(records), **{f"mean_{field}": fmean(row["work"][field] for row in records)
                                                       for field in work_fields},
                               mean_validation_ms_including_stress_if_applicable=fmean(row["validation_seconds"] * 1000
                                                                                       for row in records),
                               wall_overruns=sum(row["work"]["elapsed_seconds"] > limits["wall_seconds"] for row in records),
                               bound_rejections=sum(row["screen_rejections"] for row in records),
                               prefix_rejections=sum(row["prefix_rejections"] for row in records)))
            counts = [value(row, "candidate_evaluations") for row in records]
            quantiles = np.quantile(counts, [0, .25, .50, .75, 1])
            reasons = Counter(stop_proxy(row, limits) for row in records)
            work.append(dict(profile=profile, method=method, n=len(records), mean_trials=fmean(counts),
                             trial_min=float(quantiles[0]), trial_q1=float(quantiles[1]), trial_median=float(quantiles[2]),
                             trial_q3=float(quantiles[3]), trial_max=float(quantiles[4]),
                             reached_plan_cap=sum(count == limits["max_candidate_evals"] for count in counts),
                             reached_scenario_cap=sum(value(row, "search_scenarios") == limits["max_scenario_evals"] for row in records),
                             **{name: reasons[name] for name in ("plan_cap","scenario_cap","wall_guard","proposal_cap",
                                                                 "no_limit_logged","not_searched")}))
            if method in ("STaR", "B3", "B4"):
                rel = bootstrap([(row["parent"], value(row, "reliability")) for row in records], study.parents)
                quality.append(dict(profile=profile, method=method, mean_R=rel[0], lower95=rel[1], upper95=rel[2]))
    overall = [{"method": item["method"], **summarize(batches["c64", item["method"]])} for item in budget
               if item["profile"] == "c64"]
    family = []
    for (name, variant, method), records in sorted(grouped(main, lambda row: (row["family"], row["variant"], row["method"])).items()):
        base = [rows["c64", *route_key(row), "B0"] for row in records]
        family.append(dict(family=name, variant=variant, method=method, **summarize(records),
                           below_target_B0=sum(item["validation"]["successes"] < 9500 for item in base),
                           repaired=sum(value(row, "attained") for row, item in zip(records, base) if item["validation"]["successes"] < 9500)))
    population = []
    for (name, variant), cases in sorted(grouped(study.cases, lambda row: (row["family"], row["variant"])).items()):
        baseline = [row for row in family if row["family"] == name and row["variant"] == variant and row["method"] == "B0"]
        exposed = sum(row["exposed"] for row in cases)
        require(len(baseline) == 1 and baseline[0]["n"] == exposed, "Exposure not conserved in family")
        population.append(dict(family=name, variant=variant, instances=len(cases), all_routes=sum(row["routes"] for row in cases),
                               exposed=exposed, zero_charge=sum(row["zero_charge"] for row in cases),
                               below_target_B0=baseline[0]["below_target_B0"],
                               B0_lower_bound_nonattainment=exposed-baseline[0]["lower_bound_attained"]))
    count_fields = tuple(population[0])[2:]
    population.append(dict(family="All", variant="A+B", **{key: sum(row[key] for row in population) for key in count_fields}))
    total = population[-1]
    require(total["all_routes"] == total["exposed"] + total["zero_charge"] == 6864 and total["exposed"] == 2321, "Population conservation mismatch")
    effects, parent_effects, pairs_saved = [], [], []
    metrics = ("reliability", "attained", "full_completion", "full_completion_common_attained",
               "relative_full_completion_percent", "search_scenarios", "wall_ms", "cpu_ms", "candidate_evaluations")
    for profile in PROFILES:
        for competitor in cfg["profiles"][profile]["methods"]:
            if competitor == "STaR":
                continue
            pairs = paired(rows, profile, competitor)
            for metric in metrics:
                values = differences(pairs, metric)
                estimate, lower, upper, balanced, b_lower, b_upper = bootstrap(values, study.parents)
                effects.append(dict(profile=profile, competitor=competitor, metric=metric, n=len(values),
                                    parents=len({name for name, _ in values}), estimate=estimate, lower95=lower, upper95=upper,
                                    parent_equal_estimate=balanced, parent_equal_lower95=b_lower, parent_equal_upper95=b_upper,
                                    status="confirmatory" if (profile, competitor, metric) == ("c64","B4","reliability") else "exploratory"))
                if profile == "c64" and competitor in ("B3","B4"):
                    parent_effects.extend(dict(competitor=competitor, metric=metric, parent=parent, family=study.parents[parent],
                                               paired_routes=len(observed), mean_difference=fmean(item[1] for item in observed))
                                          for parent, observed in sorted(grouped(values, lambda item: item[0]).items()))
            if competitor in ("B3","B4"):
                for star, other in pairs:
                    key = route_key(star)
                    pairs_saved.append(dict(profile=profile, competitor=competitor, family=star["family"],
                                            parent=key[0], variant=key[1], route=key[2],
                                            star_successes=star["validation"]["successes"], other_successes=other["validation"]["successes"],
                                            topology_changed=plans[profile, *key, "STaR"]["station_positions"] !=
                                                             plans[profile, *key, competitor]["station_positions"],
                                            source=star["source"],
                                            **{f"delta_{metric}": value(star, metric)-value(other, metric) for metric in (
                                                "reliability", "attained", "full_completion", "candidate_evaluations",
                                                "search_scenarios", "wall_ms", "cpu_ms")}))
    topology = [row for row in pairs_saved if row["profile"] == "c64" and row["competitor"] == "B4"]
    mechanism = []
    for changed, records in sorted(grouped(topology, lambda row: row["topology_changed"]).items()):
        plan_pairs = [(plans["c64", *route_key(row), "STaR"], plans["c64", *route_key(row), "B4"]) for row in records]
        mechanism.append(dict(comparison_stratum="topology_changed" if changed else "same_topology", n=len(records),
                              mean_delta_R=fmean(row["delta_reliability"] for row in records),
                              contribution_to_overall_delta_R=sum(row["delta_reliability"] for row in records)/len(topology),
                              mean_delta_completion=fmean(row["delta_full_completion"] for row in records),
                              mean_delta_energy=fmean(star["energy_added"]-other["energy_added"] for star, other in plan_pairs),
                              mean_delta_visits=fmean(len(star["station_positions"])-len(other["station_positions"]) for star, other in plan_pairs)))
    require(abs(sum(row["contribution_to_overall_delta_R"] for row in mechanism) -
                fmean(row["delta_reliability"] for row in topology)) < 1e-14, "Topology strata do not recompose")
    ties = []
    for competitor in ("B4","B3"):
        records = [row for row in pairs_saved if row["profile"] == "c64" and row["competitor"] == competitor]
        for metric in ("reliability","completion"):
            diffs = [(row["star_successes"]-row["other_successes"]) if metric == "reliability"
                     else -row["delta_full_completion"] for row in records]
            tolerance = 0 if metric == "reliability" else COMPLETION_TIE
            ties.append(dict(competitor=competitor, metric=metric, n=len(diffs),
                             better=sum(d > tolerance for d in diffs), tied=sum(abs(d) <= tolerance for d in diffs),
                             worse=sum(d < -tolerance for d in diffs)))
    failures, negative = [], []
    for (name, variant), cases in sorted(grouped((row for row in main if row["method"] == "STaR"),
                                                lambda row: (row["family"], row["variant"])).items()):
        counts = Counter(failure_reason(row["validation"]) for row in cases)
        failures.append(dict(family=name, variant=variant, n=len(cases),
                             **{key: counts[key] for key in ("attained","point_only","customer_only","depot_only","joint")}))
        for row in cases:
            record = row["validation"]
            if not record["attained"]:
                negative.append(dict(parent=row["parent"], variant=variant, family=name, route=row["route"],
                                     reason=failure_reason(record), successes=record["successes"], R=record["reliability"],
                                     wilson_low=record["wilson95_lower_one_sided"], customer_fail=record["late_customer"],
                                     depot_fail=record["late_depot"], joint_fail=record["late_both"]))
    require(len(negative) == total["exposed"]-next(row for row in overall if row["method"]=="STaR")["lower_bound_attained"],
            "STaR failure count mismatch")
    stress = []
    for name, spec in cfg["stress"].items():
        for method in cfg["stress_methods"]:
            saved = [row["stress"][name] for row in batches["c64", method]]
            stress.append(dict(stress=name, method=method, wait_scale=spec["scale"], sigma_scale=spec["sigma"],
                               normal_copula_rho=spec["rho"], n=len(saved), mean_R=fmean(row["successes"]/row["n"] for row in saved),
                               lower_bound_attained=sum(row["attained"] for row in saved), full_completion=fmean(row["completion"] for row in saved)))
    station = [dict(sha256=digest, problems=len(items), holdout=sum(row["partition"] == "holdout" for row in items),
                    development=sum(row["partition"] == "development" for row in items))
               for digest, items in sorted(study.station_tables.items())]
    first, events = case_plan(study)
    return dict(overall=overall, population=population, family_variant=family, paired=effects, parent_effects=parent_effects,
                work=work, budget=budget, mechanism=mechanism, robustness=stress, reliability_quality=quality, ties=ties,
                failures=failures, negative=negative, station_tables=station, example=first, case_routes=events, pairs=pairs_saved)


def compare_csv(path, expected, keys):
    with path.open(encoding="utf-8", newline="") as handle:
        published = indexed(csv.DictReader(handle), lambda row: tuple(str(row[key]) for key in keys))
    derived = indexed(expected, lambda row: tuple(str(row[key]) for key in keys))
    require_keys(published, derived, path.name)
    errors, max_abs = [], 0.
    for index, row in published.items():
        require(index in derived, f"Missing reconstructed row {path.name}/{index}")
        for key, old in row.items():
            new = derived[index][key]
            if isinstance(new, int):
                match = float(old) == new
            elif isinstance(new, float):
                delta = abs(float(old) - new)
                max_abs = max(max_abs, delta)
                match = math.isclose(float(old), new, rel_tol=ROUND_RTOL, abs_tol=ROUND_ATOL)
            else:
                match = old == ("" if new is None else str(new))
            if not match:
                errors.append((index, key, old, new))
    require(not errors, f"{path.name}: {len(errors)} discrepancies (first ones: {errors[:8]})")
    return {"matched_rows": len(published), "maximum_absolute_difference_before_rounding": max_abs}


def reconcile(base, report_path, study):
    summary = study.summary
    keysets = {"overall": ("method",), "population": ("family","variant"),
               "family_variant": ("family","variant","method"), "paired": ("profile","competitor","metric"),
               "budget": ("profile","method"), "mechanism": ("comparison_stratum",),
               "robustness": ("stress","method"), "case_routes": ("parent","variant","route","method","stop"),
               "parent_effects": ("competitor","metric","parent")}
    checks = {name: compare_csv(base / "tables" / f"{name}.csv", [
        row for row in summary[name] if name not in ("paired","parent_effects")
        or row["metric"] not in ("cpu_ms","candidate_evaluations")
    ], keys) for name, keys in keysets.items()}
    report = report_path.read_text(encoding="utf-8")
    count_line = summary["population"][-1]
    for column in ("all_routes", "exposed", "zero_charge", "below_target_B0"):
        require(f'{count_line[column]:,}' in report, f"Final report population differs: {column}")
    for row in summary["overall"]:
        expected = (f'| {row["method"]} | {100*row["mean_R"]:.2f}% | {row["lower_bound_attained"]:,}/{row["n"]:,} | '
                    f'{row["full_completion_time"]:,.2f} | {row["search_scenarios"]:,.0f} | {row["search_wall_ms"]:.2f} |')
        require(expected in report, f"Final report method row disagrees: {row['method']}")
    effect = next(row for row in summary["paired"] if row["status"] == "confirmatory")
    citation = f'{100*effect["estimate"]:+.2f} [{100*effect["lower95"]:+.2f}, {100*effect["upper95"]:+.2f}]'
    require(citation in report, "Primary effect in Phase 3 report inconsistent")
    for comparator,metric,scale in (("B3","reliability",100),("B4","full_completion",1),("B3","wall_ms",1)):
        effect=next(row for row in summary["paired"] if
                    (row["profile"],row["competitor"],row["metric"])==("c64",comparator,metric))
        display=f'{scale * effect["estimate"]:+.2f} [{scale * effect["lower95"]:+.2f}, {scale * effect["upper95"]:+.2f}]'
        require(display in report,f"Phase 3 report mismatch: {comparator}/{metric}")
    return checks
