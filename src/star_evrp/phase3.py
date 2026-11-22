"""Frozen holdout execution, integrity checks, and independent validation."""

from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, process_time

import numpy as np
import yaml

from star_evrp.baseline import generate_baseline
from star_evrp.budget import BudgetConfig
from star_evrp.charge_plan import ChargePlan, customer_node_ids
from star_evrp.competitive_search import optimize
from star_evrp.data_loader import discover_dataset_root, load_instance, sha256_file
from star_evrp.data_validation import validate_instance
from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.experiment_phase2 import load_baseline_solution
from star_evrp.experiment_phase25 import inputs
from star_evrp.results_io import load_json, save_json
from star_evrp.route_validator import validate_repair, validate_solution
from star_evrp.scenario_tapes import generate_z_tape, tape_rng_seed
from star_evrp.statistics import wilson_ci, wilson_lower
from star_evrp.stochastic_simulator import evaluate_route_with_waits
from star_evrp.timing import RouteTiming
from star_evrp.types import NUM_TOL, NodeType, Route, RouteStop, Solution


SCHEMA = 1
DEPENDENCIES = ("numpy", "scipy", "pyyaml", "matplotlib", "pytest")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def config(root, path):
    return yaml.safe_load((root / path).read_text(encoding="utf-8"))


def canonical(data):
    return json.dumps(data, sort_keys=True, allow_nan=False, separators=(",", ":")).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def phase_cases(root):
    dataset = discover_dataset_root(root / "dataset")
    inventory = load_json(root / "results/manifests/dataset_inventory.json")["instances"]
    disjoint = {}
    counts = Counter()
    development = set(inputs(root))
    seen = set()
    for item in inventory:
        parent, variant = item["instance_key"], item["variant"]
        if (parent, variant) in seen or variant not in ("A", "B"):
            raise ValueError("Duplicate parent variant or invalid variant")
        seen.add((parent, variant))
        split = "development" if (parent, variant) in development else "holdout"
        if item["partition"] != split or item["parent_key"] != parent:
            raise ValueError("Dataset split mismatch")
        disjoint.setdefault(parent, set()).add((variant, split))
        counts[item["family"], split] += 1
    if len(seen) != 120 or len(disjoint) != 60 or any(
        siblings not in ({("A", "development"), ("B", "development")}, {("A", "holdout"), ("B", "holdout")})
        for siblings in disjoint.values()
    ) or sorted(counts.values()) != [4] * 6 + [16] * 6:
        raise ValueError("Frozen split is not 12+48 disjoint paired parents")
    return dataset, sorted(inventory, key=lambda row: (row["instance_key"], row["variant"]))


def dataset_hashes(root):
    dataset, cases = phase_cases(root)
    hashes = {}
    for row in cases:
        variant_dir = dataset / ("variant_A_original_TW" if row["variant"] == "A" else "variant_B_relaxed_TW")
        stem = row["instance_key"]
        for name, column in ((f"{stem}.txt", "instance_sha256"), (f"{stem}_stations.csv", "stations_sha256")):
            path = variant_dir / name
            if not path.is_file():
                path = variant_dir / name.lower()
            actual = sha256_file(path)
            if actual != row[column]:
                raise ValueError(f"Dataset bytes differ from historical inventory: {path.name}")
            hashes[path.relative_to(root).as_posix()] = actual
    for name in ("ev_specs.json", "params.json", "README.md", "code/evrptw_solvers.py"):
        path = dataset / name
        hashes[path.relative_to(root).as_posix()] = sha256_file(path)
    return hashes


def committed_files(root, revision, cfg_path):
    return [
        name for name in git(root, "ls-tree", "-r", "--name-only", revision).decode().splitlines()
        if name.startswith(("src/star_evrp/", "tests/"))
        or name in {cfg_path, "configs/experiment_splits.yaml", "results/manifests/dataset_inventory.json",
                    "scripts/phase3.py", "docs/PHASE3_PRE_REGISTERED_ANALYSIS.md",
                    "docs/PHASE3_PREFLIGHT.md", "prompts/PROMPT_03_POST_PHASE25_FINAL.md",
                    "pyproject.toml", "requirements.txt"}
    ]


def verify_committed(root, revision, names):
    hashes = {}
    for name in names:
        blob = git(root, "show", f"{revision}:{name}")
        working = (root / name).read_bytes()
        if blob != working and blob != working.replace(b"\r\n", b"\n"):
            raise ValueError(f"Frozen working bytes differ from tagged Git blob: {name}")
        hashes[name] = digest(blob)
    return hashes


def versions():
    return {name: importlib.metadata.version(name) for name in DEPENDENCIES}


def preflight(root, cfg_path, out):
    cfg = config(root, cfg_path)
    historical = root / "results/phase25"
    manifest = load_json(historical / "manifest.json")
    recorded = load_json(historical / "analysis_manifest.json")
    paths = {**manifest["file_sha256"], **recorded["analysis_and_replay_source_sha256"],
             **{(Path("results/phase25") / name).as_posix(): value
                for name, value in recorded["raw_file_sha256"].items()}}
    for name, expected in paths.items():
        blob = git(root, "show", f'{cfg["phase25_release"]}:{name}')
        if expected not in (digest(blob), digest(blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))):
            raise ValueError(f"Phase 2.5 release mismatch: {name}")
        if name.startswith("src/"):
            verify_committed(root, cfg["phase25_release"], [name])
    if load_json(historical / "replay.json")["validated_records"] != 15960:
        raise ValueError("Historical validation replay incomplete")
    if load_json(historical / "search_replay.json")["search_records"] != 11970:
        raise ValueError("Historical search replay incomplete")
    all_hashes = dataset_hashes(root)
    from star_evrp.phase3_analysis import png_info

    figures = [png_info(path) for path in sorted((historical / "figures").glob("*.png"))]
    if len(figures) != 10:
        raise ValueError("Missing Phase 2.5 figures")
    child = subprocess.run(["python", "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"], cwd=root,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(child.stdout, flush=True)
    if child.returncode:
        raise RuntimeError(child.stderr or "Preflight correctness tests failed")
    tests = int(re.search(r"(\d+) passed", child.stdout)[1])
    smoke(root, cfg)
    result = {
        "status": "pass", "head": git(root, "rev-parse", "HEAD").decode().strip(),
        "phase25_release": cfg["phase25_release"], "verified_phase25_files": len(paths),
        "phase25_replayed_plans": 15960, "phase25_replayed_searches": 11970,
        "phase25_reconciled": phase25_numbers(historical), "tests_passed": tests, "tests_output": child.stdout,
        "source_blobs": verify_committed(root, "HEAD", committed_files(root, "HEAD", cfg_path)),
        "dataset_files_verified": len(all_hashes), "split": {"development": 24, "holdout": 96, "parents": 48},
        "phase25_png": figures, "holdout_outcomes_accessed": False,
    }
    path = out / "manifests/preflight.json"
    if path.exists() and load_json(path)["head"] != result["head"]:
        raise ValueError("Preflight record belongs to another revision")
    save_json(path, result)
    return result


def phase25_numbers(folder):
    rows = []
    for path in sorted((folder / "raw/candidates64").glob("*.json")):
        data = load_json(path)
        if digest(json.dumps(data["rows"], sort_keys=True, allow_nan=False).encode()) != data["rows_sha256"]:
            raise ValueError("Phase 2.5 batch digest mismatch")
        rows.extend(data["rows"])
    result = {}
    for method in ("STaR", "B3", "B4"):
        selected = [row for row in rows if row["method"] == method]
        keys = {(row["parent"], row["variant"], row["route_id"]) for row in selected}
        if len(selected) != 570 or len(keys) != 570:
            raise ValueError("Phase 2.5 route coverage mismatch")
        if any(row["budget"]["candidates_evaluated"] > 64 for row in selected):
            raise ValueError("Phase 2.5 candidate cap mismatch")
        result[method] = {
            "n": len(selected),
            "R": float(np.mean([row["validation"]["reliability"] for row in selected])),
            "completion": float(np.mean([row["validation"]["mean_completion"] for row in selected])),
            "attained": sum(row["validation"]["attained"] for row in selected),
            "scenarios": float(np.mean([row["budget"]["scenarios_evaluated"] for row in selected])),
            "wall": float(np.mean([row["budget"]["elapsed_seconds"] for row in selected])),
        }
    return result


def freeze(root, cfg_path, out):
    cfg = config(root, cfg_path)
    proof = load_json(out / "manifests/preflight.json")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if proof["status"] != "pass" or proof["head"] != head or git(root, "rev-list", "-n1", cfg["tag"]).decode().strip() != head:
        raise ValueError("Freeze requires passed preflight on the tagged executable commit")
    if git(root, "status", "--porcelain", "--untracked-files=no").strip():
        raise ValueError("Commit the complete executable snapshot before freezing")
    blob_hashes = verify_committed(root, head, committed_files(root, head, cfg_path))
    if blob_hashes != proof["source_blobs"]:
        raise ValueError("Frozen executable does not match the preflight")
    _, cases = phase_cases(root)
    manifest = {
        "schema": SCHEMA, "commit": head, "tag": cfg["tag"], "config_path": cfg_path,
        "config": cfg, "git_blob_sha256": blob_hashes, "dataset_sha256": dataset_hashes(root),
        "holdout": [row for row in cases if row["partition"] == "holdout"],
        "preflight_sha256": sha256_file(out / "manifests/preflight.json"),
        "dependencies": versions(), "python": platform.python_version(),
        "platform": platform.platform(), "processor": platform.processor(), "logical_cpus": os.cpu_count(),
        "thread_settings": {name: os.environ.get(name) for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
        "commands": [f"python -B scripts/phase3.py {action}" for action in (
            "preflight", "freeze", "smoke", "run", "replay", "analyze", "audit", "report")],
    }
    path = out / "manifests/freeze.json"
    if path.exists():
        raise FileExistsError("Freeze is immutable; do not overwrite it")
    save_json(path, manifest)
    return manifest


def verified_freeze(root, out):
    manifest = load_json(out / "manifests/freeze.json")
    commit = git(root, "rev-list", "-n1", manifest["tag"]).decode().strip()
    if commit != manifest["commit"] or manifest["schema"] != SCHEMA:
        raise ValueError("Frozen tag or schema mismatch")
    if verify_committed(root, commit, manifest["git_blob_sha256"]) != manifest["git_blob_sha256"]:
        raise ValueError("Frozen source hashes changed")
    if dataset_hashes(root) != manifest["dataset_sha256"] or versions() != manifest["dependencies"]:
        raise ValueError("Frozen dataset or dependencies changed")
    if sha256_file(out / "manifests/preflight.json") != manifest["preflight_sha256"]:
        raise ValueError("Preflight changed after freeze")
    if config(root, manifest["config_path"]) != manifest["config"]:
        raise ValueError("Frozen config mismatch")
    if platform.python_version() != manifest["python"] or any(
        os.environ.get(name) != value for name, value in manifest["thread_settings"].items()
    ):
        raise ValueError("Use the frozen Python version and thread settings")
    if not (out / "manifests/smoke.json").exists():
        verify_smoke = False
    else:
        verify_smoke = load_json(out / "manifests/smoke.json")["freeze"] == digest(canonical(manifest))
    return manifest, verify_smoke


def write_bundle(path, context, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical({"context": context, "digest": digest(canonical(rows)), "rows": rows})
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle, gzip.GzipFile(fileobj=handle, filename="", mtime=0, compresslevel=3) as archive:
            archive.write(payload)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return digest(canonical(rows))


def read_bundle(path, context=None):
    with gzip.open(path, "rb") as handle:
        payload = json.load(handle)
    if context is not None and payload["context"] != context:
        raise ValueError(f"Stale bundle context: {path}")
    if digest(canonical(payload["rows"])) != payload["digest"]:
        raise ValueError(f"Corrupt bundle: {path}")
    return payload


def physics_for(cfg):
    return SimulatorConfig(cfg["battery_capacity"], cfg["energy_consumption_rate"], cfg["station_windows"])


def validation(instance, selected, trace, physics, cfg, *, stress=None, scalar=False):
    timing = RouteTiming.from_trace(instance, trace, physics)
    seed = cfg["validation_seed"] if stress is None else cfg["stress_seed"]
    count = cfg["validation_samples"]
    slots = len(timing.mus)
    tape = generate_z_tape(seed, instance.parent_key, instance.variant, selected.route_id, "holdout", count, slots)
    if stress is not None and slots:
        rho = stress["rho"]
        common = generate_z_tape(seed + 1, instance.parent_key, instance.variant, selected.route_id,
                                 "holdout", count, 1) if rho else 0.0
        shocks = np.sqrt(1 - rho) * tape + np.sqrt(rho) * common
        waits = stress["scale"] * np.exp(timing.mus + timing.sigmas * stress["sigma"] * shocks)
    else:
        waits = timing.waits(tape)
    clock = np.zeros(count)
    customer_late, depot_late, station_late = [np.zeros(count, dtype=bool) for _ in range(3)]
    tardiness = np.zeros(count)
    max_tardy = np.zeros(count)
    customer_count = 0
    for step, stop in zip(timing.steps, trace.stops[1:]):
        clock += step.travel
        np.maximum(clock, step.ready, out=clock)
        if step.slot is not None:
            clock += waits[:, step.slot]
        if stop.node_type == NodeType.CUSTOMER:
            late = np.maximum(0, clock - step.start_deadline)
            customer_late |= late > NUM_TOL
            tardiness += late
            np.maximum(max_tardy, late, out=max_tardy)
            customer_count += 1
        clock += step.duration
        if stop.node_type == NodeType.DEPOT:
            depot_late |= clock > step.end_deadline + NUM_TOL
        elif step.slot is not None:
            station_late |= clock > step.end_deadline + NUM_TOL
    success = ~(customer_late | depot_late | station_late)
    if scalar:
        for index in np.linspace(0, count - 1, cfg["validation_scalar_checks"], dtype=int):
            outcome = evaluate_route_with_waits(
                instance, selected, waits[index], Q=physics.battery_capacity, h=physics.energy_consumption_rate,
                enforce_station_time_windows=physics.enforce_station_time_windows,
            )
            if (not outcome.energy_valid or outcome.success != success[index] or
                outcome.any_late_customer != customer_late[index] or outcome.late_depot != depot_late[index] or
                not np.isclose(outcome.completion, clock[index], rtol=0, atol=1e-8)):
                raise ValueError("Scalar reference and independent validation replay disagree")
    wins = int(success.sum())
    low, high = wilson_ci(wins, count)
    lower = wilson_lower(wins, count)
    return {
        "n": count, "successes": wins, "reliability": wins / count, "wilson95_lower_one_sided": lower,
        "wilson95_two_sided": [low, high], "attained": lower >= cfg["target"],
        "completion": float(clock.mean()), "completion_quantiles": np.quantile(clock, np.linspace(0, 1, 21)).tolist(),
        "mean_customer_tardiness": float(tardiness.mean() / max(customer_count, 1)),
        "max_customer_tardiness": float(max_tardy.max()), "late_customer": int(customer_late.sum()),
        "late_depot": int(depot_late.sum()), "late_both": int((depot_late & customer_late).sum()),
        "late_station": int(station_late.sum()),
        "tape_seed": tape_rng_seed(seed, instance.parent_key, instance.variant, selected.route_id, "holdout"),
    }


def plan_details(instance, source, route, trace, timing):
    stations, events = [], []
    served = 0
    for node in trace.stops:
        if node.node_type == NodeType.CUSTOMER:
            served += 1
        attr = instance.station_attributes.get(node.node_id)
        if attr is not None:
            stations.append([served, node.node_id])
        events.append([
            node.node_id, node.node_type.value, node.service_start_time, node.departure_time,
            node.energy_charged, instance.node(node.node_id).due_date,
        ])
    return {
        "fingerprint": ChargePlan.from_route(instance, route).fingerprint(),
        "customer_sha256": digest(canonical(customer_node_ids(instance, source))),
        "stops": [asdict(stop) for stop in route.stops], "station_positions": stations,
        "events": events, "energy_added": sum(event[4] for event in events), "distance": trace.total_distance,
        "zero_wait_completion": trace.end_clock, "screen_upper_bound": float(timing.marginal_bounds(trace).min(initial=1.0)),
    }


def smoke(root, cfg):
    parent, variant = "C1_10_10", "A"
    info = inputs(root)[(parent, variant)]
    instance = load_instance(root, parent, variant)
    if (instance.instance_file_sha256, instance.stations_file_sha256) != (info["instance_sha256"], info["stations_sha256"]):
        raise ValueError("Smoke inputs changed")
    solution = load_baseline_solution(root / f"results/baselines/{parent}__{variant}.json")
    route = next(route for route in solution.routes if any(stop.node_id in instance.station_attributes for stop in route.stops))
    phys = physics_for(cfg)
    fixture = {**cfg, "validation_samples": 128}
    for method in cfg["profiles"][cfg["primary"]]["methods"]:
        result = optimize(instance, phys, route, method, BudgetConfig(max_candidate_evals=8),
                          seed=cfg["profiles"][cfg["primary"]]["seed"], samples=128, target=cfg["target"])
        trace = validate_repair(instance, route, result.route, phys)
        first = validation(instance, result.route, trace, phys, fixture, scalar=True)
        if validation(instance, result.route, trace, phys, fixture, scalar=True) != first:
            raise ValueError("Smoke replay mismatch")
    return {"fixture": f"{parent}/{variant}", "methods": 7, "validation_samples": 128}


def _route(entry):
    return Route(entry["route_id"], entry.get("customer_indices"), [RouteStop(**stop) for stop in entry["stops"]])


def _case(root, out, token, cfg, item, *, replay=False):
    parent, variant = item["instance_key"], item["variant"]
    instance = load_instance(root, parent, variant)
    phys = physics_for(cfg)
    if (instance.instance_file_sha256, instance.stations_file_sha256) != (
        item["instance_sha256"], item["stations_sha256"],
    ) or validate_instance(instance):
        raise ValueError(f"Invalid frozen input {parent}/{variant}")
    stem = f"{parent}__{variant}"
    context = {"schema": SCHEMA, "freeze": token, "case": stem,
               "instance_sha256": item["instance_sha256"], "stations_sha256": item["stations_sha256"]}
    con_path = out / "raw/con" / f"{stem}.json.gz"
    if con_path.exists() or replay:
        data = read_bundle(con_path, context)["rows"]
        solution = Solution(parent, variant, "CON", phys.battery_capacity, phys.energy_consumption_rate,
                            [_route(entry) for entry in data["routes"]], total_distance=data["distance"])
    else:
        solution = generate_baseline(instance, phys.battery_capacity, phys.energy_consumption_rate,
                                     method="CON", project_root=root)
        data = {"routes": [asdict(route) for route in solution.routes], "distance": solution.total_distance,
                "runtime": solution.metadata["runtime_seconds"]}
        if not solution.feasible:
            raise ValueError(f"Infeasible deposited CON: {stem}")
        write_bundle(con_path, context, data)
    valid = validate_solution(instance, solution, config=phys)
    if not valid.feasible or len({route.route_id for route in solution.routes}) != len(solution.routes):
        raise ValueError(f"CON rejected by validator: {stem}")
    exposed = sorted((route for route in solution.routes if any(
        stop.node_id in instance.station_attributes for stop in route.stops
    )), key=lambda route: route.route_id)
    n_replayed = 0
    for profile, definition in cfg["profiles"].items():
        for batch_start in range(0, len(exposed), cfg["batch_routes"]):
            sources = exposed[batch_start:batch_start + cfg["batch_routes"]]
            methods = definition["methods"]
            expected = [[route.route_id, method] for route in sources for method in methods]
            part = {**context, "profile": profile, "keys": expected, "con_digest": digest(canonical(data))}
            name = f"{stem}__{batch_start:04d}.json.gz"
            metrics_path = out / "raw" / profile / name
            plans_path = out / "plans" / profile / name
            if metrics_path.exists() or replay:
                metrics = read_bundle(metrics_path, part)
                plans = read_bundle(plans_path, part)
                for payload in (metrics, plans):
                    if [[row["route_id"], row["method"]] for row in payload["rows"]] != expected:
                        raise ValueError("Missing, duplicated or misordered plan")
                source_by_id = {route.route_id: route for route in sources}
                for raw, saved in zip(metrics["rows"], plans["rows"]):
                    if raw["plan_sha256"] != digest(canonical(saved)):
                        raise ValueError("Metrics and saved plan are not linked")
                    if not replay:
                        continue
                    source = source_by_id[raw["route_id"]]
                    selected = _route(saved)
                    ref = validate_repair(instance, source, selected, phys)
                    if (plan_details(instance, source, selected, ref, RouteTiming.from_trace(instance, ref, phys))
                        != {key: saved[key] for key in saved if key not in ("route_id", "method")}):
                        raise ValueError("Plan detail replay mismatch")
                    if validation(instance, selected, ref, phys, cfg, scalar=True) != raw["validation"]:
                        raise ValueError("Holdout validation replay mismatch")
                    expected_stress = set(cfg["stress"]) if (
                        profile == cfg["primary"] and raw["method"] in cfg["stress_methods"]
                    ) else set()
                    if set(raw["stress"]) != expected_stress:
                        raise ValueError("Missing or extra stress record")
                    for key, stress in raw["stress"].items():
                        if validation(instance, selected, ref, phys, cfg, stress=cfg["stress"][key],
                                      scalar=True) != stress:
                            raise ValueError("Stress replay mismatch")
                    if raw["method"] in ("B0", "B4"):
                        if [stop.node_id for stop in source.stops] != [stop.node_id for stop in selected.stops]:
                            raise ValueError("Fixed station/control topology changed")
                    if raw["method"] == "B0" and source.stops != selected.stops:
                        raise ValueError("B0 altered its source plan")
                    limits = definition["limits"]
                    if (raw["work"]["candidates_evaluated"] > limits["max_candidate_evals"]
                        or raw["work"]["scenarios_evaluated"] > limits["max_scenario_evals"]):
                        raise ValueError("Hard count budget violated")
                    n_replayed += 1
                continue
            results, plans = [], []
            for source in sources:
                for method in methods:
                    cpu_start = process_time()
                    search = optimize(instance, phys, source, method, BudgetConfig(**definition["limits"]),
                                      seed=definition["seed"], samples=cfg["opt_samples"], target=cfg["target"],
                                      nearby=cfg["nearby_stations"])
                    cpu = process_time() - cpu_start
                    selected = search.route
                    validation_start = perf_counter()
                    trace = validate_repair(instance, source, selected, phys)
                    plan = {"route_id": source.route_id, "method": method, **plan_details(
                        instance, source, selected, trace, RouteTiming.from_trace(instance, trace, phys),
                    )}
                    final = validation(instance, selected, trace, phys, cfg)
                    stress = {}
                    if profile == cfg["primary"] and method in cfg["stress_methods"]:
                        stress = {key: validation(instance, selected, trace, phys, cfg, stress=model)
                                  for key, model in cfg["stress"].items()}
                    plans.append(plan)
                    results.append({
                        "route_id": source.route_id, "method": method, "plan_sha256": digest(canonical(plan)),
                        "work": search.budget, "cpu_seconds": cpu, "validation_seconds": perf_counter() - validation_start,
                        "validation": final, "stress": stress, "search_score": list(search.score),
                        "accepted_moves": search.moves, "time_to_opt_target": search.target_time,
                        "screen_rejections": search.screen_rejections, "prefix_rejections": search.prefix_rejections,
                        "rejected_reasons": {"fixed_plan_bound": search.screen_rejections,
                                             "fixed_tape_prefix": search.prefix_rejections},
                    })
            write_bundle(plans_path, part, plans)
            write_bundle(metrics_path, part, results)
    return {
        "parent": parent, "family": item["family"], "variant": variant, "case": stem, "routes": len(solution.routes),
        "exposed": len(exposed), "zero_charge": len(solution.routes) - len(exposed), "replayed": n_replayed,
        "con_runtime_seconds": data["runtime"], "eligible_route_ids": [route.route_id for route in exposed],
    }


def _case_worker(root, out, token, cfg, item, replay):
    try:
        return _case(root, out, token, cfg, item, replay=replay)
    except Exception as exc:
        return {"case": f'{item["instance_key"]}__{item["variant"]}', "error": f"{type(exc).__name__}: {exc}"}


def execute(root, out, *, replay=False):
    manifest, tested = verified_freeze(root, out)
    if not tested:
        raise ValueError("Post-freeze smoke check must pass first")
    cfg, token = manifest["config"], digest(canonical(manifest))
    if not replay and not (out / "manifests/started.json").exists():
        save_json(out / "manifests/started.json", {"freeze": token, "tag": manifest["tag"]})
    if load_json(out / "manifests/started.json")["freeze"] != token:
        raise ValueError("Execution already started under a different freeze")
    started = perf_counter()
    with ProcessPoolExecutor(max_workers=cfg["workers"]) as pool:
        jobs = [pool.submit(_case_worker, root, out, token, cfg, item, replay) for item in manifest["holdout"]]
        reports = []
        for index, job in enumerate(jobs, start=1):
            report = job.result()
            reports.append(report)
            print(f'{"Replay" if replay else "Run"}: {index}/{len(jobs)} cases, '
                  f'{sum("error" in item for item in reports)} errors', flush=True)
    result = {"freeze": token, "cases": reports, "elapsed_seconds": perf_counter() - started,
              "errors": [report for report in reports if "error" in report]}
    save_json(out / ("reports/replay.json" if replay else "reports/execution.json"), result)
    if result["errors"]:
        raise RuntimeError("Study incomplete; see persisted per-case error names and diagnostics")
    return result
