"""Offline tests for hrai.law and the Chapter 5 examples."""
from datetime import date

import pytest

from hrai import law
from chapters.ch05_jurisdiction_map import register as reg
from chapters.ch05_jurisdiction_map import horizon_drafter as hd

RULES = law.load_rules()
D = date(2027, 2, 15)


def ids(fs, outcome=None):
    return {f.rule_id for f in fs if outcome in (None, f.outcome)}


def test_every_rule_cites_evidence_and_is_unchecked():
    for r in RULES:
        assert r["evidence"], r["id"]
        assert all(e.startswith("R-") for e in r["evidence"])
        assert not r.get("checked"), "law stays VERIFY (Ch 5)"


def test_place_chain():
    assert law.place_chain("US-NYC") == ["US-NYC", "US-NY", "US"]
    assert law.place_chain("NL") == ["NL", "EU"]
    assert law.place_chain("UK") == ["UK"]


def test_solely_rules_drop_when_a_person_decides():
    solely = law.Facts("UK", "hire", ai="solely")
    person = law.Facts("UK", "hire", ai="assist")
    assert "UK-DUAA-22A" in ids(law.obligations(solely, D, RULES))
    assert "UK-DUAA-22A" not in ids(law.obligations(person, D, RULES))


def test_any_ai_rules_stay_when_a_person_decides():
    f = law.Facts("US-IL", "hire", ai="assist")
    assert "US-IL-HRA-AI" in ids(law.obligations(f, D, RULES))


def test_no_ai_means_no_ai_rule_but_statutes_remain():
    f = law.Facts("US-IL", "hire", ai="none")
    assert ids(law.obligations(f, D, RULES)) == {"US-FED-TITLE7"}


def test_size_threshold():
    small = law.Facts("CA-ON", "hire", ai="assist", employees=24)
    big = law.Facts("CA-ON", "hire", ai="assist", employees=25)
    assert "CA-ON-ESA-POSTING" not in ids(
        law.obligations(small, D, RULES))
    assert "CA-ON-ESA-POSTING" in ids(law.obligations(big, D, RULES))


def test_future_date_and_pause():
    f = law.Facts("NL", "hire", ai="assist")
    eu = [x for x in law.obligations(f, D, RULES)
          if x.rule_id == "EU-AIA-ANNEX3-4"][0]
    assert eu.when == "from 2027-12-02"
    co = [x for x in law.obligations(
        law.Facts("US-CO", "hire", ai="assist"), D, RULES)
        if x.rule_id == "US-CO-SB26-189"][0]
    assert co.outcome == "PAUSED"


def test_unchecked_place_is_a_gap_never_silence():
    f = law.Facts("AU-QLD", "hire", ai="assist")
    gaps = [x for x in law.obligations(f, D, RULES)
            if x.outcome == "GAP"]
    assert any(g.lane == "AU-QLD" for g in gaps)


def test_unclear_decision_and_eor():
    f = law.Facts("US-IL", "schedule", ai="solely",
                  subject="employee")
    assert "US-IL-HRA-AI" in ids(
        law.obligations(f, D, RULES), "UNCLEAR")
    e = law.Facts("ES", "hire", ai="substantial", via_eor=True)
    assert "EU-AIA-ANNEX3-4" in ids(
        law.obligations(e, D, RULES), "UNCLEAR")


def test_emotion_recognition_banned_in_eu_now():
    f = law.Facts("IE", "hire", ai="substantial",
                  features=frozenset({"emotion"}))
    hit = [x for x in law.obligations(f, D, RULES)
           if x.rule_id == "EU-AIA-ART5-EMOTION"][0]
    assert hit.duties == ["BANNED"] and hit.when == "in force"


def test_platform_rules_skip_employers():
    f = law.Facts("NL", "allocate", ai="solely")
    assert "EU-PWD" not in ids(law.obligations(f, D, RULES))


def test_unknown_duty_rejected(tmp_path):
    (tmp_path / "coverage.yaml").write_text("parents: {}\n")
    (tmp_path / "x.yaml").write_text(
        "- {id: X, lane: US, name: x, places: [US], decisions: [],"
        " trigger: any, status: in_force, duties: [MAGIC],"
        " evidence: [R-001]}\n")
    with pytest.raises(ValueError):
        law.load_rules(tmp_path)


def test_hartwell_register_counts():
    wf = reg.load()
    rows, qs = reg.register(wf, RULES, D)
    assert len(rows) == 16
    assert sum(1 for r in rows if r.control) == 9
    assert len(qs) == 2
    assert any(r.rule == "NL-WOR-27" for r in rows)


def test_horizon_sorted_and_windowed():
    rows = law.horizon(RULES, date(2026, 11, 9), date(2027, 12, 31))
    ds = [r["date"] for r in rows]
    assert ds == sorted(ds) and len(rows) == 11


def test_drafter_schema_check():
    good = {"status": "enacted", "trigger": "ai",
            "decisions": ["hire"], "duties": ["NOTICE"],
            "in_force": "2027-10-01"}
    assert hd.problems(good) == []
    bad = {**good, "duties": ["MAGIC"], "in_force": "soon"}
    assert set(hd.problems(bad)) == {"duties", "in_force"}
