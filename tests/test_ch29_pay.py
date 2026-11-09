"""Offline tests for Chapter 29 (no key, no network)."""
from datetime import date
from decimal import Decimal as D

from chapters.ch29_pay import (desk, explain, gratuity, offers,
                               rules, sectors, variance)
from chapters.ch29_pay.sheets import MARISOL, sheets


def test_marisol_rule_and_legacy():
    r = rules.compute(MARISOL)
    assert r.gross == D("2233.96") and r.ot == 14
    assert rules.legacy(MARISOL) == D("2197.40")


def test_california_daily_and_double_time():
    s = rules.Sheet("X", "CA", D("20"), [D(13)] + [D(8)] * 4
                    + [D(0)] * 2)
    r = rules.compute(s)
    assert (r.ot, r.dt) == (D(4), D(1))
    assert r.gross == D(45) * 20 + 4 * 10 + 20


def test_colorado_takes_the_greater():
    s = rules.Sheet("X", "CO", D("20"), [D(14), D(14)]
                    + [D(0)] * 5)
    assert rules.compute(s).ot == 4


def test_no_overtime_at_forty():
    assert all(rules.compute(s).ot == 0 for s in sheets()
               if sum(s.days) <= 40 and s.state != "CA")


def test_uae_gratuity():
    assert gratuity.uae(D(3000), D("0.9")) == 0
    assert gratuity.uae(D(3000), D(5)) == D(10500)
    assert gratuity.uae(D(3000), D(6)) == D(13500)
    assert gratuity.uae(D(3000), D(40)) == D(72000)


def test_saudi_resignation_shares():
    assert gratuity.saudi(D(4000), D("1.5"), True) == 0
    assert gratuity.saudi(D(4000), D(4), True) == D("2666.67")
    assert gratuity.saudi(D(4000), D(12), True) == D(38000)


def test_offer_rule_ignores_pay_history():
    for c in offers.candidates():
        assert offers.LOW <= offers.rule(c["years"], c["pe"]) \
            <= offers.HIGH


def test_postings():
    got = {p[0]: sectors.posting_check(p)
           for p in sectors.POSTINGS}
    assert got["TK-NY-121"] == []
    assert "NY: no minimum and maximum" in got["TK-NY-130"]


def test_variance_v2_finds_all_planted():
    lines = variance.run_lines()
    faults = [l for l in lines if l.fault]
    assert all(variance.hold(l) for l in faults)
    assert sum(bool(variance.hold(l, variance.V1))
               for l in faults) == 6


def test_answer_check_helpers():
    assert explain.numbers("$2,233.96 and 36.50") == {
        "2233.96", "36.5"}
    assert explain.CLAIM.search("I've updated your rate")
    assert not explain.CLAIM.search("I can't update your rate")


def test_two_month_clock():
    assert desk.add_months(date(2028, 12, 31), 2) == \
        date(2029, 2, 28)
