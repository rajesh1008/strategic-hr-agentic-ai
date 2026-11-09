"""Offline tests for chapters/ch27_skills (no key, no network)."""
from chapters.ch27_skills import agreement, guard, mobility, perf
from chapters.ch27_skills.volunteers import (
    CATALOG, VOLUNTEERS, render)


def test_v2_reads_reports_only_without_times():
    p = VOLUNTEERS[0]
    t2, t1 = render(p, "v2"), render(p, "v1")
    assert "Teams channel" not in t2 and "Teams channel" in t1
    assert "2027" not in t2 and "2027" in t1


def test_volunteer_set_counts():
    assert len(VOLUNTEERS) == 24
    assert sum(len(p.facts) for p in VOLUNTEERS) == 24
    assert sum(len(p.found) for p in VOLUNTEERS) == 29
    assert sum(len(p.decoy) for p in VOLUNTEERS) == 20


def test_guard_refuses_and_passes():
    p = VOLUNTEERS[1]                      # care fact in R1
    allowed = [p.docs["R1"]["text"], p.docs["R2"]["text"]]
    ok = {"skill_id": "SK-06", "quote": "Signed the F-gas "
          "leak-check log for all eight split units as the "
          "certified person."}
    assert guard.check(ok, CATALOG, allowed) == "ok"
    bad = dict(ok, skill_id="SK-99")
    assert guard.check(bad, CATALOG, allowed) == "not_in_catalog"
    made = dict(ok, quote="Signed every F-gas log on site.")
    assert guard.check(made, CATALOG, allowed) == \
        "quote_not_in_source"
    care = dict(ok, quote="I will be out on Friday afternoon "
                "to take my father to his dialysis appointment.")
    assert guard.check(care, CATALOG, allowed) == "never_class"


def test_never_classes():
    assert guard.classes("after the Betriebsrat meeting") == {"REP"}
    assert not guard.classes("14 weekend work windows")


def test_agreement_counts():
    import yaml
    d = yaml.safe_load((agreement.HERE / "designs.yaml").read_text())
    kept = {k: sum(ok(v) for _, _, ok in agreement.CLAUSES)
            for k, v in d.items()}
    assert kept == {"v1": 0, "v2": 6, "v2.1": 8}


def test_mobility_every_vacancy_reaches_everyone():
    r = mobility.run()
    assert r["b"] == r["relevant"]
    assert len(r["a"]) < len(r["b"])


def test_pack_check_refuses_rating_and_made_up_quote():
    s = perf.STAFF[0]
    good = {"objectives": [{"objective": "O1", "evidence": [
        {"record": "O1", "quote": "Retrofit handed over "
         "October 18, 13 days early"}]}]}
    assert perf.pack_check(good, s) == []
    rated = {"objectives": [], "rating": 4}
    assert "rating_word" in perf.pack_check(rated, s)
    made = {"objectives": [{"objective": "O1", "evidence": [
        {"record": "O1", "quote": "Best engineer on the team"}]}]}
    assert perf.pack_check(made, s) == ["quote_not_in_O1"]


def test_bands_by_rule():
    assert [perf.band(s[0]) for s in perf.STAFF] == [
        "Exceeds", "Exceeds", "Meets", "Exceeds", "Meets",
        "Meets", "Partly meets", "Meets"]
