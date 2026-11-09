"""Offline tests for the Chapter 6 checker and council plan."""
from datetime import date
from itertools import product

import yaml

from chapters.ch06_high_risk import checker, councils, intake


def base(**kw):
    f = {k: False for k in checker.FACTS}
    f["ai_system"] = True
    f.update(kw)
    return f


def test_emotion_inference_is_prohibited_before_annex():
    f = base(infers_emotion=True, recruit_select=True)
    assert checker.classify(f).label == "prohibited"


def test_medical_or_safety_lifts_the_prohibition_only():
    f = base(infers_emotion=True, medical_or_safety=True)
    assert checker.classify(f).label == "not high-risk"


def test_ranking_is_high_risk_even_with_override():
    f = base(recruit_select=True, profiling=True,
             materially_influences=True)
    assert checker.classify(f).high_risk


def test_profiling_overrides_every_exemption():
    for ex in checker.EXEMPT:
        f = base(monitor_evaluate=True, profiling=True, **{ex: True})
        assert checker.classify(f).high_risk


def test_exemption_needs_no_material_influence():
    f = base(recruit_select=True, narrow_procedural=True)
    assert checker.classify(f).label.startswith("exempt")
    f["materially_influences"] = True
    assert checker.classify(f).high_risk


def test_not_ai_system_has_no_ai_act_duties():
    f = base(ai_system=False, task_allocation=True)
    r = checker.classify(f)
    assert r.label == "not an AI system"
    assert checker.obligations(r, "n/a",
                               checker.load()["obligations"]) == []


def test_monotone_in_annex_and_profiling():
    """Saying yes to an Annex trigger or to profiling never
    makes a result less strict."""
    order = intake.ORDER
    for bits in product([False, True], repeat=6):
        f = base(recruit_select=bits[0], monitor_evaluate=bits[1],
                 profiling=bits[2], preparatory=bits[3],
                 pattern_check=bits[4],
                 materially_influences=bits[5])
        r0 = order.index(checker.classify(f).label)
        for k in ("recruit_select", "profiling"):
            g = dict(f, **{k: True})
            assert order.index(checker.classify(g).label) <= r0


def test_article22_token_review_is_solely_automated():
    d = {"decision_about_person": True, "significant_effect": True,
         "meaningful_review": False}
    assert checker.article22(d) == "Art 22 applies"
    d["meaningful_review"] = True
    assert checker.article22(d).startswith("outside")


def test_inventory_results():
    got = {s["id"]: checker.classify(s["facts"]).label
           for s in checker.load()["systems"]}
    assert got["H8"] == got["A2"] == "prohibited"
    assert got["P1"] == "not an AI system"
    assert sum(v == "high-risk" for v in got.values()) == 6


def test_council_start_date_uses_longest_track():
    cfg = yaml.safe_load(open(
        "chapters/ch06_high_risk/councils.yaml"))
    s = {x["id"]: x for x in checker.load()["systems"]}["H3"]
    out = councils.plan(s, date(2027, 9, 6), cfg)
    assert out["lead_weeks"] == 16
    assert out["start"] == date(2027, 5, 17)
