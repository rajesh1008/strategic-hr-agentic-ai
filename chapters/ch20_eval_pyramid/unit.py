"""Level 1: unit checks, and the faults that test them.

Book section: "Level 1: checks that need no model". Every
deterministic part of the service agent gets a check that
runs in milliseconds with no model: the approval matrix, the
lifecycle's failure paths, the idempotency key, readback and
the reply phrase check. Then the checks are tested in turn:
each mutant below breaks one part of the code on purpose, and
a check that fails under the mutant has "killed" it. A mutant
that no check kills is a hole in the suite, not in the agent.

Run: HRAI_MODEL=no-model python -m \\
     chapters.ch20_eval_pyramid.unit
"""
from __future__ import annotations

import time
from contextlib import contextmanager

from chapters.ch14_controlled_actions import actions as A
from chapters.ch14_controlled_actions import agent as ag
from chapters.ch14_controlled_actions.fakes import (Clock,
                                                    HartwellOne)
from hrai.llm import RunRecorder

LENA, DIEGO, MGR = "HW-012771", "HW-019044", "HW-012927"
NEW = "2240 Larimer Street, Apt 5, Denver, CO 80205"
BANK = "Front Range CU ****7731"
PAY = "HYD-PAY-0117"


def lc(*faults):
    c = Clock()
    life = A.Lifecycle(HartwellOne(), c, managers={LENA: MGR})
    if faults:
        life.hris.inject(*faults, emp=LENA)
    return c, life


def addr(*faults):
    c, life = lc(*faults)
    return life, life.propose(LENA, "home_address", NEW, LENA)


def bank():
    c, life = lc()
    return c, life, life.propose(LENA, "bank_account", BANK,
                                 LENA)


def _approved(c, life, a):
    life.approve(a.id, PAY, "payroll_ops", callback_done=True)
    return a


def u12():
    life, a = addr("lose_reply")
    return (a.state == "done" and len(life.hris.audit) == 1
            and any("lookup" in s[3] for s in a.steps))


def u13():
    c = Clock()
    life = A.Lifecycle(HartwellOne(honor_keys=False), c)
    life.hris.inject("lose_reply", emp=LENA)
    a = life.propose(LENA, "home_address", NEW, LENA)
    return a.state == "done" and len(life.hris.audit) == 1


def u09():
    c, life, a = bank()
    _approved(c, life, a)
    c.advance(241)
    return life.dispatch(a.id).state == "expired"


def u11():
    c, life, a = bank()
    _approved(c, life, a)
    life.dispatch(a.id)
    life.revoke(a.id, PAY, "changed mind")
    return a.state == "done"


def u18():
    c, life = lc()
    a = life.propose(LENA, "home_address", NEW, LENA)
    b = life.propose(LENA, "home_address", NEW.upper(), LENA)
    return a is b and len(life.hris.audit) == 1


def u24():
    life, a = addr()
    r = life.reverse(a.id, "HR-DEN-ADV-031", "wrong address")
    return (r.state == "done" and r.reverses == a.id
            and life.hris.read(LENA)["home_address"]
            == a.before)


def refused(who, role="payroll_ops", **chk):
    c, life, a = bank()
    life.approve(a.id, who, role, **chk)
    return a.state == "awaiting_approval"


CHECKS = {
    "U01 own address, valid: done, 1 write":
        lambda: (lambda l, a: a.state == "done"
                 and len(l.hris.audit) == 1)(*addr()),
    "U02 address with no ZIP: denied":
        lambda: lc()[1].propose(LENA, "home_address",
                                "12 Clarkson St, Denver",
                                LENA).state == "denied",
    "U03 bank change: awaiting approval":
        lambda: bank()[2].state == "awaiting_approval",
    "U04 requester cannot approve":
        lambda: refused(LENA, callback_done=True),
    "U05 agent cannot approve":
        lambda: refused("svc-askhartwell-agent",
                        callback_done=True),
    "U06 requester's manager cannot approve":
        lambda: refused(MGR, callback_done=True),
    "U07 no callback, no approval":
        lambda: refused(PAY),
    "U08 payroll with callback: done":
        lambda: (lambda c, l, a: _approved(c, l, a)
                 and l.dispatch(a.id).state == "done")(*bank()),
    "U09 approval expires after 240 min": u09,
    "U10 revoke before dispatch":
        lambda: (lambda c, l, a: l.revoke(a.id, PAY, "x").state
                 == "revoked")(*bank()),
    "U11 no revoke after dispatch": u11,
    "U12 lost reply: done by lookup, 1 write": u12,
    "U13 lost reply, keys ignored: 1 write": u13,
    "U14 two timeouts: needs person, 0 writes":
        lambda: (lambda l, a: a.state == "needs_person"
                 and not l.hris.audit)(*addr("drop", "drop")),
    "U15 overwrite: mismatch, sent once":
        lambda: (lambda l, a: a.state == "mismatch"
                 and a.dispatches == 1)(*addr("overwrite")),
    "U16 HartwellOne rejects: failed":
        lambda: addr("reject")[1].state == "failed",
    "U17 postal form stored: done (normalized)":
        lambda: addr("normalize")[1].state == "done",
    "U18 same request twice: 1 action, 1 write": u18,
    "U19 pay rate: denied":
        lambda: lc()[1].propose(LENA, "base_pay", "34.00",
                                LENA).state == "denied",
    "U20 another person's record: denied":
        lambda: lc()[1].propose(DIEGO, "bank_account", BANK,
                                LENA).state == "denied",
    "U21 phrase check: 'has been updated' is done":
        lambda: ag.says_done("Your address has been updated."),
    "U22 phrase check: 'once payroll approves' is not":
        lambda: not ag.says_done(
            "Not changed yet: it will be saved once payroll"
            " approves."),
    "U23 waiting status says 'not changed yet'":
        lambda: "not changed yet" in (lambda c, l, a:
                                      l.status_text(a))(*bank()),
    "U24 reversal is a new action, before restored": u24,
}


# Mutants: one deliberate fault each ---------------------------
def _rb_always(self, a):
    a.state = "done"
    return a


def _settle_blind(self, a):
    if a.dispatches < 2:
        return self._send(a)
    return self._end(a, "needs_person", "receipt",
                     "lifecycle", "two unknown receipts")


_real_rb = A.Lifecycle.readback


def _rb_retry(self, a):
    a = _real_rb(self, a)
    if a.state == "mismatch" and a.dispatches < 2:
        a.state = "approved"
        return self._send(a)
    return a


def _status_vague(self, a):
    return f"{a.id} {a.field}: submitted"


def _key_raw(emp, fld, value):
    return "IK-" + str(abs(hash((emp, fld, value))))[:10]


MUTANTS = {
    "M1 readback always says it matches":
        [(A.Lifecycle, "readback", _rb_always)],
    "M2 unknown receipt resent without lookup":
        [(A.Lifecycle, "_settle", _settle_blind)],
    "M3 matrix forgets who may never approve":
        [("bank_detail_change", "not_approver", [])],
    "M4 approval window typed as 100,000 min":
        [("bank_detail_change", "approval_ttl_min", 100000)],
    "M5 mismatch retried once":
        [(A.Lifecycle, "readback", _rb_retry)],
    "M6 phrase check ignores negation":
        [(ag, "HEDGE", __import__("re").compile(r"(?!x)x"))],
    "M7 waiting status reads 'submitted'":
        [(A.Lifecycle, "status_text", _status_vague)],
    "M8 address rule drops the ZIP check":
        [("address_change", "rule",
          ["own_record", "session_verified"])],
    "M9 'own record only' row check removed":
        [("bank_detail_change", "requester", "any")],
    "M10 key built from the raw value":
        [(A, "idem_key", _key_raw)],
    "M11 address row: 'own record only' removed":
        [("address_change", "requester", "any")],
}


@contextmanager
def mutant(patches):
    saved = []
    for obj, name, new in patches:
        if isinstance(obj, str):
            row = A.MATRIX["actions"][obj]
            saved.append((row, name, row.get(name)))
            row[name] = new
        else:
            saved.append((obj, name, getattr(obj, name)))
            setattr(obj, name, new)
    try:
        yield
    finally:
        for obj, name, old in reversed(saved):
            if isinstance(obj, dict):
                obj[name] = old
            else:
                setattr(obj, name, old)


def run_checks() -> dict[str, bool]:
    out = {}
    for name, fn in CHECKS.items():
        try:
            out[name] = bool(fn())
        except Exception:
            out[name] = False
    return out


def main() -> None:
    rec = RunRecorder("ch20", "unit")
    t0 = time.perf_counter()
    base = run_checks()
    ms = (time.perf_counter() - t0) * 1000
    ok = sum(base.values())
    rec.print(f"Level 1 unit checks: {ok} of {len(base)} pass"
              f" ({ms:.0f} ms, no model)")
    for name, good in base.items():
        if not good:
            rec.print(f"  FAILED {name}")
    rec.print("Mutants (each breaks one thing on purpose):")
    killed = 0
    for name, patches in MUTANTS.items():
        with mutant(patches):
            res = run_checks()
        by = [c.split()[0] for c, g in res.items()
              if base[c] and not g]
        killed += bool(by)
        rec.print(f"  {name}")
        rec.print("     killed by " + ", ".join(by) if by
                  else "     SURVIVED: no check failed")
        rec.note(mutant=name, killed_by=by)
    rec.print(f"Mutants killed: {killed} of {len(MUTANTS)}")
    print(rec.save())


if __name__ == "__main__":
    main()
