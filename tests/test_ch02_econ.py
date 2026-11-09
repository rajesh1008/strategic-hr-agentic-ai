"""Offline tests for the Chapter 2 workforce-economics calculator."""
import pytest

from chapters.ch02_strategic_hr import econ, numbers

FX = econ.load("roles.json")
OM = econ.load("operating_model.json")
ICU = econ.load("lakemont_icu.json")


def test_forty_roles_matter():
    crit = [r for r in econ.role_map(FX) if r["critical"]]
    assert len(crit) == 40


def test_volume_roles_are_not_critical_even_when_costly():
    rows = {r["id"]: r for r in econ.role_map(FX)}
    assert rows["FT-US"]["annual"] > rows["PD-US"]["annual"]
    assert not rows["FT-US"]["critical"]


def test_attrition_narrows_the_offshore_gap():
    d, h, m = OM["delivery_models"]
    esc = OM["escalation_cost_per_contact"]
    naive = econ.naive_cost(d) / econ.naive_cost(h)
    allin = econ.cost_per_resolved(d, esc) / econ.cost_per_resolved(h, esc)
    assert allin < naive
    # the cheapest seat is not the cheapest resolved contact
    assert econ.annual_cost(m) < econ.annual_cost(h)
    assert econ.cost_per_resolved(m, esc) > econ.cost_per_resolved(h, esc)


def test_break_even_is_where_agent_equals_no_agent():
    be = econ.break_even_containment(OM)
    human, _ = econ._human_route(OM)
    assert econ.agent_blended(OM, be) == pytest.approx(human)


def test_unplaced_hours_are_refused():
    om = {**OM, "redeployed_to": OM["redeployed_to"][:-1]}
    with pytest.raises(ValueError):
        econ.hours_ledger(om)
    assert econ.hours_ledger(OM)["fte_of_time"] == 60.0


def test_heads_language_is_flagged():
    assert econ.refuse_heads("FTE savings of 60") == ["fte savings"]
    assert econ.refuse_heads("60 FTE-equivalents of time") == []


def test_agent_cannot_decide_consequential():
    bad = [{"decision": "x", "consequential": True,
            "decides": "agent", "agent_mode": "act"}]
    assert len(econ.check_rights(bad)) == 2
    assert econ.check_rights(OM["decision_rights"]) == []


def test_bed_closure_is_counted():
    sp = econ.shift_premium(ICU)
    assert sp["expected"] > 2 * econ.agency_only_view(ICU)


def test_unsourced_numbers():
    src = "cost $22,939,001 a year; 60.0 FTE"
    assert numbers.unsourced("$22,939,001 and 60.0", src) == []
    assert numbers.unsourced("about 23 million", src) == ["23"]


def test_revenue_view_inflates_the_sales_case():
    bw = econ.load("brightwater_sales.json")
    rev = econ.role_map(bw, "revenue_at_risk_per_day")
    mar = econ.role_map(bw)
    assert sum(r["annual"] for r in rev) > 20 * sum(
        r["annual"] for r in mar)
    crit = {r["id"] for r in mar if r["critical"]}
    assert crit == {"NKA-US", "KAM-UK", "KAM-NL"}


def test_manager_hours_more_than_double_fieldnote_cost():
    fn = econ.cost_per_employee(econ.load("fieldnote_people.json"))
    assert fn["all_in"] > 2 * fn["visible"]


def test_cfo_view_carries_only_hartwell_numbers():
    from chapters.ch02_strategic_hr import workforce_economics
    lines: list[str] = []
    workforce_economics.report(lines.append, hartwell_only=True)
    text = "\n".join(lines).upper()
    for org in ("LAKEMONT", "BRIGHTWATER", "FIELDNOTE"):
        assert org not in text
