"""Offline tests for Chapter 22 (no key, no network)."""
from datetime import date

from chapters.ch22_shadow_gates import crew, gates, release
from chapters.ch22_shadow_gates.workforce import _milestone


def test_release_fixes_hold():
    assert all(ok for *_, ok in release.unit_checks())


def test_milestone_is_a_benefits_rule_that_tracks_age():
    assert _milestone("US", 54.0, 12.0) == 1
    assert _milestone("US", 40.0, 20.0) == 0
    assert _milestone("DE", 58.5, 3.0) == 1


def test_gate_denies_missing_evidence():
    assert gates.check("signature", None) == [
        "no evidence in the pack"]
    assert gates.check("consent", {"status": "met",
                                   "lanes": {"DE": "unmet"}})


def test_gate_requires_every_item():
    pack = {"gate": "intent", "evidence": {
        "problem_statement": {"status": "met"}}}
    r = gates.review(pack)
    assert r["decision"] == "REFUSE"
    assert r["items"]["problem_statement"] == []


def test_crew_rules_check_the_last_day():
    t = {"X": {"certs": {"NFPA 70E": "2027-08-02"},
               "inductions": []}}
    o = {"start": "2027-08-02", "days": 2, "hours": 20,
         "needs": ["NFPA 70E"], "induction": False,
         "site": "s", "board": [{"id": "X", "booked": 40,
                                 "miles": 5}]}
    assert crew.rules(o, "X", t) == ["CERT"]
    o["days"] = 1
    assert crew.rules(o, "X", t) == []
    assert crew.rules(o, "none", t) == ["NONE"]
    assert crew.TODAY == date(2027, 7, 30)


def test_day_reconciles_with_payroll_queue(monkeypatch):
    lines = []

    class Out:
        final_text = "Noted."

    class Rec:
        def print(self, line=""):
            lines.append(line)

        def note(self, **k):
            pass

        def save(self):
            return "saved"
    monkeypatch.setattr(release, "run", lambda *a, **k: Out())
    monkeypatch.setattr(release, "RunRecorder",
                        lambda *a: Rec())
    release.day_main()
    assert "=== end of day" in lines
