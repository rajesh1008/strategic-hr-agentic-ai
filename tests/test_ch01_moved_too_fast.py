"""Offline tests for Chapter 1 (no key, no network)."""
from chapters.ch01_moved_too_fast import first_pass, incidents
from chapters.ch01_moved_too_fast import replay
from hrai import gate


def _quiet(_line=""):
    pass


def test_vendor_batch_is_412_and_gate_refuses_all():
    policy = gate.load_policy("ats-status")
    cands = replay.load()
    pre = replay.before(policy, cands)
    assert len(pre) == 412
    assert all(e["status"] == "not_progressed" for e in pre)
    assert not any(e["recruiter_id"] for e in pre)
    assert all(e["gate"] == "DENY" for e in pre)


def test_agent_cannot_end_an_application():
    policy = gate.load_policy("ats-status")
    cands = replay.load()
    ats, evs = replay.apply(policy, cands,
                            replay.offline_proposals(cands))
    assert set(ats.values()) == {"applied"}
    assert all(e["gate"] == "DENY" for e in evs)


def test_malformed_and_unknown_proposals_are_denied():
    policy = gate.load_policy("ats-status")
    cands = replay.load()
    props = [{"candidate_id": "C-0412-007",
              "status": "interview_scheduled"},
             {"candidate_id": "C-9999-999",
              "status": "interview_scheduled",
              "reason_code": "TOP"}]
    ats, evs = replay.apply(policy, cands, props)
    assert [e["gate"] for e in evs] == ["DENY", "DENY"]
    assert evs[1]["gate_reason"] == "unknown candidate"
    assert ats["C-0412-007"] == "applied"


def test_agent_may_schedule_an_interview():
    policy = gate.load_policy("ats-status")
    cands = replay.load()
    props = [{"candidate_id": "C-0412-007",
              "status": "interview_scheduled",
              "reason_code": "TOP_RANK"}]
    ats, evs = replay.apply(policy, cands, props)
    assert evs[0]["gate"] == "ALLOW"
    assert ats["C-0412-007"] == "interview_scheduled"


def test_first_pass_flags_five_steps_over_ceiling():
    out = first_pass.run(_quiet)
    over = [s["id"] for s in out if not s["within"]]
    assert over == ["S2", "S3", "B1", "A1", "C2"]
    placed = {s["id"]: s["placed"] for s in out}
    assert placed["S2"] == "keep/recommend"
    assert placed["C2"] == "keep/retrieve"
    assert placed["S5"] == "automate/act"


def test_incident_counts():
    h = incidents.hartwell(_quiet)
    assert h["status"]["not_progressed"] == 412
    assert sum(h["invited"].values()) == 61
    assert h["invited"]["not_progressed"] == 14
    a = incidents.ashby_lowe(_quiet)
    assert (a["declined"], a["declined_certified"],
            a["declined_for_wording"]) == (44, 22, 20)
    b = incidents.brightwater(_quiet)
    assert (b["booked"], b["cancelled"], b["not_rebooked"],
            b["not_told"], b["neither"]) == (286, 83, 27, 24, 8)


def test_updates_sent_as_a_string_are_parsed_or_denied():
    ups, s = replay.updates_of(
        {"updates": '[{"candidate_id": "C-0412-007"}]'})
    assert s and ups == [{"candidate_id": "C-0412-007"}]
    ups, s = replay.updates_of({"updates": "not json"})
    assert s and ups == [{}]
    ups, s = replay.updates_of({"updates": ["x", {"a": 1}]})
    assert not s and ups == [{}, {"a": 1}]
    policy = gate.load_policy("ats-status")
    _, evs = replay.apply(policy, replay.load(), [{}])
    assert evs[0]["gate"] == "DENY"
