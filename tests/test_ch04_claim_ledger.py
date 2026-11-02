"""Offline tests for the Chapter 4 examples (no model calls)."""
import yaml

from chapters.ch04_claim_ledger import business_case, claim_intake, deflection, rerun_claim
from hrai.ledger import Ledger, Status


def test_rerun_numbers_are_stable():
    apps = rerun_claim.DATA["applications"]
    assert round(rerun_claim.reduction(apps)) == 24
    assert round(rerun_claim.reduction(apps, vendor_rule=True)) == 58
    ir = rerun_claim.impact_ratio(apps)
    assert ir["40+"][2] < 0.8


def test_hartwell_ledger_statuses():
    led = rerun_claim.build_ledger()
    assert led["T-01"].effective_status() is Status.TESTED
    assert led["T-01"].board_number() is None
    assert led["T-02"].contested


def test_deflection_is_production_and_below_claim():
    c = deflection.build_claim()
    assert c.effective_status() is Status.PRODUCTION
    assert 25 < c.board_number() < 35 < c.value


def test_business_case_blocks_on_contested_fairness():
    case = yaml.safe_load((business_case.HERE / "cases/hartwell-screening.yaml").read_text())
    r = business_case.evaluate(case)
    assert r["blocked"] == ["T-02"]
    assert r["cols"]["base"] < r["cols"]["planning"] < r["cols"]["vendor"]


def test_ashby_case_counts_nothing_in_base():
    case = yaml.safe_load((business_case.HERE / "cases/ashby-lowe.yaml").read_text())
    r = business_case.evaluate(case)
    assert r["cols"]["base"] == 0 and r["cols"]["planning"] < 200


def test_intake_rules():
    led = Ledger("t")
    doc = "Recruiters spend 70% less time screening. RankRight gives you bias-free ranking."
    ok = {"statement": "Recruiters spend 70% less time screening.", "metric_id": "screening_time",
          "value": 70, "unit": "percent reduction", "suggested_status": "Measured in production"}
    assert "Claimed (model suggested Measured in production)" in claim_intake.admit(led, "Talentra", doc, ok, 1)
    assert led["TA-01"].effective_status() is Status.CLAIMED
    vague = dict(ok, statement="bias-free ranking", value=None)
    assert claim_intake.admit(led, "RankRight", doc, vague, 2).startswith("RESTATE")
    fake = dict(ok, statement="cuts cost by half")
    assert claim_intake.admit(led, "Talentra", doc, fake, 3).startswith("REFUSED")
