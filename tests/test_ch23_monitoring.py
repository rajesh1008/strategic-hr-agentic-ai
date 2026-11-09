"""Offline tests for Chapter 23: the incident replay, runbook
scoring, regulator pack, canary layout, inventory checks,
drafter checks and the FOI deadline. No model."""
from datetime import date

import yaml

from chapters.ch23_monitoring import (canary, drafter, foi,
                                      inventory, pack)

D = "chapters/ch23_monitoring/data/"


def test_canary_is_24_fixed_cases():
    a, b = canary.canary(), canary.canary()
    assert len(a) == 24
    assert [x["candidate_id"] for x in a] == \
        [x["candidate_id"] for x in b]


def test_northgate_layout_keeps_every_role():
    for c in canary.canary():
        ng = canary.northgate(c["resume"])
        roles = [ln for ln in c["resume"].splitlines()
                 if canary.ROLE.match(ln)]
        assert ng.count(" | ") // 2 == len(roles)
        assert " to present" not in ng
        assert "Licenses & certifications:" in ng


def test_inventory_october_has_five_problems():
    inv = yaml.safe_load(open(D + "inventory-2027-10.yaml"))
    codes = sorted(p[:5] for p in inventory.check(inv))
    assert codes == ["INV-1", "INV-2", "INV-3", "INV-4",
                     "INV-5"]


def test_inventory_december_lists_the_feed():
    inv = yaml.safe_load(open(D + "inventory-2027-12.yaml"))
    probs = inventory.check(inv)
    assert not [p for p in probs if p.startswith("INV-5")]


def test_drafter_holds_invented_number():
    facts = "37 employees; pay on November 19."
    bad = ("NOTICE: 38 of you were affected. You need to do "
           "nothing. Pay on November 19. Ask AskHartwell.")
    assert drafter.check(bad, facts) == \
        ["number not in facts: 38"]


def test_drafter_holds_promise_and_missing_route():
    facts = "37 employees; pay on November 19."
    bad = ("NOTICE: This will never happen again. Pay on "
           "November 19. You need to do nothing.")
    probs = drafter.check(bad, facts)
    assert "promise: 'will never'" in probs
    assert "notice lacks where to ask" in probs


def test_foi_deadline_skips_weekends_and_holidays():
    assert foi.working_day(date(2027, 11, 1), 20, set()) == \
        date(2027, 11, 29)
    assert foi.working_day(date(2027, 12, 20), 5,
                           {"2027-12-27", "2027-12-28"}) == \
        date(2027, 12, 29)


def test_pack_finds_cobbleford_gaps():
    inputs = pack.load("pack_inputs.yaml")
    g = pack.gaps(inputs["incidents"]["CB-2027-044"],
                  inputs["sections"])
    assert sorted(k for k, v in g.items() if v) == \
        ["RP-4", "RP-6", "RP-8", "RP-9"]


class Quiet:
    def print(self, line=""):
        pass


def test_blind_retry_holds_37_and_lookup_holds_none():
    from chapters.ch23_monitoring import feed
    blind = feed.night("blind", Quiet())
    fixed = feed.night("lookup", Quiet())
    assert len(blind["bank_held"]) == 37
    assert len(fixed["bank_held"]) == 0
    assert sum(c["origin"] == "agent"
               for c in blind["bank_held"]) == 23


def test_hartwell_misses_only_t1():
    from chapters.ch23_monitoring import incident
    rows = incident.score(incident.load("inc-2027-031.yaml"),
                          incident.load("runbook.yaml"))
    assert [r["id"] for r in rows if not r["met"]] == ["T1"]


def test_cluster_rule_fires_on_third_call():
    from chapters.ch23_monitoring import quayfen
    t = [quayfen.minutes(x) for x in
         ["19:20", "19:48", "20:05", "20:41"]]
    assert quayfen.fires(t) == quayfen.minutes("20:05")
