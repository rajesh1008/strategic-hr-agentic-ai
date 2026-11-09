"""Offline tests for the Chapter 10 diagnostic (no API calls)."""
from datetime import datetime, timedelta

from chapters.ch10_diagnose import mining, pilots, problem, taxonomy
from chapters.ch10_diagnose.export import wilson


def evs(*acts, step=10):
    t0 = datetime(2026, 10, 1, 9)
    return [{"activity": a, "t": t0 + timedelta(minutes=i * step)}
            for i, a in enumerate(acts)]


def test_route_fails_closed_on_unknown_and_sensitive():
    assert taxonomy.route("NOPE", False, False) == "person"
    assert taxonomy.route("LV-BAL", True, False) == "person"


def test_person_route_beats_chasing():
    assert taxonomy.route("ACCOM", False, True) == "person"


def test_chasing_makes_fix():
    assert taxonomy.route("LV-BAL", False, True) == "fix"
    assert taxonomy.route("LV-BAL", False, False) == "answer"


def test_wilson_contains_point():
    lo, hi = wilson(30, 100)
    assert lo < 0.30 < hi


def test_endings():
    assert mining.ending(evs("Chat opened", "Bot answered",
                             "Answer accepted")) == \
        "bot answer accepted"
    assert mining.ending(evs("Chat opened", "Bot fallback",
                             "Handoff promised")).startswith("nothing")
    assert mining.ending(evs("Chat opened", "Handoff promised",
                             "Ticket created", "Resolved")) == \
        "ticket resolved"


def test_time_to_nothing_counts_only_dead_ends():
    cases = {"a": evs("Chat opened", "Bot fallback",
                      "Conversation abandoned"),
             "b": evs("Chat opened", "Bot answered",
                      "Answer accepted")}
    assert mining.time_to_nothing(cases) == [20.0]


def test_pilot_without_owner_stops():
    p = {"owner": None, "baseline": "x", "kill": "y",
         "needs_write": False, "write_built": False,
         "changes_person": False, "approver": None,
         "run_owner": "z"}
    assert pilots.verdict(pilots.checks(p)) == "stop: no owner"
    p["owner"] = "lead"
    assert pilots.verdict(pilots.checks(p)).startswith("continue")
    p["changes_person"] = True
    assert pilots.verdict(pilots.checks(p)) == "stalled: authority"


def test_problem_statement_rejects_tool_words():
    s = dict(who="staff", now="12 tickets in Q4", cost="c",
             owner="Payroll lead", measure="AI deflects 60%",
             limits="none")
    assert any("names a tool" in f for f in problem.check(s))
    s["measure"] = "fewer than 5 by June, People Analytics"
    assert problem.check(s) == []
