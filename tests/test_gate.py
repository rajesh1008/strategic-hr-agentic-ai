"""Offline tests: the gate is deterministic and needs no model or key."""
from hrai import gate

P = gate.load_policy("ats-status")


def test_agent_may_schedule_interview():
    assert gate.evaluate(P, status="interview_scheduled", actor="agent", context={}).allowed


def test_agent_may_not_end_an_application():
    d = gate.evaluate(P, status="not_progressed", actor="agent", context={"reason_code": "LOW_RANK"})
    assert not d.allowed and "no rule allows" in d.reason


def test_human_needs_recruiter_and_reason():
    d = gate.evaluate(P, status="not_progressed", actor="human", context={"reason_code": "R2"})
    assert not d.allowed and d.missing == ["recruiter_id"]
    assert gate.evaluate(P, status="not_progressed", actor="human",
                         context={"reason_code": "R2", "recruiter_id": "U-1187"}).allowed


def test_unknown_status_denied_by_default():
    assert not gate.evaluate(P, status="hired", actor="agent", context={}).allowed
