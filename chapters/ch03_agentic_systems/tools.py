"""AskHartwell's tools, in two versions (Chapter 3).

Book section: "Read tools and write tools". The read tools
and the route tool are the same in both versions. The write
tools differ:
  direct      book_leave writes to HartwellOne at once, and
              remember keeps any note the model sends.
  controlled  propose_leave goes through the controlled-
              action ledger and Hartwell Gate; remember_
              preference keeps only listed keys, screened.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from hrai import gate
from .action_ledger import Ledger
from .hris import HartwellOne, Timeout, days
from .loop import Result, Tool

HERE = Path(__file__).resolve().parent
POLICY = yaml.safe_load((HERE / "policy.yaml").read_text())
KINDS = ["vacation", "sick"]
PREF_KEYS = ["contact_channel", "language", "preferred_name"]
HEALTH = ("surgery", "hospital", "knee", "doctor", "medical",
          "diagnos", "injur", "therapy", "pregnan", "illness",
          "medication", "condition", "clinic", "appointment")
RETAIN_DAYS = 90


@dataclass
class Session:
    employee: str               # the signed-in employee
    hris: HartwellOne
    ledger: Ledger = field(default_factory=Ledger)
    notes: list[dict] = field(default_factory=list)


def checks(s: Session, start, end, kind) -> dict:
    """The rule's view of a request. Deterministic."""
    cfg = s.hris.cfg
    n = len(days(start, end, cfg["holidays"]))
    today = date.fromisoformat(cfg["as_of"])
    lead = (date.fromisoformat(start) - today).days
    cal = s.hris.crew_calendar(start, end)
    low = [d for d, v in cal.items() if v["on_shift"] - 1
           < cfg["crew"]["minimum_on_shift"]]
    bal = s.hris.balance(s.employee).get(kind, 0)
    sick = kind == "sick"
    return {"days": n, "within_balance": n <= bal,
            "notice_ok": sick or lead >= 7,
            "short_request": n <= 3,
            "staffing_ok": sick or not low,
            "short_staffed_days": [] if sick else low}


def _dates_ok(a: dict) -> str | None:
    try:
        s, e = (date.fromisoformat(a["start"]),
                date.fromisoformat(a["end"]))
    except (KeyError, TypeError, ValueError):
        return "start and end must be YYYY-MM-DD dates."
    if e < s or (e - s).days > 31:
        return "end must be on or after start, within 31 days."
    if a.get("type") not in KINDS:
        return f"type must be one of {KINDS}."
    return None


# ---- read and route tools (both versions) ---------------
def read_tools(s: Session) -> list[Tool]:
    def balance(a):
        if a.get("employee_id") != s.employee:
            return Result("Denied: you may read only the "
                          "signed-in employee's balance.", True)
        return Result(str(s.hris.balance(s.employee)))

    def policy(a):
        p = s.hris.cfg["policy"]
        return Result(
            f"{p['name']} v{p['version']}\n{p['text']}")

    def calendar(a):
        bad = _dates_ok({**a, "type": "vacation"})
        if bad:
            return Result(bad, True)
        cal = s.hris.crew_calendar(a["start"], a["end"])
        return Result("\n".join(
            f"{d}: {v['on_shift']} on shift" for d, v in
            cal.items()) or "no working days in range")

    def hand_off(a):
        return Result("Handed to the HR service team.",
                      stop="human route")

    span = {"type": "object", "properties": {
        "start": {"type": "string"}, "end": {"type": "string"}},
        "required": ["start", "end"]}
    return [
        Tool("get_leave_balance", "read",
             "Leave balances in working days.",
             {"type": "object", "properties": {
                 "employee_id": {"type": "string"}},
              "required": ["employee_id"]}, balance),
        Tool("get_leave_policy", "read",
             "The leave policy that applies to this employee.",
             {"type": "object", "properties": {}}, policy),
        Tool("get_crew_calendar", "read",
             "How many of the crew are on shift each working "
             "day (names withheld). Dates YYYY-MM-DD.",
             span, calendar),
        Tool("hand_off_to_person", "route",
             "Pass the conversation to a person in the HR "
             "service team.",
             {"type": "object", "properties": {
                 "reason": {"type": "string"}},
              "required": ["reason"]}, hand_off),
    ]


LEAVE = {"type": "object", "properties": {
    "start": {"type": "string", "description": "YYYY-MM-DD"},
    "end": {"type": "string", "description": "YYYY-MM-DD"},
    "type": {"type": "string", "enum": KINDS}},
    "required": ["start", "end", "type"]}


# ---- direct write tools ---------------------------------
def direct_tools(s: Session) -> list[Tool]:
    def book(a):
        bad = _dates_ok(a)
        if bad:
            return Result(bad, True)
        try:
            b = s.hris.book(s.employee, a["start"], a["end"],
                            a["type"], by="agent")
        except Timeout as exc:
            return Result(f"Error: {exc}. Outcome unknown.",
                          True)
        return Result(f"Booked {b['ref']}: {b['days']} day(s).")

    def remember(a):
        s.notes.append({"note": str(a.get("note", ""))})
        return Result("Noted for future conversations.")

    return read_tools(s) + [
        Tool("book_leave", "write",
             "Book leave in HartwellOne for the employee.",
             LEAVE, book),
        Tool("remember", "write",
             "Keep a note about the employee for future "
             "conversations.",
             {"type": "object", "properties": {
                 "note": {"type": "string"}},
              "required": ["note"]}, remember),
    ]


# ---- controlled write tools -----------------------------
def propose(s: Session, a: dict) -> Result:
    """Proposal, approval, dispatch, receipt, readback."""
    bad = _dates_ok(a)
    if bad:
        return Result(bad, True)
    p = {"employee": s.employee, "type": a["type"],
         "start": a["start"], "end": a["end"]}
    e = next((x for x in s.ledger.entries if x.proposal == p),
             None)
    if e and e.state().startswith(("done", "awaiting")):
        return Result(f"Already {e.state()}: {e.action_id}.")
    e = e or s.ledger.propose(POLICY["tool"], p)
    ctx = checks(s, a["start"], a["end"], a["type"])
    d = gate.evaluate(POLICY, status="booked", actor="rule",
                      context=ctx)
    if not d.allowed:
        sup = s.hris.cfg["crew"]["supervisor"]
        e.approval = {"approver": f"supervisor {sup}",
                      "approved": False, "failed": d.missing,
                      "policy": d.policy,
                      "version": d.policy_version}
        return Result(
            f"PENDING {e.action_id}: sent to the crew "
            "supervisor "
            f"for approval ({', '.join(d.missing)} not met). "
            "Nothing is booked yet.")
    e.approval = {"approver": "rule", "approved": True,
                  "policy": d.policy,
                  "version": d.policy_version}
    for attempt in (1, 2):
        e.dispatch = {"attempt": attempt}
        try:
            b = s.hris.book(s.employee, p["start"], p["end"],
                            p["type"], by=f"rule:{e.action_id}",
                            idempotency_key=e.key)
            e.receipt = {"status": "confirmed", "ref": b["ref"]}
        except Timeout as exc:
            e.receipt = {"status": "unknown", "error": str(exc)}
        got = s.hris.find(p["employee"], p["start"],
                          p["end"], p["type"])
        e.readback = {"found": len(got),
                      "matches": len(got) == 1}
        if got:
            break               # landed: never dispatch again
    if not e.readback["matches"]:
        return Result(f"FAILED {e.action_id}: not confirmed. "
                      "A person in HR will check.", True,
                      stop="human route")
    ref = got[0]["ref"]
    how = ("confirmed by readback after a timeout"
           if e.receipt["status"] == "unknown" else "confirmed")
    return Result(f"BOOKED {e.action_id} as {ref}: "
                  f"{ctx['days']} day(s), {how}.")


def controlled_tools(s: Session) -> list[Tool]:
    def remember(a):
        k, v = a.get("key"), str(a.get("value", ""))
        if k not in PREF_KEYS:
            return Result(f"Denied: only {PREF_KEYS} may be "
                          "kept.", True)
        if any(w in v.lower() for w in HEALTH):
            return Result("Denied: health details are never "
                          "kept.", True)
        s.notes.append({"key": k, "value": v,
                        "retain_days": RETAIN_DAYS})
        return Result(f"Kept {k} for {RETAIN_DAYS} days.")

    return read_tools(s) + [
        Tool("propose_leave", "write",
             "Propose a leave booking. Hartwell Gate approves "
             "it by rule or sends it to the crew supervisor, "
             "and returns the status.",
             LEAVE, lambda a: propose(s, a)),
        Tool("remember_preference", "write",
             "Keep one contact or language preference for "
             f"future conversations ({RETAIN_DAYS} days).",
             {"type": "object", "properties": {
                 "key": {"type": "string", "enum": PREF_KEYS},
                 "value": {"type": "string"}},
              "required": ["key", "value"]}, remember),
    ]
