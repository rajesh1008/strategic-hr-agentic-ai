"""Offline tests for chapter 31 (no model calls)."""
from datetime import date

import pytest

from chapters.ch31_restructuring import (
    exposure, scenario_agent, scenarios, selection, sectors,
    timeline)
from chapters.ch31_restructuring.model import (
    assert_no_people, load)


def test_exposure_is_not_absorption():
    r = exposure.readings(load())
    for role, x in r.items():
        assert x["vendor"] > x["high"] >= x["plan"] >= x["base"]
    assert round(r["hr_admin"]["exposed"], 2) == 0.90


def test_fan_totals():
    f = scenarios.fan(load())
    risk = {c: sum(p.at_risk for p in ps) for c, ps in f.items()}
    assert risk["vendor"] == 63
    assert risk["plan"] == risk["base"] == risk["high"] == 0
    end = {c: sum(p.need[-1] for p in ps) for c, ps in f.items()}
    assert end == {"vendor": 70, "base": 131, "plan": 120,
                   "high": 113}


def test_no_people_in_outputs():
    assert_no_people(scenarios.summary(load()))
    with pytest.raises(ValueError):
        assert_no_people(["HW-310001 at risk"])


def test_timeline_flags():
    props, rules = load("proposals.yaml"), load("rules.yaml")
    cfo = timeline.run(props["cfo_draft"], rules)
    man = [x for x in cfo if x["site"] == "Manchester"][0]
    assert man["late"] and man["earliest"] == date(2028, 7, 1)
    b = timeline.run(props["aurelia_b"], rules)
    assert "SHAPE" in b[0]["flags"] and not b[0]["triggered"]
    a = timeline.run(props["aurelia_a"], rules)
    assert a[0]["days"] == 56
    cob = timeline.run(props["cobbleford"], rules)
    assert cob[0]["flags"] == ["NEAR"]


def test_ontario_bands():
    rules = load("rules.yaml")
    assert timeline.band(rules["CA-ON"], 199) == 56
    assert timeline.band(rules["CA-ON"], 200) == 84
    assert timeline.band(rules["CA-ON"], 500) == 112
    assert timeline.band(rules["UK"], 100) == 45


def test_selection_checks():
    cfg = load("matrices.yaml")
    ppl = selection.pool()
    v1 = selection.checks(cfg["v1"], cfg, ppl)
    v2 = selection.checks(cfg["v2"], cfg, ppl)
    assert [k for k, s in v1.items() if s == "FAIL"] == [
        "SC-1", "SC-2", "SC-3", "SC-4"]
    assert set(v2.values()) == {"PASS"}


def test_retraining_offers_everyone():
    c = sectors.crew()
    v1 = sectors.retrain_v1(c, 40)
    assert len(v1) == 40


def test_v2_tools_return_no_people():
    cfg = load()
    for name in scenario_agent.DESIGN["v2"]:
        args = {"get_scope": {}, "run_scenario": {
            "case": "vendor"}, "consultation_timeline": {
            "site": "MAN", "count": 29, "start": "2028-06-01",
            "effective": "2028-06-30"}}[name]
        out = scenario_agent.tool(name, args, cfg)
        assert not scenario_agent.PERSON.search(out)
    assert "get_employees" not in scenario_agent.DESIGN["v2"]


def test_agent_checks():
    allowed = {135, 62, 29}
    assert scenario_agent.numbers_ok(
        "Scope is 210 roles; Manchester 62, 29 at risk by"
        " 30 June 2028 (2028Q3).", allowed) == ["210"]
    assert scenario_agent.achievable(
        "Leeds is below threshold; 30 June 2028 is"
        " achievable.") == ["30 June 2028 is achievable."]
    assert not scenario_agent.achievable(
        "June 30, 2028 is not achievable.")
