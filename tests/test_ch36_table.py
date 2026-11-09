"""Tests for Chapter 36 (the closing Scoreboard)."""
from chapters.ch36_table import explain, horizon, promises, scoreboard


def test_verdicts_computed():
    sb = scoreboard.load("scoreboard.yaml")
    v = {o["n"]: scoreboard.verdict(o) for o in sb["objectives"]}
    assert v[5] == v[8] == v[9] == "met"
    assert v[7] == "partly met"


def test_records_count_and_owners():
    dr = scoreboard.load("records.yaml")
    ids = [r["id"] for r in dr["records"]]
    assert len(ids) == len(set(ids)) == 28
    assert all(r["owner"] for r in dr["records"])
    assert sum(r["gate"] for r in dr["returns"]) == 3


def test_board_weight_only_production():
    assert scoreboard.weight("measured") == 1.0
    for s in ("tested", "shadow", "claimed", "illustrative",
              "projection"):
        assert scoreboard.weight(s) == 0.0


def test_promises_split():
    s = promises.split(promises.load())
    assert len(s["closed"]) + len(s["dated"]) + len(s["undated"]) \
        == len(promises.load())
    assert all(r.get("due") for r in s["dated"])


def test_horizon_every_row_cited():
    d = horizon.load()
    assert all(m["r"].startswith("R-") for m in d["milestones"])
    s = horizon.sort(d)
    assert all(m["date"] > d["as_of"] for m in s["ahead"])


def test_explain_checks_catch_bad_notes():
    bad = ("Our AI agent caused 40 duplicate payments. This will "
           "never happen again. Contact HR.")
    c = explain.check("board", bad)
    assert not c["N1"] and not c["PROMISE"] and not c["OWNER"]
    assert not c["CAUSE"] and not c["BOARD"]
    good = ("On November 16, 2027 the payroll feed retried a batch "
            "and 37 bank changes were held. All 37 were reversed "
            "and paid on Friday, November 19. We missed one target. "
            "Megan Hale owns DR-23-01.")
    c = explain.check("board", good)
    c.pop("_stray")
    assert all(c.values())
    e = explain.check("employee", "PR-1 readback found it; "
                      "you were paid on November 19.")
    assert not e["PLAIN"]


def test_recheck_plain_cause():
    from chapters.ch36_table import recheck
    assert recheck.cause_v11("A fault sent your change twice.")
    assert not recheck.cause_v11("An error caused your bank details "
                                 "to be changed more than once.")
    assert not recheck.cause_v11("The agent caused the duplicate "
                                 "and it was sent twice.")


def test_mismatch_status_carries_stored_value():
    from chapters.ch14_controlled_actions.actions import Lifecycle
    from chapters.ch14_controlled_actions.fakes import (Clock,
                                                        HartwellOne)
    from chapters.ch14_controlled_actions import agent as A
    lc = Lifecycle(HartwellOne(), Clock(),
                   managers={A.LENA: "HW-012927"})
    lc.hris.inject("overwrite", emp=A.LENA)
    act = lc.propose(A.LENA, "home_address", A.NEW,
                     requester=A.LENA)
    assert act.state == "mismatch"
    assert act.stored and act.stored in lc.status_text(act)


def test_mismatch_recheck_checks():
    from chapters.ch36_table.mismatch_recheck import FALSE, STORED
    assert FALSE.search("Your record still shows the old address")
    assert FALSE.search("Your current address on file hasn't"
                        " been changed yet")
    assert not FALSE.search("HartwellOne shows a different address"
                            " on file, so the change wasn't"
                            " confirmed.")
    assert STORED.search("it now shows 2240 Larimer St, Apt 15")
