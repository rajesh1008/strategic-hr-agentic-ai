"""Offline tests for Chapter 21 (no key, no network)."""
from chapters.ch21_fairness import fairness as fx
from chapters.ch21_fairness import counterfactual, fieldnote, selfid
from chapters.ch21_fairness.record import check


def test_selfid_is_reproducible():
    assert selfid.OUT.read_bytes() == selfid.make()


def test_wilson_bounds():
    lo, hi = fx.wilson(0, 10)
    assert lo == 0 and 0.2 < hi < 0.35
    lo, hi = fx.wilson(5, 10)
    assert lo < 0.5 < hi


def test_errors_counts_only_people_who_met_the_bar():
    rs = [{"g": "a", "m": True, "s": False},
          {"g": "a", "m": True, "s": True},
          {"g": "b", "m": True, "s": True},
          {"g": "b", "m": False, "s": False}]
    rows, missing = fx.errors(rs, lambda r: r["g"],
                              lambda r: r["m"], lambda r: r["s"])
    got = {e.group: (e.n, e.wrong) for e in rows}
    assert got == {"a": (2, 1), "b": (1, 0)} and missing == 0


def test_holm_is_stricter_than_raw():
    keep = fx.holm({"x": 0.01, "y": 0.04, "z": 0.30})
    assert keep == {"x": True, "y": False, "z": False}


def test_readable_never_uses_a_small_reference():
    rs = [{"g": "tiny", "s": True}] * 3 + \
         [{"g": "big", "s": i % 2 == 0} for i in range(40)]
    rows, _, small = fx.readable(rs, lambda r: r["g"],
                                 lambda r: r["s"])
    assert [r.group for r in rows] == ["big"]
    assert small == [("tiny", 3)]


def test_cell_rule():
    assert fx.cell(29, .5) == "too few"
    assert fx.cell(40, .1) == "too few expected"
    assert fx.cell(40, .2) == "READ"


def test_counterfactual_changes_one_line_only():
    items = counterfactual.pairs()
    by = {}
    for it in items:
        by.setdefault(it["candidate_id"], {})[it["variant"]] = it
    for cid, vs in by.items():
        base = vs["base"]["text"].splitlines()
        assert vs["retest"]["text"] == vs["base"]["text"]
        for v, it in vs.items():
            if v in ("base", "retest"):
                continue
            other = it["text"].splitlines()
            diff = len(set(other) ^ set(base))
            assert diff in (1, 2), (cid, v)


def test_letters_say_the_same_facts():
    ls = fieldnote.letters()
    assert len(ls) == 45
    for i in range(0, 45, 3):
        a, b, c = ls[i:i + 3]
        for x in (a, b, c):
            assert str(a["years"]) in x["text"]
            assert str(a["tickets"]) in x["text"]
            assert ("SQL" in x["text"]) == a["sql"]
            assert ("API" in x["text"]) == a["api"]


def test_record_checks_flag_a_vendor_summary():
    assert all(v != "ok" for v in check({"title": "x"}).values())
