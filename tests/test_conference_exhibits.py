"""Focused Prompt-09 publication package tests (snapshot-only)."""

from pathlib import Path

import pytest

from star_evrp.conference_data import DISPLAY, INPUTS, load_snapshot
from star_evrp.conference_exhibits import TABLE_STEMS, build
from star_evrp.conference_figures import PANEL_COUNTS, STEMS
from star_evrp.phase4_results import read_json
from star_evrp.phase6_archive import csv_rows

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "conference"


def test_snapshot_inputs_present_and_hashed():
    data = load_snapshot(ROOT, OUT)
    assert data["comparison"][0]["method"] == "CON"
    assert [round(r["reliability_pct"], 2) for r in data["comparison"]] == [80.97, 95.29, 95.21, 97.31]
    assert [r["attained"] for r in data["comparison"]] == [1686, 2052, 2183, 2211]
    assert data["exact_routewise_npp_equality"] is True
    assert [r["n"] for r in data["complexity"]] == [1587, 159, 575]
    assert [r["nonattained"] for r in data["complexity"]] == [4, 4, 102]


def test_four_figures_three_tables_panel_contract():
    assert list(STEMS) == [
        "Fig01_spatial_charging_repair",
        "Fig02_comparative_reliability",
        "Fig03_charging_complexity",
        "Fig04_progressive_evaluation",
    ]
    assert [PANEL_COUNTS[s] for s in STEMS] == [2, 2, 2, 1]
    for stem in STEMS:
        for ext in ("png", "pdf", "svg", "json"):
            assert (OUT / "figures" / f"{stem}.{ext}").is_file()
        meta = read_json(OUT / "figures" / f"{stem}.json")
        assert meta["panels"] == PANEL_COUNTS[stem]
    assert len(list((OUT / "figures").glob("Fig*.png"))) == 4
    for stem in TABLE_STEMS:
        for ext in ("csv", "tex", "md"):
            assert (OUT / "tables" / f"{stem}.{ext}").is_file()


def test_method_whitelist_in_exhibits():
    banned = ("FSPC", "SLS", "AS1", "FT-SAA", "Fig05", "Sup01", "Sup02", "star_framework")
    for path in list((OUT / "figures").glob("*")) + list((OUT / "tables").glob("*")):
        if path.suffix.lower() in {".png", ".pdf", ".svg"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in banned:
            assert token not in text, f"{token} in {path.name}"
    rows = csv_rows(OUT / "tables" / "Tab02_method_comparison.csv")
    assert [r["Method"] for r in rows] == ["CON", "MWR", "QBR", "STaR"]
    ab = csv_rows(OUT / "tables" / "Tab03_component_ablation.csv")
    assert len(ab) == 5


def test_fig01_route_and_npp_draws():
    selection = read_json(OUT / "data" / "inputs" / "fig01_route.json")
    chosen = selection["chosen"]
    assert (chosen["parent"], chosen["variant"], chosen["route"]) == ("C1_10_3", "A", 106)
    data = load_snapshot(ROOT, OUT)
    assert abs(data["npp"]["saved_draws"] - 5903.110728134425) < 1e-6
    assert abs(data["npp"]["reduction_pct"] - 31.18844768708989) < 1e-6
    assert data["example"]["metrics"][0]["successes"] == 3063
    assert data["example"]["metrics"][1]["successes"] == 10000


def test_archival_disclosure_present_but_not_as_figure():
    text = (OUT / "ARCHIVAL_EVIDENCE.md").read_text(encoding="utf-8")
    assert "STaR − FSPC" in text or "STaR-FSPC" in text or "FSPC" in text
    assert "SLS" in text
    assert not (OUT / "figures" / "Fig02_star_framework.png").exists()
    assert not (OUT / "supplementary").exists() or not any((OUT / "supplementary").glob("*"))


def test_missing_inputs_fail(tmp_path):
    empty = tmp_path / "empty_out"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path, empty)


def test_clean_rebuild_matches_hashes(tmp_path):
    out = tmp_path / "rebuild"
    build(ROOT, out, 178)
    for stem in STEMS:
        assert (out / "figures" / f"{stem}.png").stat().st_size > 1000
    assert [r["Method"] for r in csv_rows(out / "tables" / "Tab02_method_comparison.csv")] == list(DISPLAY)
