"""Publication-style figures (400 DPI PNG, colorblind palette)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

COLORBLIND = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "cyan": "#56B4E9",
    "yellow": "#F0E442",
    "black": "#000000",
}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 100,
            "savefig.dpi": 400,
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "legend.fontsize": 9,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _load_aggregate(results_dir: Path) -> list[dict[str, str]]:
    path = results_dir / "raw" / "aggregate_routes.csv"
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def fig01_charging_exposure_by_family_variant(rows: list[dict[str, str]], out: Path) -> None:
    apply_style()
    if not rows:
        _empty_figure("No route data", out)
        return
    families = sorted({r["family"] for r in rows})
    variants = sorted({r["variant"] for r in rows})
    fig, axes = plt.subplots(1, len(variants), figsize=(6 * len(variants), 4), squeeze=False)
    for vi, var in enumerate(variants):
        ax = axes[0, vi]
        x = np.arange(len(families))
        w = 0.25
        z0, z1, z2 = [], [], []
        for fam in families:
            sub = [r for r in rows if r["family"] == fam and r["variant"] == var]
            if not sub:
                z0.append(0); z1.append(0); z2.append(0)
                continue
            n = len(sub)
            z0.append(sum(int(float(r.get("num_charging_visits", 0))) == 0 for r in sub) / n)
            z1.append(sum(int(float(r.get("num_charging_visits", 0))) == 1 for r in sub) / n)
            z2.append(sum(int(float(r.get("num_charging_visits", 0))) >= 2 for r in sub) / n)
        ax.bar(x - w, z0, w, label="0 charges", color=COLORBLIND["blue"])
        ax.bar(x, z1, w, label="1 charge", color=COLORBLIND["orange"])
        ax.bar(x + w, z2, w, label="2+ charges", color=COLORBLIND["green"])
        ax.set_xticks(x)
        ax.set_xticklabels(families)
        ax.set_ylim(0, 1)
        ax.set_title(f"Variant {var}")
        ax.set_ylabel("Fraction of routes")
    axes[0, 0].legend(loc="upper right")
    fig.suptitle("Charging exposure by family")
    fig.tight_layout()
    fig.savefig(out, format="png")
    plt.close(fig)


def fig02_baseline_route_reliability(rows: list[dict[str, str]], out: Path) -> None:
    apply_style()
    if not rows:
        _empty_figure("No route data", out)
        return
    rels_all = sorted(float(r["reliability"]) for r in rows)
    exposed = [float(r["reliability"]) for r in rows if int(float(r.get("num_charging_visits", 0))) > 0]
    exposed.sort()
    fig, ax = plt.subplots(figsize=(6, 4))
    for data, label, color in (
        (rels_all, "All routes", COLORBLIND["blue"]),
        (exposed, "Charging-exposed", COLORBLIND["orange"]),
    ):
        if not data:
            continue
        y = np.arange(1, len(data) + 1) / len(data)
        ax.step(data, y, where="post", label=label, color=color)
    ax.axvline(0.95, color=COLORBLIND["red"], linestyle="--", label="95% target")
    ax.set_xlabel("Route reliability")
    ax.set_ylabel("ECDF")
    ax.set_xlim(0, 1)
    ax.legend()
    ax.set_title("Baseline stochastic route reliability")
    fig.tight_layout()
    fig.savefig(out, format="png")
    plt.close(fig)


def fig03_slack_vs_reliability(rows: list[dict[str, str]], out: Path) -> None:
    apply_style()
    exposed = [
        r
        for r in rows
        if int(float(r.get("num_charging_visits", 0))) > 0 and r.get("min_customer_slack")
    ]
    if not exposed:
        _empty_figure("No charging-exposed routes", out)
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    for var, color in (("A", COLORBLIND["blue"]), ("B", COLORBLIND["orange"])):
        sub = [r for r in exposed if r["variant"] == var]
        if not sub:
            continue
        x = [float(r["min_customer_slack"]) for r in sub]
        y = [float(r["reliability"]) for r in sub]
        ax.scatter(x, y, alpha=0.6, label=f"Variant {var}", color=color, s=20)
    ax.axhline(0.95, color=COLORBLIND["red"], linestyle="--")
    ax.set_xlabel("Min deterministic customer TW slack")
    ax.set_ylabel("Route reliability")
    ax.legend()
    ax.set_title("Slack vs reliability (charging-exposed)")
    fig.tight_layout()
    fig.savefig(out, format="png")
    plt.close(fig)


def fig04_station_waiting_time_risk(rows: list[dict[str, str]], out: Path) -> None:
    apply_style()
    # Requires instance-level station params — use e_total_wait from routes as proxy if no station table
    waits = [float(r.get("e_total_wait", 0)) for r in rows if int(float(r.get("num_charging_visits", 0))) > 0]
    if not waits:
        _empty_figure("No charging exposure", out)
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(waits, bins=min(30, len(waits)), color=COLORBLIND["cyan"], edgecolor="white")
    ax.set_xlabel("Expected total charging wait (route level)")
    ax.set_ylabel("Count")
    ax.set_title("Station waiting-time risk (route aggregates)")
    fig.tight_layout()
    fig.savefig(out, format="png")
    plt.close(fig)


def fig05_failure_modes(rows: list[dict[str, str]], out: Path) -> None:
    apply_style()
    from collections import Counter

    modes = Counter(r.get("failure_mode", "unknown") for r in rows)
    if not modes:
        _empty_figure("No failure modes", out)
        return
    labels, vals = zip(*sorted(modes.items(), key=lambda t: -t[1]))
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = [COLORBLIND["blue"], COLORBLIND["orange"], COLORBLIND["green"], COLORBLIND["red"], COLORBLIND["purple"]]
    ax.barh(labels, vals, color=colors[: len(labels)])
    ax.set_xlabel("Route count")
    ax.set_title("Stochastic failure modes")
    fig.tight_layout()
    fig.savefig(out, format="png")
    plt.close(fig)


def fig06_repair_headroom(project_root: Path, out: Path) -> None:
    apply_style()
    from star_evrp.results_io import load_json

    raw = project_root / "results" / "raw"
    base_rel: list[float] = []
    best_rel: list[float] = []
    for path in sorted(raw.glob("*__repair_probe.json")):
        data = load_json(path)
        for c in data.get("candidates", []):
            if c.get("action") == "baseline" and c.get("reliability") is not None:
                rid = c["route_id"]
                alts = [
                    x
                    for x in data.get("candidates", [])
                    if x.get("route_id") == rid
                    and x.get("reliability") is not None
                    and x.get("action") != "baseline"
                ]
                if alts:
                    base_rel.append(float(c["reliability"]))
                    best_rel.append(max(float(x["reliability"]) for x in alts))
    if not base_rel:
        _empty_figure("No repair probe results", out)
        return
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(base_rel, best_rel, color=COLORBLIND["green"], alpha=0.7)
    lims = [0, 1]
    ax.plot(lims, lims, color=COLORBLIND["black"], linestyle=":")
    ax.axhline(0.95, color=COLORBLIND["red"], linestyle="--")
    ax.set_xlabel("Baseline reliability")
    ax.set_ylabel("Best probe alternative")
    ax.set_title("Repair headroom (exploratory probe)")
    fig.tight_layout()
    fig.savefig(out, format="png")
    plt.close(fig)


def _empty_figure(message: str, out: Path) -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="png")
    plt.close(fig)


def regenerate_all_figures(results_dir: Path | str, figures_dir: Path | str) -> list[Path]:
    results = Path(results_dir)
    figures = Path(figures_dir)
    figures.mkdir(parents=True, exist_ok=True)
    rows = _load_aggregate(results)
    project_root = results.parent if results.name == "results" else results

    specs = [
        ("fig01_charging_exposure_by_family_variant.png", lambda p: fig01_charging_exposure_by_family_variant(rows, p)),
        ("fig02_baseline_route_reliability.png", lambda p: fig02_baseline_route_reliability(rows, p)),
        ("fig03_slack_vs_reliability.png", lambda p: fig03_slack_vs_reliability(rows, p)),
        ("fig04_station_waiting_time_risk.png", lambda p: fig04_station_waiting_time_risk(rows, p)),
        ("fig05_failure_modes.png", lambda p: fig05_failure_modes(rows, p)),
        ("fig06_repair_headroom.png", lambda p: fig06_repair_headroom(project_root, p)),
    ]
    written: list[Path] = []
    for name, fn in specs:
        path = figures / name
        fn(path)
        written.append(path)
    return written