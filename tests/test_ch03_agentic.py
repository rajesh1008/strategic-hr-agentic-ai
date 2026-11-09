"""Offline tests for Chapter 3 (no model, no network)."""
from types import SimpleNamespace as NS

from chapters.ch03_agentic_systems import tools as T
from chapters.ch03_agentic_systems.hris import HartwellOne, days
from chapters.ch03_agentic_systems.loop import Budget, run

EMP = "HW-012771"


def sess(lose=False):
    return T.Session(EMP, HartwellOne(lose_reply_once=lose))


def test_working_days_skip_weekend_and_holiday():
    assert days("2027-05-24", "2027-05-31", ["2027-05-31"]) == [
        "2027-05-24", "2027-05-25", "2027-05-26", "2027-05-27",
        "2027-05-28"]


def test_rule_approves_two_days_in_april():
    c = T.checks(sess(), "2027-04-08", "2027-04-09", "vacation")
    assert c["days"] == 2 and all(
        c[k] for k in ("within_balance", "notice_ok",
                       "short_request", "staffing_ok"))


def test_week_in_may_goes_to_supervisor():
    c = T.checks(sess(), "2027-05-24", "2027-05-28", "vacation")
    assert not c["short_request"] and not c["staffing_ok"]
    assert c["short_staffed_days"] == ["2027-05-27", "2027-05-28"]
    s = sess()
    r = T.propose(s, {"start": "2027-05-24", "end": "2027-05-28",
                      "type": "vacation"})
    assert r.text.startswith("PENDING") and s.hris.writes == 0


def test_timeout_is_resolved_by_readback_not_retry():
    s = sess(lose=True)
    a = {"start": "2027-04-08", "end": "2027-04-09",
         "type": "vacation"}
    r = T.propose(s, a)
    assert "readback after a timeout" in r.text
    assert s.hris.writes == 1
    again = T.propose(s, a)        # the agent asks twice
    assert again.text.startswith("Already done")
    assert s.hris.writes == 1
    assert s.hris.balance(EMP)["vacation"] == 4.5


def test_direct_tool_double_books_on_retry():
    s = sess(lose=True)
    book = {t.name: t for t in T.direct_tools(s)}["book_leave"]
    a = {"start": "2027-04-08", "end": "2027-04-09",
         "type": "vacation"}
    assert book.handler(a).error
    book.handler(a)
    assert s.hris.writes == 2
    assert s.hris.balance(EMP)["vacation"] == 2.5


def test_memory_keeps_preference_not_health():
    s = sess()
    rem = {t.name: t for t in T.controlled_tools(s)}[
        "remember_preference"]
    assert not rem.handler({"key": "contact_channel",
                            "value": "text message"}).error
    assert rem.handler({"key": "contact_channel",
                        "value": "texts; knee surgery"}).error
    assert rem.handler({"key": "health", "value": "x"}).error
    assert s.notes == [{"key": "contact_channel",
                        "value": "text message",
                        "retain_days": 90}]


def test_balance_of_someone_else_is_denied():
    s = sess()
    bal = {t.name: t for t in T.direct_tools(s)}[
        "get_leave_balance"]
    assert bal.handler({"employee_id": "HW-012781"}).error


class FakeRec:
    """Scripted model: one tool call, then an answer."""
    def __init__(self, script):
        self.script, self.n = script, 0

    def create(self, **kw):
        blocks = self.script[self.n]
        self.n += 1
        return NS(content=blocks, model="fake",
                  usage=NS(output_tokens=10))


def block(**kw):
    kw.setdefault("model_dump", lambda **_: dict(kw))
    return NS(**kw)


def test_loop_stops_on_answer_and_on_budget():
    s = sess()
    call = block(type="tool_use", id="t1",
                 name="get_leave_policy", input={})
    say = block(type="text", text="Done.")
    out = run(FakeRec([[call], [say]]), "sys",
              T.controlled_tools(s), "hi")
    assert out.stop_reason == "answered" and out.turns == 2
    out = run(FakeRec([[call]] * 9), "sys",
              T.controlled_tools(s), "hi", Budget(max_turns=3))
    assert out.stop_reason == "budget: turns"
    assert len(out.calls) == 3


def test_hand_off_stops_the_loop():
    s = sess()
    call = block(type="tool_use", id="t1",
                 name="hand_off_to_person",
                 input={"reason": "asked for a person"})
    out = run(FakeRec([[call]]), "sys", T.direct_tools(s), "hi")
    assert out.stop_reason == "human route"


def test_permission_table_findings():
    import yaml
    from pathlib import Path
    from chapters.ch03_agentic_systems import permissions as P
    t = yaml.safe_load((Path(P.__file__).parent
                        / "tool_tables.yaml").read_text())
    n = {a: sum(len(P.findings(x)) for x in v["tools"])
         for a, v in t.items()}
    assert n == {"askhartwell_v2": 0,
                 "ashby_lowe_suite_assistant": 5,
                 "aurelia_shift_swap": 0,
                 "lakemont_credential_check": 1}
