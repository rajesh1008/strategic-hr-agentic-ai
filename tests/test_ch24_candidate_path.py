"""Offline tests for Chapter 24 (no API calls)."""
from chapters.ch24_candidate_path import (agency, capacity, notice,
                                          path, polish, scheduler,
                                          sectors, video)


def test_path_is_seeded_and_counts_add_up():
    a = path.simulate("2027-03 old path")
    b = path.simulate("2027-03 old path")
    assert a == b and len(a) == 10_000
    f = path.funnel(a)
    assert f[0]["reached"] == 10_000


def test_video_has_three_phases_of_270():
    rows = video.make()
    for ph in ("phone", "video", "choice"):
        assert sum(r["phase"] == ph for r in rows) == 270


def test_capacity_never_allows_model_rejection():
    for d in capacity.designs(2000, 0.3):
        if "rejects" in d[0]:
            assert d[2] is False


def test_polish_sample_is_forty():
    assert len(polish.sample()) == 40


def test_message_check():
    assert scheduler.check_message("You passed!") is not None
    assert scheduler.check_message(
        "What is your medical condition?") is not None
    assert scheduler.check_message(
        "I have passed your request to the team.") is None
    assert scheduler.check_message(
        "You have a medical appointment noted.") is None


def test_booking_rule_refuses_unadvanced_and_races():
    w = scheduler.world("S4", True)
    assert scheduler.book(w, "SL-1609")["status"] == "refused"
    assert scheduler.run_tool(w, "find_slots", {
        "candidate_id": "C24-104"})["status"] == "refused"
    w = scheduler.world("S2", True)
    assert scheduler.book(w, "SL-1509")["status"] == "conflict"
    assert scheduler.book(w, "SL-1513")["status"] == "done"


def test_notice_has_no_duty_for_rule_knockout():
    assert all(notice.cell(j, {"rule"}) == "."
               for j in notice.JURIS)
    assert notice.cell("Connecticut", {"scheduling"}) == "X"


def test_sector_checks():
    held = [r for r, why in sectors.straits() if why]
    assert held == ["SL-EP-03", "SL-EP-05", "SL-EP-08"]
    assert agency.order_flags("Prefer young guys") == [
        "sex", "age (ADEA, not Title VII)"]
    assert agency.order_flags("Sunday shifts only") == []
