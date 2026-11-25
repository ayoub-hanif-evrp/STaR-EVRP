import pytest

from star_evrp.phase6_analysis import audit_certificate, contrast
from star_evrp.phase6_diagnostics import summarize_direction


def test_reliability_tie_certificate_requires_independent_replay():
    row = {"status":"target_certified","opt_successes":512,"attempts":[
        {"stage":"target_completion","fun":800.},
        {"stage":"target_reliability_tie","certified_min_successes":512}]}
    assert audit_certificate(row)=="target_completion_only"
    row["attempts"][1].update(replay_successes=512,replay_completion=800+1e-7)
    assert audit_certificate(row)=="target_certified"
    row["attempts"][1]["replay_completion"]=800+2e-7
    assert audit_certificate(row)=="target_completion_only"


def test_direction_signed_contributions_and_attainment_effect():
    result=summarize_direction([.5,0,-.1,0,.2],0)
    assert (result["gains"],result["ties"],result["losses"])==(2,2,1)
    assert result["gain_contribution"]+result["loss_contribution"]==pytest.approx(result["mean_signed"])
    effect=contrast({"reliability":.952,"attained":False,"completion":50.},
                    {"reliability":.955,"attained":True,"completion":60.})
    assert effect==pytest.approx({"R_pp":-.3,"attained_pp":-100,"completion":-10})
