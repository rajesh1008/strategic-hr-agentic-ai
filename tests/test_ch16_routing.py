"""Offline tests for Chapter 16 (no API calls)."""
from chapters.ch16_routing import make_data
from hrai import routing as rt

LINE = rt.RoutingLine(step="A04", version="t", model="m",
                      complete_at=0.9, review_at=0.7,
                      fail_closed=["not_meets", "rehire"],
                      review_if=["NEAR"])


def test_fail_closed_beats_any_score():
    c = rt.Case("x", "not_meets", 0.999)
    assert rt.route(c, LINE)[0] == "fail_closed"
    c = rt.Case("x", "meets", 0.999, flags=["rehire"])
    assert rt.route(c, LINE)[0] == "fail_closed"


def test_missing_or_bad_score_fails_closed():
    for s in (None, 1.5, -0.1):
        assert rt.route(rt.Case("x", "meets", s),
                        LINE)[0] == "fail_closed"


def test_lanes_by_score():
    assert rt.route(rt.Case("x", "meets", 0.95),
                    LINE)[0] == "complete"
    assert rt.route(rt.Case("x", "meets", 0.8),
                    LINE)[0] == "review"
    assert rt.route(rt.Case("x", "meets", 0.5),
                    LINE)[0] == "escalate"


def test_isotonic_is_monotone():
    pairs = [(0.9, False), (0.9, True), (0.8, True),
             (0.95, True), (0.95, True), (0.85, False)]
    fit = rt.isotonic(pairs)
    vals = [v for _, v in fit]
    assert vals == sorted(vals)
    assert rt.calibrate(fit, 0.99) == vals[-1]


def test_reliability_and_ece():
    pairs = [(0.9, True)] * 6 + [(0.9, False)] * 4
    rows = rt.reliability(pairs, [0.0, 0.5, 1.0])
    assert rows[1]["n"] == 10 and abs(rows[1]["right"] - 0.6) < 1e-9
    assert abs(rt.ece(pairs, [0.0, 0.5, 1.0]) - 0.3) < 1e-9


def test_lowest_safe_needs_lower_bound():
    pairs = [(0.9, True)] * 40 + [(0.8, True)] * 30 + \
        [(0.8, False)] * 10
    t, n, lo = rt.lowest_safe(pairs, 0.9)
    assert t == 0.9 and n == 40 and lo >= 0.9


def test_wilson():
    lo, hi = rt.wilson(95, 100)
    assert lo < 0.95 < hi


def test_fixture_is_seeded_and_labeled():
    rows = make_data.load()
    assert len(rows) == 400 and all(r["_synthetic"] for r in rows)
    assert make_data.make() == make_data.OUT.read_bytes()


def test_overlap_counts_once():
    r1 = {"field": True, "start": 0, "end": 12}
    r2 = {"field": True, "start": 6, "end": 18}
    r3 = {"field": False, "start": 0, "end": 40}
    assert make_data.field_months([r1, r2, r3]) == 18


def test_review_flag_beats_high_score():
    c = rt.Case("x", "meets", 0.99, flags=["NEAR"])
    assert rt.route(c, LINE)[0] == "review"


def test_flags_from_text():
    from chapters.ch16_routing.flags import flags
    text = ("Experience\n- A, Jan 2025 to present\n"
            "- B, Mar 2025 to Jan 2026\nCertifications")
    assert "OVERLAP" in flags(text, 28)
    assert "NEAR" in flags(text, 28)
    assert "NO_COUNT" in flags(text, "n/a")


def test_quayfen_tickets_seeded():
    from chapters.ch16_routing.quayfen import tickets
    a, _ = tickets()
    b, _ = tickets()
    assert a == b and len(a) == 135
    assert all(t["_synthetic"] for t in a)


def test_person_category_fails_closed_at_any_score():
    line = rt.RoutingLine(step="t", version="1", model="m",
                          complete_at=0.8, review_at=0.5,
                          fail_closed=["person"])
    assert rt.route(rt.Case("x", "person", 0.99),
                    line)[0] == "fail_closed"
