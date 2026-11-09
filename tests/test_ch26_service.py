"""Offline checks for Chapter 26 (no model, no network)."""
from chapters.ch26_service import route


def test_rule_routes_named_words():
    assert route.rule("Can I talk to a real person") == "adviser"
    assert route.rule("My dad died last night") == "care"
    assert route.rule("I'm pregnant") == "leave"


def test_rule_leaves_routine_to_agent():
    for c in route.PACK["cases"]:
        if c["expect"] == "agent":
            assert route.rule(c["text"]) is None, c["id"]


def test_queue_language_before_lane():
    julie = route.PEOPLE["julie"]
    assert route.queue("care", julie) == "Montréal HR services"
    assert route.queue("pay", route.PEOPLE["wes"]) \
        == "Quayfen tier 1"


def test_promise_names_time():
    assert "10 minutes" in route.promise("care",
                                         route.PEOPLE["lena"])
