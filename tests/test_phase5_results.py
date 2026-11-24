import csv
from collections import Counter
from pathlib import Path

import pytest

from star_evrp.phase4_results import file_sha, read_json
from star_evrp.phase5_analysis import effect, metric_summary, paired
from star_evrp.phase5_experiments import methods_for, settings

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/"results/phase5"


def test_empty_cells_and_profile_boundaries():
    empty=metric_summary([],pooled=False)
    assert empty["n"]==0 and empty["mean_R"] is None and empty["search_wall_ms"] is None
    _,freeze=settings(ROOT)
    assert not methods_for("development",{"partition":"holdout"},freeze["config"])
    assert len(methods_for("development",{"partition":"development"},freeze["config"]))==7
    assert len(methods_for("ablations",{"partition":"holdout"},freeze["config"]))==3


def test_pair_and_parent_weights():
    def records(successes):
        return [{"parent":name,"variant":variant,"route":0,"validation":{"successes":success,"n":10000}}
                for (name,variant),success in zip((("p1","A"),("p1","B"),("p2","A")),successes)]
    samples=paired(records([10000,10000,0]),records([0,0,10000]))
    means=effect(samples,"reliability",{"p1":"dev:C1","p2":"holdout:C1"})
    assert means["mean"]==pytest.approx(1/3) and means["parent_mean"]==0
    assert means["lo95"]==means["hi95"]==means["mean"]
    with pytest.raises(ValueError,match="paired route set"):
        paired(records([10000,10000,0]),records([0,0]))


def test_published_phase5_coverage():
    summary_path=RESULTS/"data/summary.json"
    if not summary_path.exists():
        pytest.skip("Build archived Phase 5 outputs for publication integration")
    summary=read_json(summary_path)
    assert summary["counts"]=={"archived_controls":16247,"new_controls":3990,"new_ablations":8673,"all":28910}
    assert len(summary["population"])==120
    assert len(summary["instance"])==1200 and set(Counter(row["instance"] for row in summary["instance"]).values())=={10}
    zero=[row for row in summary["instance"] if not row["n"]]
    assert zero and all(row["mean_R"] is None and row["lower_bound_attained"] is None for row in zero)
    primary=[row for row in summary["paired"] if row["status"]=="confirmatory"]
    assert len(primary)==1 and primary[0]["comparison"]=="FSPC" and primary[0]["cohort"]=="holdout"
    assert primary[0]["mean"]==pytest.approx(.012420293,abs=1e-9)
    assert all(row["search_wall_ms"] is None for row in summary["pool"] if row["cohort"]=="all120")
    for row in summary["work"]:
        if row["method"]=="STaR-NAS":
            assert row["screen_checks"]==row["analytical_rejections"]==0
        if row["method"]=="STaR-NPP":
            assert row["prefix_rejections"]==0


def test_exhibits_and_clean_labels():
    manifest=RESULTS/"data/exhibits.json"
    if not manifest.exists():
        pytest.skip("Build exhibits before validating staged files")
    exhibits=read_json(manifest)
    assert sum(row["filename"].startswith("figures/main/") for row in exhibits["figures"])==7
    assert sum(row["filename"].startswith("figures/supplementary/") for row in exhibits["figures"])==8
    for row in exhibits["figures"]:
        path=RESULTS/row["filename"]
        assert file_sha(path)==row["png_sha256"]
        assert row["dpi"]==400
    for row in exhibits["tables"]:
        path=RESULTS/row["filename"]
        with path.with_suffix(".csv").open(newline="",encoding="utf-8") as handle:
            vals=list(csv.reader(handle))
        assert vals and not any(cell in ("B0","B1","B2","B3","B4") for cells in vals for cell in cells)


def test_csv_fields_follow_headers_after_an_empty_cell():
    path=RESULTS/"data/instance_results.csv"
    if not path.exists():
        pytest.skip("Run the Phase 5 analysis for this integration check")
    with path.open(newline="",encoding="utf-8") as source:
        records=list(csv.DictReader(source))
    assert len(records)==1200
    for row in records:
        if int(row["n"])==0:
            assert row["mean_R"]==row["unique_trials"]=="NA"
        else:
            assert 0<=float(row["mean_R"])<=1
            assert 1<=float(row["unique_trials"])<=64
            assert 0<=float(row["lower_bound_attained"])<=int(row["n"])
