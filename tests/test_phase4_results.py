import csv
import gzip
import json
from pathlib import Path
from statistics import fmean

import pytest

from star_evrp.phase4_release import markdown, png_audit, tex_table
from star_evrp.phase4_results import (FAMILIES, audit, bootstrap, bundle, canonical, differences, indexed,
                                     plan_link, probability_to_pp, require_keys, sha, strata, wilson)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/phase4"


@pytest.fixture(scope="module")
def frozen_study():
    return audit(ROOT)


def test_parent_stratification_and_missing_sibling():
    samples = [{"parent_key": f"{family}_{index}", "family": family, "variant": variant}
               for family in FAMILIES for index in range(8) for variant in ("A","B")]
    blocks = strata(samples)
    assert len(blocks) == 48
    assert all(list(blocks.values()).count(family)==8 for family in FAMILIES)
    with pytest.raises(ValueError,match="parent block"):
        strata(samples[:-1])


def test_duplicate_and_missing_keys():
    key = ("c64","C1_10_2","A",3,"B4")
    rows = [{"key":key},{"key":("c64",*key[1:4],"STaR")}]
    assert len(indexed(rows,lambda item:item["key"]))==2
    with pytest.raises(ValueError,match="Duplicate"):
        indexed([*rows,rows[0]],lambda item:item["key"])
    with pytest.raises(ValueError,match="missing"):
        require_keys([key],[item["key"] for item in rows],"batch")
    with pytest.raises(ValueError,match="extra"):
        require_keys(["unknown"],["c64"],"profiles")


def test_bad_plan_hash_and_changed_b4_station_rejected():
    source = {"stops":[{"node_id":n} for n in (0,1,1001,2,0)]}
    plan = {**source,"method":"B4","customer_sha256":sha(canonical([1,2])),"station_positions":[[1,1001]]}
    with pytest.raises(ValueError,match="Wrong selected"):
        plan_link({"plan_sha256":"bad"}, plan, source)
    plan_link({"plan_sha256":sha(canonical(plan))},plan,source)
    new_plan = {**plan,"stops":[{"node_id":n} for n in (0,1,2,1001,0)],"station_positions":[[2,1001]]}
    with pytest.raises(ValueError,match="B4 changed"):
        plan_link({"plan_sha256":sha(canonical(new_plan))},new_plan,source)


def test_wilson_attainment_and_straddling_are_separate():
    assert 9500/10000>=.95
    assert wilson(9500,10000,one_sided=True)[0]<.95
    assert wilson(9540,10000,one_sided=True)[0]>=.95
    low,high=wilson(9540,10000,one_sided=False)
    assert low<=.95<=high
    assert wilson(0,10000,one_sided=True)[0]==0


def test_pair_keys_and_estimands():
    common={"parent":"parent-A","variant":"B","route":21}
    variant={"validation":{"successes":9449,"n":10000},**common}
    other={"validation":{"successes":9400,"n":10000},**common}
    assert differences([(variant,other)],"reliability")[0][1]==pytest.approx(.0049)
    with pytest.raises(ValueError,match="Unmatched"):
        differences([(variant,{**other,"route":22})],"reliability")
    observed=[("a",1.),("a",1.),("b",-1.),("c",.2)]
    refs={"c":"R2","b":"R1","a":"R1"}
    tested=bootstrap(observed,refs,seed=312406,replicates=1234)
    assert tested[0]==pytest.approx(.3)
    assert tested[3]==pytest.approx(.2/3)
    assert tested==bootstrap(observed,refs,seed=312406,replicates=1234)
    assert probability_to_pp(.01242029)==pytest.approx(1.242029)


def test_frozen_population_and_primary_effect(frozen_study):
    summary=frozen_study.summary
    total=summary["population"][-1]
    assert (total["all_routes"],total["exposed"],total["zero_charge"])==(6864,2321,4543)
    assert (total["below_target_B0"],total["B0_lower_bound_nonattainment"])==(628,635)
    assert len(frozen_study.rows)==len(frozen_study.plans)==37136
    main=[row for row in summary["paired"] if row["status"]=="confirmatory"]
    assert len(main)==1 and (main[0]["profile"], main[0]["competitor"],main[0]["metric"])==("c64","B4","reliability")
    assert main[0]["estimate"]==pytest.approx(.012420293,abs=1e-9)
    assert main[0]["lower95"]==pytest.approx(.0086,abs=.00006)
    assert main[0]["upper95"]==pytest.approx(.0165,abs=.00006)
    assert sum(row["contribution_to_overall_delta_R"] for row in summary["mechanism"])==pytest.approx(main[0]["estimate"])
    assert all(row["n"]==2321 for row in summary["overall"])
    assert sum(row["n"]-row["attained"] for row in summary["failures"])==110
    assert len(summary["station_tables"])==4


def test_tex_escaping():
    columns=["Entity","Percent"]
    rows=[["A_B","51%"],["R&D","-"]]
    tex=tex_table(columns,rows)
    assert "A\\_B & 51\\%" in tex and r"R\&D & -" in tex
    assert r"\begin{tabular}" in tex and r"\end{tabular}" in tex
    assert "| A_B | 51% |" in markdown(columns,rows)


def test_batch_context_and_byte_hash_must_agree():
    context = {"schema": 1, "profile": "c64"}
    rows = [{"method": "B4"}]
    data = gzip.compress(canonical({"context": context, "digest": sha(canonical(rows)), "rows": rows}))
    assert bundle(data, sha(data), context) == rows
    with pytest.raises(ValueError,match="byte hash"):
        bundle(data, "0"*64, context)
    with pytest.raises(ValueError,match="context"):
        bundle(data, sha(data), {"schema": 1, "profile": "unknown"})


def test_generated_plot_and_table_formats():
    source=OUTPUT/"data/exhibits.json"
    if not source.is_file():
        pytest.skip("Build Phase 4 exhibits to test the on-disk package")
    exhibits=json.loads(source.read_text(encoding="utf-8"))
    assert sum(item["kind"]=="figure" and item["folder"]=="main" for item in exhibits)>=7
    for item in exhibits:
        path=OUTPUT/item["filename"]
        if item["kind"]=="figure":
            meta=json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
            assert png_audit(path,meta)["dpi"]==400
            assert "placeholder" not in item["caption"].lower()
            if "reliability" in item["id"] and item["id"].startswith(("F01","F03")):
                assert "perce" in item["caption"]
        else:
            table=json.loads((OUTPUT/"data/table_rows"/f'{item["id"]}.json').read_text(encoding="utf-8"))
            with path.with_suffix(".csv").open(encoding="utf-8",newline="") as handle:
                assert list(csv.reader(handle))==[table["columns"],*table["rows"]]
            assert path.read_text(encoding="utf-8")==tex_table(table["columns"],table["rows"])
