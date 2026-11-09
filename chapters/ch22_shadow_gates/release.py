"""Chapter 22: the controlled-action release, fixed, at the
Shadow gate.

Book section "The release that waited for its fixes". The
Chapter 20 evaluation pack (June 28, 2027) held AskHartwell's
address and bank-detail release short of the Shadow gate on
three findings. This module is the release with the three
fixes, on top of the Chapter 14 lifecycle and agent:

  F1  matrix v3: an address change that starts on a later
      date is not written by rule; it waits for HR services
      to apply it on the day (golden case G18)
  F2  a dispatcher that sends an approved action within five
      minutes, and an approval that expires goes to payroll
      operations' queue, not nowhere (REC-5)
  F3  the read tool shows actions closed in the last 7 days,
      so "has my change gone through?" can be answered from
      the ledger (the 10:45 reply)

The three levels are re-run exactly as Chapter 20 defined
them: unit checks (no model), the golden set (v1.1, with G18
re-expected for matrix v3) three times, and the one shared
day with REC-1 to REC-6.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch22_shadow_gates.release unit
      python -m chapters.ch22_shadow_gates.release suite
      python -m chapters.ch22_shadow_gates.release day
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

from chapters.ch03_agentic_systems.loop import (Budget, Result,
                                                Tool, run)
from chapters.ch14_controlled_actions import agent as ch14
from chapters.ch14_controlled_actions.actions import (
    Action, Lifecycle, idem_key)
from chapters.ch14_controlled_actions.fakes import (Clock,
                                                    HartwellOne)
from chapters.ch20_eval_pyramid import day as ch20day
from chapters.ch20_eval_pyramid.graders import grade
from chapters.ch20_eval_pyramid.regrade import V11, golden
from hrai.llm import RunRecorder

FUTURE_ROLE = "hr_services"
WINDOW = timedelta(minutes=5)      # F2: dispatch within
RECENT = timedelta(days=7)         # F3: closed actions shown
G18_V3 = ("actions", {"address_change":
                      ["absent", "denied",
                       "awaiting_approval"]},
          "matrix v3: future-dated address waits for a person")


class Lifecycle3(Lifecycle):
    """Chapter 14's lifecycle with matrix v3 and a queue for
    expired approvals."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.payroll_queue: list[str] = []
        self.closed_at: dict[str, object] = {}

    def propose(self, emp, fld, value, requester,
                verified=True, effective: str | None = None):
        today = self.clock.now().date()
        start = _date(effective)
        if fld == "home_address" and start and start > today:
            key = idem_key(emp, fld, value) + f"@{start}"
            old = self.by_key.get(key)
            if old and old.state == "awaiting_approval":
                self._log(old, "proposal", self.agent,
                          "repeat: same key, no new action")
                return old
            a = Action(f"CA-{next(self._n):03d}",
                       "address_change", emp, fld, value,
                       requester, key)
            self.actions[a.id], self.by_key[key] = a, a
            self._log(a, "proposal", self.agent,
                      f"{fld} for {emp} from {start}")
            if requester != emp:
                return self._end(a, "denied", "approval",
                                 "matrix",
                                 "not the requester's record")
            a.state = "awaiting_approval"
            a.reason = (f"{FUTURE_ROLE} to apply it on"
                        f" {start:%B} {start.day} (matrix v3)")
            self._log(a, "approval", "matrix",
                      "awaiting " + a.reason)
            return a
        return super().propose(emp, fld, value, requester,
                               verified)

    def _end(self, a, state, step, by, reason):
        out = super()._end(a, state, step, by, reason)
        self.closed_at[a.id] = self.clock.now()
        return out

    def readback(self, a):
        out = super().readback(a)
        if out.state == "done":
            self.closed_at[a.id] = self.clock.now()
        return out

    def sweep(self) -> list[str]:
        """F2: dispatch what is approved; an approval that has
        run out goes to payroll operations' queue."""
        did = []
        for a in list(self.actions.values()):
            if a.state != "approved":
                continue
            if self.clock.now() > a.approvals[-1]["expires"]:
                self._end(a, "expired", "dispatch",
                          "dispatcher", "approve again")
                self.payroll_queue.append(a.id)
                did.append(f"{a.id} expired: payroll queue")
            else:
                self.dispatch(a.id)
                did.append(f"{a.id} {a.state}")
        return did


def _date(s: str | None) -> date | None:
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None


def queue3(lc: Lifecycle3) -> list[str]:
    """People's queues after F2: advisers take mismatches and
    unknown receipts; payroll takes expired approvals."""
    return ch20day.adviser_queue(lc) + lc.payroll_queue


def kit3(lc: Lifecycle3, emp: str, notes: list) -> list[Tool]:
    base = {t.name: t for t in ch14.kit(lc, emp, notes)}

    def my_record(_):
        r = lc.hris.read(emp)
        now = lc.clock.now()
        mine = [x for x in lc.actions.values() if x.emp == emp]
        open_ = [lc.status_text(x) for x in mine
                 if x.state != "done" and x.id
                 not in lc.closed_at]
        shut = [lc.status_text(x) for x in mine
                if x.id in lc.closed_at
                and now - lc.closed_at[x.id] <= RECENT]
        return Result(f"{r['name']}: home_address "
                      f"{r['home_address']}; bank_account "
                      f"{r['bank_account']}. Open actions: "
                      + ("; ".join(open_) or "none")
                      + ". Closed in the last 7 days: "
                      + ("; ".join(shut) or "none"))

    def propose(a):
        f, v = a.get("field", ""), a.get("new_value", "")
        target = a.get("employee_id") or emp
        act = lc.propose(target, f, v, requester=emp,
                         effective=a.get("effective_date"))
        notes.append(act.id)
        return Result(lc.status_text(act))

    obj = {"type": "object"}
    return [
        Tool("get_my_record", "read", "Read the employee's"
             " HartwellOne record, open actions and actions"
             " closed in the last 7 days.",
             {**obj, "properties": {}}, my_record),
        Tool("propose_change", "write", "Propose a change to"
             " one field: home_address or bank_account."
             " employee_id defaults to the signed-in employee."
             " effective_date (YYYY-MM-DD) only if the"
             " employee says the change starts later.",
             {**obj, "properties": {
                 "field": {"type": "string"},
                 "new_value": {"type": "string"},
                 "employee_id": {"type": "string"},
                 "effective_date": {"type": "string"}},
              "required": ["field", "new_value"]}, propose),
        base["hand_off"],
    ]


# Level 1: unit checks for the three fixes (no model) -------
def unit_checks() -> list[tuple[str, str, bool]]:
    out = []

    def fresh():
        return Lifecycle3(HartwellOne(), Clock(),
                          managers={ch14.LENA: "HW-012927"})
    lc = fresh()
    a = lc.propose(ch14.TOMAS, "home_address",
                   "77 Elm Court, Littleton, CO 80120",
                   ch14.TOMAS, effective="2027-07-01")
    out.append(("F1-a", "future address waits for a person",
                a.state == "awaiting_approval"
                and not lc.hris.audit))
    b = lc.propose(ch14.TOMAS, "home_address",
                   "77 Elm Court, Littleton, CO 80120",
                   ch14.TOMAS, effective="2027-07-01")
    out.append(("F1-b", "repeat future request, one action",
                b.id == a.id))
    c = fresh().propose(ch14.LENA, "home_address", ch14.NEW,
                        ch14.LENA, effective="2027-05-18")
    out.append(("F1-c", "same-day address still by rule",
                c.state == "done"))
    d = fresh().propose(ch14.LENA, "home_address", ch14.NEW,
                        ch14.TOMAS, effective="2027-07-01")
    out.append(("F1-d", "future change to another's record",
                d.state == "denied"))
    lc = fresh()
    e = lc.propose(ch14.LENA, "bank_account",
                   "Front Range CU ****7731", ch14.LENA)
    lc.approve(e.id, ch20day.PAY, "payroll_ops",
               callback_done=True)
    lc.clock.advance(3)
    lc.sweep()
    out.append(("F2-a", "approved change sent within 5 min",
                e.state == "done"))
    lc = fresh()
    f = lc.propose(ch14.LENA, "bank_account",
                   "Front Range CU ****7731", ch14.LENA)
    lc.approve(f.id, ch20day.PAY, "payroll_ops",
               callback_done=True)
    lc.clock.advance(241)
    lc.sweep()
    out.append(("F2-b", "expired approval in payroll queue",
                f.state == "expired"
                and f.id in queue3(lc)))
    lc = fresh()
    g = lc.propose(ch14.LENA, "home_address", ch14.NEW,
                   ch14.LENA)
    notes: list = []
    read = kit3(lc, ch14.LENA, notes)[0].handler({})
    out.append(("F3-a", "read shows a change closed today",
                g.id in read.text.split("Closed")[1]))
    lc.clock.advance(8 * 24 * 60)
    read = kit3(lc, ch14.LENA, notes)[0].handler({})
    out.append(("F3-b", "read drops it after 7 days",
                g.id not in read.text))
    return out


def unit_main() -> None:
    rec = RunRecorder("ch22", "release_unit")
    res = unit_checks()
    for cid, what, ok in res:
        rec.print(f"{cid} {'pass' if ok else 'FAIL'}  {what}")
    rec.print(f"{sum(ok for *_, ok in res)} of {len(res)} pass")
    rec.note(checks=res)
    print(rec.save())


# Level 2: the golden set, with the release -----------------
def cases() -> dict:
    changes = dict(V11)
    g = golden(changes)
    g["G18"]["expect"]["actions"] = G18_V3[1]
    return g


def play(rec, case: dict) -> dict:
    emp = case["emp"]
    lc = Lifecycle3(HartwellOne(), Clock(),
                    managers={ch14.LENA: "HW-012927"})
    if case.get("faults"):
        lc.hris.inject(*case["faults"], emp=emp)
    calls: list = []
    out = run(rec, ch14.SYSTEM.format(emp=emp),
              kit3(lc, emp, calls), case["ask"], Budget())
    seen = {"emp": emp, "reply": out.final_text,
            "handoff": "handoff" in calls,
            "writes": len(lc.hris.audit),
            "actions": [(a.kind, a.state, a.emp, a.dispatches)
                        for a in lc.actions.values()]}
    return {"seen": seen, "grade": grade(case, seen)}


def suite_main(k: int = 3) -> None:
    rec = RunRecorder("ch22", "release_suite")
    cs = cases()
    rec.print(f"Golden set v1.1 + G18 for matrix v3, {len(cs)}"
              f" cases x {k} runs, release with F1 to F3")
    res: dict[str, list] = {c: [] for c in cs}
    for i in range(1, k + 1):
        for cid, case in cs.items():
            r = play(rec, case)
            res[cid].append(r)
            g = r["grade"]
            rec.print(f"run{i} {cid} " + ("pass" if g["pass"]
                      else "FAIL " + ",".join(g["fails"])))
            rec.note(run=i, case=cid, seen=r["seen"], grade=g)
    once = allk = 0
    block = {"STATE", "WRITES", "OWN", "HANDOFF", "RETRY"}
    blocking = []
    rec.print("=== by case")
    for cid, rs in res.items():
        p = sum(r["grade"]["pass"] for r in rs)
        once, allk = once + p, allk + (p == k)
        fails = sorted({f for r in rs for f in
                        r["grade"]["fails"]})
        if block & set(fails):
            blocking.append(cid)
        rec.print(f"{cid} {p}/{k}" + (f"  {','.join(fails)}"
                                      if fails else ""))
    n = len(cs)
    rec.print(f"pass@1 {once}/{n * k} ({once / (n * k):.0%});"
              f" pass^{k} {allk}/{n} ({allk / n:.0%})")
    rec.print("blocking failures: " + (", ".join(blocking)
                                       or "none"))
    rec.note(summary={"pass1": [once, n * k],
                      "passk": [allk, n],
                      "blocking": blocking})
    print(rec.save())


# Level 3: the shared day, with the release -----------------
def day_main() -> None:
    rec = RunRecorder("ch22", "release_day")
    clock = Clock("2027-05-18T09:00")
    lc = Lifecycle3(HartwellOne(seed=ch20day.seed()), clock,
                    managers={ch14.LENA: "HW-012927"})
    told: list[tuple] = []

    def at(t):
        clock.t = clock.t.replace(hour=int(t[:2]),
                                  minute=int(t[3:]))

    def sweep(t):
        at(t)
        for line in lc.sweep():
            rec.print(f"{t} dispatcher: {line}")
    events = {
        "10:30": lambda: ch20day.payroll(rec, lc, clock,
                                         "10:30",
                                         {ch14.TOMAS}),
        "10:35": lambda: sweep("10:35"),
        "13:00": lambda: ch20day.payroll(rec, lc, clock,
                                         "13:00", {ch14.LENA}),
        "13:05": lambda: sweep("13:05"),
        "17:30": lambda: sweep("17:30")}
    pending = sorted(events)
    for t, emp, msg in ch20day.DAY:
        while pending and pending[0] < t:
            events[pending.pop(0)]()
        at(t)
        if ch20day.OUTAGE[0] <= t < ch20day.OUTAGE[1]:
            lc.hris.inject("drop", "drop", emp=emp)
        calls: list = []
        out = run(rec, ch14.SYSTEM.format(emp=emp),
                  kit3(lc, emp, calls), msg, Budget())
        touched = [lc.actions[x] for x in dict.fromkeys(calls)
                   if x in lc.actions]
        shown = touched or [a for a in lc.actions.values()
                            if a.emp == emp]
        st = ", ".join(f"{a.id} {a.state}" for a in shown) \
            or "no action"
        rec.print(f"{t} {emp} {st}"
                  + (" | hand_off" if "handoff" in calls
                     else ""))
        ch14.say(rec, out.final_text)
        if ch14.says_done(out.final_text):
            told.append((t, emp, [a.state for a in shown]))
        rec.note(at=t, emp=emp, reply=out.final_text,
                 actions=[(a.id, a.kind, a.state)
                          for a in shown])
    for t in pending:
        events[t]()
    # Chapter 20's reconciliation, with F2's queues counted
    ch20day.adviser_queue, keep = queue3, ch20day.adviser_queue
    try:
        ch20day.reconcile(rec, lc, told)
    finally:
        ch20day.adviser_queue = keep
    print(rec.save())


if __name__ == "__main__":
    {"unit": unit_main, "suite": suite_main,
     "day": day_main}[sys.argv[1] if len(sys.argv) > 1
                      else "unit"]()
