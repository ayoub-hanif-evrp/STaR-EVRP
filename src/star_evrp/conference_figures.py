"""Prompt-09 conference figures: four stems, panels 2/2/2/1, no methodology artwork."""

from __future__ import annotations

from base64 import b64encode
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fontTools import subset
from fontTools.ttLib import TTFont
from matplotlib.lines import Line2D

from star_evrp.phase4_results import file_sha, require
from star_evrp.phase6_archive import write_bytes, write_json

TEAL, SLATE, AMBER, BLUE, PURPLE, NAVY = (
    "#0D9488", "#64748B", "#D97706", "#2563EB", "#7C3AED", "#1E293B",
)
GRID = "#E3E9EF"
COLORS = {"CON": SLATE, "MWR": BLUE, "QBR": PURPLE, "STaR": TEAL}
STEMS = (
    "Fig01_spatial_charging_repair",
    "Fig02_comparative_reliability",
    "Fig03_charging_complexity",
    "Fig04_progressive_evaluation",
)
PANEL_COUNTS = {
    "Fig01_spatial_charging_repair": 2,
    "Fig02_comparative_reliability": 2,
    "Fig03_charging_complexity": 2,
    "Fig04_progressive_evaluation": 1,
}
FORBIDDEN_SERIES = ("FSPC", "SLS", "AS1", "FT-SAA", "FT_SAA")
STYLE = {
    "font.family": "DejaVu Sans", "font.size": 8.2, "axes.labelcolor": NAVY, "text.color": NAVY,
    "axes.titlesize": 9.0, "axes.titleweight": "bold", "xtick.labelsize": 7.8, "ytick.labelsize": 7.8,
    "xtick.color": NAVY, "ytick.color": NAVY, "axes.edgecolor": SLATE, "axes.linewidth": 0.65,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.edgecolor": "white",
    "mathtext.fontset": "dejavusans", "pdf.fonttype": 42, "svg.fonttype": "none",
    "svg.hashsalt": "star-conference-p9",
}


def heading(ax, letter, text):
    ax.set_title(f"({letter})  {text}", loc="left", pad=6)


def new_figure(width_mm, height_mm):
    return plt.figure(figsize=(width_mm / 25.4, height_mm / 25.4))


def arrow_leg(ax, left, right, color):
    x, y = left["x"], left["y"]
    vx, vy = right["x"] - x, right["y"] - y
    if vx * vx + vy * vy < 900:
        return
    a = (x + vx * 0.52, y + vy * 0.52)
    b = (x + vx * 0.60, y + vy * 0.60)
    ax.annotate(
        "",
        xy=b,
        xytext=a,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=0.85, mutation_scale=7, shrinkA=0, shrinkB=0),
        zorder=4,
    )


def count_panels(fig):
    """Count Axes that are actual data panels (exclude colorbars/legends)."""
    return sum(1 for ax in fig.axes if ax.get_label() != "<colorbar>" and ax.has_data())


def svg_typography():
    assets = Path(matplotlib.get_data_path()) / "fonts/ttf"
    license_text = (assets / "LICENSE_DEJAVU").read_text(encoding="utf-8")
    rules = []
    characters = [*range(32, 0x180), *range(0x370, 0x400), *range(0x2000, 0x2070), 0x2192, 0x2212]
    for filename, weight in (("DejaVuSans.ttf", 400), ("DejaVuSans-Bold.ttf", 700)):
        with TTFont(assets / filename, recalcTimestamp=False) as font:
            options = subset.Options()
            options.drop_tables += ["FFTM"]
            cut = subset.Subsetter(options)
            cut.populate(unicodes=characters)
            cut.subset(font)
            content = BytesIO()
            font.save(content)
        encoded = b64encode(content.getvalue()).decode("ascii")
        rules.append(
            f"@font-face{{font-family:'DejaVu Sans';font-weight:{weight};"
            f"src:url(data:font/ttf;base64,{encoded}) format('truetype');}}"
        )
    style = (
        f"<desc>{escape(license_text)}</desc>"
        f'<defs><style type="text/css">{"".join(rules)}</style></defs>'
    )
    return style.encode("utf-8"), license_text.encode("utf-8")


def export(fig, out, stem, panels, captions, sources, plot_sha):
    folder = out / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    typography, _ = svg_typography()
    observed = count_panels(fig)
    require(observed == panels == PANEL_COUNTS[stem], f"Panel count for {stem}: got {observed}")
    dim = [round(v * 25.4, 4) for v in fig.get_size_inches()]
    for extension, meta in (
        ("png", {"Software": "STaR-EVRP / Matplotlib"}),
        ("pdf", {
            "Creator": "STaR-EVRP / Matplotlib",
            "Title": stem,
            "CreationDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "ModDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
        }),
        ("svg", {"Creator": "STaR-EVRP / Matplotlib", "Date": None, "Title": stem}),
    ):
        buffer = BytesIO()
        fig.savefig(buffer, format=extension, dpi=400, metadata=meta, facecolor="white")
        content = buffer.getvalue()
        if extension == "svg":
            content = content.replace(b"'DejaVu Sans';", b"'DejaVu Sans', sans-serif;")
            content = content.replace(b"</metadata>", b"</metadata>\n " + typography, 1)
            for token in FORBIDDEN_SERIES:
                require(token.encode() not in content, f"Forbidden series {token} in {stem}")
        write_bytes(folder / f"{stem}.{extension}", content)
    plt.close(fig)
    files = {ext: file_sha(folder / f"{stem}.{ext}") for ext in ("png", "pdf", "svg")}
    card = dict(
        stem=stem,
        physical_mm=dim,
        dpi=400,
        panels=panels,
        font="DejaVu Sans",
        formats_sha256=files,
        caption=captions[stem],
        source_sha256=sources,
        plot_source_sha256=plot_sha,
    )
    write_json(folder / f"{stem}.json", card)
    return card


def fig01(data, width):
    example = data["example"]
    fig = new_figure(width, 88)
    axes = fig.subplots(1, 2)
    # Extra top room for two-line headings; bottom room separates x labels from the legend.
    fig.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.30, wspace=0.20)
    maps = {k: [s for s in example["stops"] if s["plan"] == k] for k in ("CON", "STaR")}
    xy = [(s["x"], s["y"]) for s in example["stops"]]
    xmin, ymin = np.min(xy, axis=0) - 28
    xmax, ymax = np.max(xy, axis=0) + 28
    metrics = {m["method"]: m for m in example["metrics"]}
    charges = {(r["plan"], r["node"]): r for r in example["charges"]}
    # Station callouts kept inside the axes and clear of customers / route legs.
    station_offsets = {("CON", 1253): (22, -55), ("STaR", 1248): (22, 14)}
    customer_offsets = {
        ("CON", 1): (8, -16), ("CON", 2): (12, 6),
        ("STaR", 1): (8, -16), ("STaR", 2): (12, 6),
    }
    types = {"customer": ("o", BLUE), "station": ("s", AMBER), "depot": ("D", NAVY)}
    for ax, method, letter in ((axes[0], "CON", "a"), (axes[1], "STaR", "b")):
        path = maps[method]
        color = COLORS[method]
        used = {s["node"] for s in path}
        faint = [
            n for n in example["nodes"]
            if n["type"] == "station" and n["node"] not in used
            and xmin - 40 <= n["x"] <= xmax + 40 and ymin - 40 <= n["y"] <= ymax + 40
        ]
        if faint:
            ax.scatter(
                [n["x"] for n in faint], [n["y"] for n in faint],
                s=7, marker="s", c="#E8EDF2", edgecolors="none", zorder=1,
            )
        style = dict(lw=1.35, color=color, solid_capstyle="round", zorder=3)
        if method == "CON":
            ax.plot([s["x"] for s in path], [s["y"] for s in path], ls=(0, (3.2, 2.0)), **style)
        else:
            ax.plot([s["x"] for s in path], [s["y"] for s in path], ls="-", **style)
        for left, right in zip(path, path[1:]):
            arrow_leg(ax, left, right, color)
        for kind, (marker, face) in types.items():
            pts = [s for s in path if s["type"] == kind]
            ax.scatter(
                [s["x"] for s in pts], [s["y"] for s in pts],
                s={"customer": 28, "station": 42, "depot": 48}[kind],
                marker=marker, c=face, edgecolors="white", linewidths=0.5, zorder=5,
            )
        for stop in [s for s in path if s["type"] == "customer"]:
            dx, dy = customer_offsets.get((method, stop["customer_order"]), (6, 6))
            ax.annotate(
                str(stop["customer_order"]), (stop["x"], stop["y"]),
                xytext=(dx, dy), textcoords="offset points", fontsize=7.0, color=NAVY, zorder=8,
            )
        station = next(s for s in path if s["type"] == "station")
        charge = charges[method, station["node"]]["charged"]
        rel = 100 * metrics[method]["reliability"]
        # Reliability and station/charge live in the heading to avoid on-map collisions.
        ax.set_title(
            f"({letter})  {method}  ·  R = {rel:.2f}%\n"
            f"station {station['node']} ({charge:.2f})",
            loc="left", pad=6, fontsize=8.3, fontweight="bold", color=NAVY, linespacing=1.2,
        )
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x")
        if letter == "a":
            ax.set_ylabel("y")
        ax.grid(color=GRID, lw=0.4)
    handles = [
        Line2D([0], [0], color=SLATE, lw=1.4, ls=(0, (3, 2)), label="CON path"),
        Line2D([0], [0], color=TEAL, lw=1.4, label="STaR path"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=BLUE, markersize=5, label="Customer"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=AMBER, markersize=5, label="Station"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=NAVY, markersize=5, label="Depot"),
    ]
    fig.legend(
        handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=7.0,
        bbox_to_anchor=(0.5, 0.015), borderaxespad=0.0,
    )
    return fig, 2


def fig02(data, width):
    fig = new_figure(width, 82)
    # Give the forest panel more horizontal room for interval labels.
    grid = fig.add_gridspec(1, 2, left=0.09, right=0.99, top=0.88, bottom=0.22,
                            width_ratios=(1.0, 1.55), wspace=0.38)
    ax0 = fig.add_subplot(grid[0, 0])
    ax1 = fig.add_subplot(grid[0, 1])
    methods = data["comparison"]
    names = [r["method"] for r in methods]
    values = [r["reliability_pct"] for r in methods]
    colors = [COLORS[n] for n in names]
    bars = ax0.bar(names, values, color=colors, width=0.72, edgecolor="white", linewidth=0.4, zorder=2)
    ax0.axhline(95, color=SLATE, lw=0.95, ls=(0, (2.5, 1.8)), zorder=1)
    ax0.set_ylim(0, 115)
    ax0.set_ylabel("Mean route reliability (%)")
    for bar, value in zip(bars, values):
        lift = 2.4 if abs(value - 95.0) < 0.4 else 1.5
        ax0.text(
            bar.get_x() + bar.get_width() / 2, value + lift, f"{value:.2f}",
            ha="center", va="bottom", fontsize=7.2, color=NAVY,
        )
    heading(ax0, "a", "Mean reliability")
    # Target clarification below the bars, outside the bar bodies.
    ax0.text(
        0.5, -0.18,
        "Dashed line: 95% nominal individual target (not Wilson attainment)",
        transform=ax0.transAxes, ha="center", va="top", fontsize=6.2, color=SLATE,
        clip_on=False,
    )
    ax0.grid(axis="y", color=GRID, lw=0.5)

    paired = data["paired"]
    y = np.arange(len(paired))[::-1]
    for i, row in enumerate(paired):
        yi = y[i]
        ax1.errorbar(
            row["mean_pp"], yi,
            xerr=[[row["mean_pp"] - row["lo95_pp"]], [row["hi95_pp"] - row["mean_pp"]]],
            fmt="o", color=COLORS["STaR"], ecolor=SLATE, elinewidth=1.1,
            capsize=3.2, markersize=5.5, zorder=3,
        )
        label = f'{row["mean_pp"]:+.2f} [{row["lo95_pp"]:+.2f}, {row["hi95_pp"]:+.2f}]'
        if row["comparison"] == "CON":
            # Long CON interval: label to the left of the whisker so it cannot clip.
            ax1.annotate(
                label, xy=(row["lo95_pp"], yi),
                xytext=(-6, 0), textcoords="offset points",
                va="center", ha="right", fontsize=6.3, color=NAVY,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9),
            )
        else:
            ax1.annotate(
                label, xy=(row["hi95_pp"], yi),
                xytext=(6, 0), textcoords="offset points",
                va="center", ha="left", fontsize=6.3, color=NAVY,
            )
    ax1.axvline(0, color=SLATE, lw=0.85, ls=(0, (2, 2)), zorder=1)
    ax1.set_yticks(y)
    ax1.set_yticklabels([f"STaR − {r['comparison']}" for r in paired])
    ax1.set_xlabel("Reliability difference (pp)")
    short_right = max(r["hi95_pp"] for r in paired if r["comparison"] != "CON") + 8.0
    long_right = max(r["hi95_pp"] for r in paired) + 2.0
    ax1.set_xlim(-0.8, max(short_right, long_right))
    ax1.set_ylim(-0.45, len(paired) - 0.45)
    heading(ax1, "b", "Paired differences")
    ax1.grid(axis="x", color=GRID, lw=0.5)
    return fig, 2


def fig03(data, width):
    fig = new_figure(width, 76)
    ax0, ax1 = fig.subplots(1, 2)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.86, bottom=0.18, wspace=0.34)
    bins = data["complexity"]
    labels = [f"{r['bin']}\n(n={r['n']:,})" for r in bins]
    x = np.arange(len(bins))
    means = [r["mean_pp"] for r in bins]
    yerr = np.array([
        [r["mean_pp"] - r["lo95_pp"] for r in bins],
        [r["hi95_pp"] - r["mean_pp"] for r in bins],
    ])
    ax0.bar(x, means, color=TEAL, width=0.62, edgecolor="white", zorder=2)
    ax0.errorbar(x, means, yerr=yerr, fmt="none", ecolor=NAVY, elinewidth=1.0, capsize=3, zorder=3)
    ax0.set_xticks(x, labels)
    ax0.set_ylabel("STaR − CON reliability (pp)")
    ax0.set_xlabel("Original charging visits")
    ax0.axhline(0, color=SLATE, lw=0.7, ls=(0, (2, 2)))
    for i, r in enumerate(bins):
        ax0.text(i, r["hi95_pp"] + 0.9, f'{r["mean_pp"]:.2f}', ha="center", fontsize=7.0, color=NAVY)
    heading(ax0, "a", "Reliability gain by original visits")
    ax0.grid(axis="y", color=GRID, lw=0.5)

    rates = [r["nonattainment_pct"] for r in bins]
    ax1.bar(x, rates, color=AMBER, width=0.62, edgecolor="white", zorder=2, alpha=0.92)
    ax1.set_xticks(x, labels)
    ax1.set_ylabel("STaR Wilson nonattainment (%)")
    ax1.set_xlabel("Original charging visits")
    ax1.set_ylim(0, max(rates) * 1.28)
    for i, r in enumerate(bins):
        ax1.text(
            i, rates[i] + 0.4,
            f'{rates[i]:.2f}%\n({r["nonattained"]}/{r["n"]:,})',
            ha="center", fontsize=6.5, color=NAVY,
        )
    heading(ax1, "b", "Remaining nonattainment")
    ax1.grid(axis="y", color=GRID, lw=0.5)
    return fig, 2


def fig04(data, width):
    # Compact single-column width (~88 mm) inside the 178 mm canvas.
    fig = new_figure(width, 48)
    ax = fig.add_axes([0.28, 0.28, 0.42, 0.52])
    npp = data["npp"]
    labels = ["STaR", "STaR−NPP"]
    values = [npp["full_draws"], npp["npp_draws"]]
    colors = [TEAL, "#94A3B8"]
    y = np.arange(len(labels))[::-1]
    ax.barh(y, values, color=colors, height=0.52, edgecolor="white")
    ax.set_yticks(y, labels)
    ax.set_xlabel("Mean incremental search draws")
    ax.set_xlim(0, max(values) * 1.28)
    for yi, value in zip(y, values):
        ax.text(value + max(values) * 0.02, yi, f"{value:,.0f}", va="center", fontsize=7.6, color=NAVY)
    ax.set_title(
        f'Progressive prefix  ·  {npp["reduction_pct"]:.1f}% fewer draws\n'
        "identical recorded reliability / attainment / completion",
        loc="left", pad=8, fontsize=8.2,
    )
    ax.grid(axis="x", color=GRID, lw=0.5)
    return fig, 1


def draw(root, out, data, width, captions):
    require(width == 178, "Canonical width is 178 mm")
    _, license_text = svg_typography()
    write_bytes(out / "FONT_LICENSE.txt", license_text)
    plot_sha = file_sha(root / "src/star_evrp/conference_figures.py")
    with plt.rc_context(STYLE):
        builders = (fig01, fig02, fig03, fig04)
        metas = []
        for stem, builder in zip(STEMS, builders, strict=True):
            fig, panels = builder(data, width)
            meta = export(fig, out, stem, panels, captions, data["sources"], plot_sha)
            metas.append(meta)
    require([m["panels"] for m in metas] == [2, 2, 2, 1], "Panel contract")
    return metas
