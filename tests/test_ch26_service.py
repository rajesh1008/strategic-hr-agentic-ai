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


def test_catalog_v0_fails_and_v1_passes():
    import yaml
    from chapters.ch26_service import catalog as c
    for v, want in (("0", True), ("1", False)):
        cat = yaml.safe_load(
            (c.DATA / f"catalog_v{v}.yaml").read_text())
        bad = [c.check(r, cat["jurisdictions"])
               for r in cat["actions"]]
        assert any(bad) is want


def test_journey_holds_access_before_right_to_work():
    from chapters.ch26_service.journeys import ONBOARD, held
    order = [("offer_signed", "recruiter"),
             ("record_created", "agent"),
             ("access_granted", "agent")]
    assert ("access_granted", "before right_to_work") \
        in held(ONBOARD, order)


def test_language_and_figures():
    from chapters.ch26_service.languages import (
        figures, language)
    assert language("Ти маєш 13,5 днів відпустки.") == "uk"
    assert figures("13,5 dni; 26 listopada") == (True, True)
