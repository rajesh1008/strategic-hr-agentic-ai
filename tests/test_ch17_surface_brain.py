"""Offline tests for Chapter 17 (no key, no network)."""
from types import SimpleNamespace as N

import pytest

from chapters.ch17_surface_brain import (assistant, entitled,
                                         pilot_log, retrieve,
                                         surfaces)
from chapters.ch17_surface_brain.gateway import Gateway, Refused

DOCS, USERS = entitled.load("hartwell")


class FakeRec:
    def __init__(self, text='{"answer": "25 days", "sources": '
                 '["UK-POL-11"], "route": false}'):
        self.text = text

    def create(self, **req):
        return N(content=[N(type="text", text=self.text)],
                 usage=N(input_tokens=1000, output_tokens=100))


def test_entitlement_rules():
    paul = USERS["paul"]
    assert entitled.can_read(paul, DOCS["UK-REW-03"])[0]
    assert entitled.can_read(paul, DOCS["NL-REW-07"]) == (
        False, "entity NL")
    assert entitled.can_read(paul, DOCS["UK-ER-09"]) == (
        False, "audience")
    assert not entitled.can_read(USERS["helen"], DOCS["NL-REW-07"])[0]
    assert entitled.can_read(USERS["reward"], DOCS["NL-REW-07"])[0]
    assert not entitled.can_read(USERS["brisbane"],
                                 DOCS["US-IL-CBA"])[0]
    assert entitled.can_read(USERS["joliet"], DOCS["US-IL-CBA"])[0]
    assert not entitled.can_read(USERS["lena"], DOCS["UK-REW-03"])[0]


def test_filter_before_rank():
    q = "pay band for a senior maintenance technician"
    pilot = retrieve.search(q, USERS["paul"], DOCS, "pilot")
    assert pilot[0] == "NL-REW-07"
    ent = retrieve.search(q, USERS["paul"], DOCS, "entitled")
    assert ent and all(entitled.can_read(USERS["paul"], DOCS[i])[0]
                       for i in ent)


def test_gateway_refusals():
    gw = Gateway.load(FakeRec())
    kw = dict(user_id="paul", surface="test", system="s",
              prompt="p", docs=[], question="leave days")
    with pytest.raises(Refused, match="G-UNREG"):
        gw.call(use="ka.nope", caller="svc-ka-eval",
                model="claude-haiku-5-5", **kw)
    with pytest.raises(Refused, match="G-IDENT"):
        gw.call(use="ka.manager", caller="svc-ka-eval",
                model="claude-haiku-5-5", **kw)
    with pytest.raises(Refused, match="G-MODEL"):
        gw.call(use="ka.manager", caller="svc-knowledge-assistant",
                model="claude-opus-5-5", **kw)
    kw["question"] = "notes from the disciplinary investigation"
    with pytest.raises(Refused, match="G-CLASS"):
        gw.call(use="ka.eval", caller="svc-ka-eval",
                model="claude-haiku-5-5", **kw)
    kw["question"] = "leave days"
    gw.pause("ka.eval", by="test")
    with pytest.raises(Refused, match="G-PAUSED"):
        gw.call(use="ka.eval", caller="svc-ka-eval",
                model="claude-haiku-5-5", **kw)
    assert [e["status"] for e in gw.log if "status" in e] == [
        "G-UNREG", "G-IDENT", "G-MODEL", "G-CLASS", "G-PAUSED"]


def test_budget_and_metering_and_redaction():
    gw = Gateway.load(FakeRec())
    gw.uses["ka.eval"]["monthly_budget_usd"] = 0.0016
    kw = dict(use="ka.eval", caller="svc-ka-eval", user_id="u",
              surface="test", system="s", question="leave",
              prompt="HW-012771 asks", model="claude-haiku-5-5",
              docs=[])
    _, e = gw.call(**kw)
    assert e["cost_usd"] == pytest.approx(0.0015)
    assert e["redactions"] == 1 and "prompt" not in e
    gw.call(**kw)
    with pytest.raises(Refused, match="G-BUDGET"):
        gw.call(**kw)


def test_answer_checks():
    paul = USERS["paul"]
    shown = ["UK-REW-03", "GRP-REC-01"]
    ok = {"answer": "UK-T3 is 33,600 to 39,900 pounds.",
          "sources": ["UK-REW-03"], "route": False}
    assert assistant.check(ok, paul, DOCS, shown) == []
    bad = dict(ok, answer="About 37,250 pounds.")
    assert assistant.check(bad, paul, DOCS, shown) == [
        "number 37250 is in no cited source"]
    nos = dict(ok, sources=[])
    assert "answer cites no source" in assistant.check(
        nos, paul, DOCS, shown)
    leak = dict(ok, sources=["NL-REW-07"])
    assert assistant.check(leak, paul, DOCS, ["NL-REW-07"])[0] == (
        "cites NL-REW-07, which this user may not read")
    assert assistant.leaks("Pay group 7 is 3,412 euros", paul, DOCS,
                           []) == ["NL-REW-07"]


def test_entitled_fails_closed():
    gw = Gateway.load(FakeRec('{"answer": "It is 36,750.", '
                              '"sources": ["UK-REW-03"], '
                              '"route": false}'))
    r = assistant.ask(gw, "UK band", USERS["paul"], DOCS,
                      "entitled", "ka.eval", "claude-haiku-5-5")
    assert r["held"] and r["final"] == assistant.ROUTE
    gw2 = Gateway.load(FakeRec('{"answer": "It is 36,750.", '
                               '"sources": ["UK-REW-03"], '
                               '"route": false}'))
    r2 = assistant.ask(gw2, "UK band", USERS["paul"], DOCS, "pilot",
                       "ka.eval", "claude-haiku-5-5")
    assert not r2["held"] and r2["final"] == "It is 36,750."


def test_surface_check_and_pilot_replay():
    gw = Gateway.load(FakeRec())
    assert surfaces.check(gw.uses) == [
        "teams-ka-pilot: shows answers, but ka.manager is at shadow"]
    r = pilot_log.replay("pilot")
    assert r["questions"] == 220 and r["exposed"] > 0
    assert pilot_log.replay("entitled")["exposed"] == 0


def test_whole_design_and_sector_entitlements():
    whole = retrieve.search("x", USERS["paul"], DOCS, "whole")
    assert set(whole) == set(entitled.readable(USERS["paul"], DOCS))
    tk, tu = entitled.load("thorne")
    assert entitled.can_read(tu["ny_senior"], tk["TK-US-LV-26"]) == (
        False, "superseded")
    assert not entitled.can_read(tu["ny_senior"],
                                 tk["TK-PTR-PAY"])[0]
    bw, bu = entitled.load("brightwater")
    assert entitled.readable(bu["kiosk"], bw) == ["BW-GRP-SAFE"]
    assert not entitled.can_read(bu["in_rep"], bw["BWA-SG-INC"])[0]


def test_drive_scan_reach():
    from chapters.ch17_surface_brain import drive_scan
    sizes = {"everyone": 410, "managers": 41, "hr": 2}
    assert drive_scan.reach(["everyone", "hr"], sizes) == 410
    assert drive_scan.reach(["hr"], sizes) == 0
