from collections import Counter
from pathlib import Path
from statistics import fmean

import pytest

from star_evrp.conference_audit import png_format, svg_format, verify_flow, verify_map
from star_evrp.conference_data import PRIMARY, near
from star_evrp.conference_exhibits import TABLE_STEMS, table_latex
from star_evrp.conference_figures import STEMS
from star_evrp.phase4_results import read_json
from star_evrp.phase6_archive import csv_rows

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"results/conference"


def test_signed_archived_success_counts_and_estimates():
    pairs=csv_rows(OUT/"data/Fig03_paired_routes.csv")
    summaries=csv_rows(OUT/"data/Fig03_contrast_summary.csv")
    for row in summaries:
        matched=[r for r in pairs if r["comparator"]==row["comparator"]]
        keys={(r["parent"],r["variant"],r["route"]) for r in matched}
        assert len(keys)==len(matched)==2321 and len({k[0] for k in keys})==48
        delta=[int(r["star_successes"])-int(r["control_successes"]) for r in matched]
        assert {r["scenarios"] for r in matched}=={"10000"}
        assert [sum(d>0 for d in delta),delta.count(0),sum(d<0 for d in delta)]==[
            int(row[name]) for name in ("higher","equal","lower")]
        assert float(row["mean_pp"])==pytest.approx(fmean(delta)/100,abs=1e-13)
    assert [float(summaries[0][k])/100 for k in ("mean_pp","lo95_pp","hi95_pp")]==pytest.approx(PRIMARY,abs=1e-14)


def test_source_visit_strata_and_signed_contributions():
    data=csv_rows(OUT/"data/Fig04_route_inputs.csv")
    summary=csv_rows(OUT/"data/Fig04_source_visit_bins.csv")
    for row in data:
        count=int(row["source_visits"])
        assert count>0 and row["bin"]==("3+" if count>=3 else str(count))
    for row in summary:
        relevant=[x for x in data if x["bin"]==row["bin"]]
        assert int(row["n"])==len(relevant)
        assert int(row["nonattained"])==sum(x["nonattained"]=="True" for x in relevant)
        assert float(row["contribution_pp"])==pytest.approx(sum(float(x["delta_pp"]) for x in relevant)/len(data))
    assert sum(int(r["nonattained"]) for r in summary)==110


def test_spatial_selection_and_frozen_diagram():
    detail=verify_map(ROOT,OUT)
    chosen=detail["chosen"]
    source=csv_rows(ROOT/"results/phase6/data/route_features.csv")
    eligible=[r for r in source if r["partition"]=="holdout" and r["topology_changed"]=="True"
              and r["CON_attained"]=="False" and r["STaR_attained"]=="True"
              and int(r["STaR_successes"])>int(r["CON_successes"])]
    assert len(eligible)==int(read_json(OUT/"data/Fig01_route_selection.json")["eligible_tier_counts"]["1"])
    expected=min((int(r["customers"]),r["parent"],r["variant"],int(r["route"])) for r in eligible)
    assert expected==(chosen["customers"],chosen["parent"],chosen["variant"],chosen["route"])
    assert len(verify_flow(ROOT,OUT))==7


def test_timing_panel_paired_population_and_guard_notes():
    panel=csv_rows(OUT/"data/Fig05_route_aggregates.csv")
    counts=Counter((r["guard_ms"],r["method"]) for r in panel)
    assert len(counts)==6 and set(counts.values())=={118}
    assert len({(r["partition"],r["parent"],r["variant"],r["route"]) for r in panel})==118
    for row in csv_rows(OUT/"data/Fig05_paired_intervals.csv"):
        if row["metric"]=="R_pp":
            assert float(row["lo95"])<0<float(row["hi95"]) and int(row["n"])==118
    values={r["method"]:float(r["draws"]) for r in csv_rows(OUT/"data/Fig05_guard_summary.csv") if r["guard_ms"]=="50"}
    assert f'{100*(1-values["STaR"]/values["SLS"]):.2f}' in (OUT/"CLAIMS_AND_LIMITATIONS.md").read_text(encoding="utf-8")


def test_tables_exact_csv_and_loss_convention():
    for stem in TABLE_STEMS:
        info=read_json(OUT/"data"/f"{stem}_display.json")
        assert (OUT/"tables"/f"{stem}.tex").read_text(encoding="utf-8")==table_latex(stem,info["headers"],info["rendered"])
    result=csv_rows(OUT/"data/Tab03_exact.csv")
    origin=float(result[0]["reliability_pct"])
    assert [r["method"] for r in result]==["STaR","STaR-NPC","STaR-NSP","STaR-NAS","STaR-NPP"]
    for reduced in result[1:]:
        near(origin-float(reduced["reliability_pct"]),reduced["loss_pp"],"Full-minus-ablation")
    p=read_json(OUT/"audit/numerical.json")
    assert p["exact_routewise_npp_equality"] and float(result[-1]["loss_pp"])==0


def test_png_and_svg_metadata_on_all_five_figures():
    for stem in STEMS:
        where=OUT/"figures"/stem
        meta=read_json(where.with_suffix(".json"))
        assert meta["physical_mm"][0]==178 and meta["dpi"]==400
        assert png_format(where.with_suffix(".png"),meta["physical_mm"])[0]==2803
        assert svg_format(where.with_suffix(".svg"),meta["physical_mm"])["text_objects"]>0


def test_unit_conversion_and_tolerance_fail_on_error():
    with pytest.raises((AssertionError,ValueError),match="Percentage point scale"):
        near(PRIMARY[0]*100,PRIMARY[0],"Percentage point scale")
