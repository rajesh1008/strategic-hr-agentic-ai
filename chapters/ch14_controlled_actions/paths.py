"""Every path through the lifecycle, run once (no model).

Book section: "Five ways a write goes wrong". Twelve short
cases against the fake HartwellOne, each printed as its
ledger: the complete, approve and refuse paths, then every
partial failure the chapter names. The last case repeats a
lost reply against a system that ignores idempotency keys,
once with a blind retry and once with the lifecycle.

Run: python -m chapters.ch14_controlled_actions.paths
"""
from __future__ import annotations

from hrai.llm import RunRecorder
from .actions import MATRIX, Lifecycle, idem_key
from .fakes import Clock, HartwellOne, Timeout

LENA, DIEGO, TOMAS = "HW-012771", "HW-019044", "HW-015118"
MGR = {LENA: "HW-012927"}
PAY = "HYD-PAY-0117"            # payroll operations, Hyderabad
NEW = "2240 Larimer Street, Apt 5, Denver, CO 80205"
BANK = "Front Range CU ****7731"


def show(rec, title: str, lc: Lifecycle, *ids: str) -> None:
    rec.print(f"== {title}")
    for aid in ids:
        a = lc.actions[aid]
        writes = len([c for c in lc.hris.audit
                      if c["action_id"] == aid])
        rec.print(f"{a.id} {a.kind}: {a.state.upper()}"
                  f" | writes {writes}")
        for t, step, by, d in a.steps:
            rec.print(f"  {t} {step:<9}{d}")


def fresh(start: str = "2027-05-18T09:00", **kw):
    c = Clock(start)
    return c, Lifecycle(HartwellOne(**kw), c, managers=MGR)


def main() -> None:
    rec = RunRecorder("ch14", "paths")
    rec.print(f"== Approval matrix v{MATRIX['version']}")
    for name, r in MATRIX["actions"].items():
        who = r["approver"]
        if who == "person":
            who = "/".join(r["approver_roles"]) + " + " + \
                "/".join(r["requires"])
        ttl = r.get("approval_ttl_min", "-")
        rec.print(f"  {name:<19}{who:<29}{ttl}")
    c, lc = fresh()
    a = lc.propose(LENA, "home_address", NEW, LENA)
    show(rec, "P1 complete: address change", lc, a.id)

    c, lc = fresh()
    a = lc.propose(LENA, "bank_account", BANK, LENA)
    lc.approve(a.id, LENA, "payroll_ops", callback_done=True)
    lc.approve(a.id, MGR[LENA], "payroll_ops",
               callback_done=True)
    lc.approve(a.id, PAY, "payroll_ops")
    c.advance(25)
    lc.approve(a.id, PAY, "payroll_ops", callback_done=True)
    lc.dispatch(a.id)
    show(rec, "P2 approve: bank-detail change", lc, a.id)
    rec.print(f"  notices sent: {len(lc.hris.notices)}"
              " (old and new contact)")

    c, lc = fresh()
    a = lc.propose(LENA, "base_pay", "USD 36.50/h", LENA)
    b = lc.propose(DIEGO, "bank_account", BANK, LENA)
    show(rec, "P3 refuse: pay rate; another's record", lc,
         a.id, b.id)

    c, lc = fresh()
    lc.hris.inject("lose_reply")
    a = lc.propose(TOMAS, "home_address",
                   "90 Rampart Way, Aurora, CO 80011", TOMAS)
    show(rec, "P4 unknown receipt, write landed", lc, a.id)

    c, lc = fresh()
    lc.hris.inject("drop")
    a = lc.propose(TOMAS, "home_address",
                   "90 Rampart Way, Aurora, CO 80011", TOMAS)
    show(rec, "P5 unknown receipt, nothing written", lc, a.id)

    c, lc = fresh()
    lc.hris.inject("drop", "drop")
    a = lc.propose(TOMAS, "home_address",
                   "90 Rampart Way, Aurora, CO 80011", TOMAS)
    show(rec, "P6 unknown twice", lc, a.id)

    c, lc = fresh()
    a = lc.propose(LENA, "home_address", NEW, LENA)
    c.advance(3)
    b = lc.propose(LENA, "home_address",
                   NEW.replace("Street", "St"), LENA)
    show(rec, "P7 duplicate request", lc, a.id)
    rec.print(f"  second proposal returned {b.id}")

    c, lc = fresh()
    a = lc.propose(LENA, "bank_account", BANK, LENA)
    lc.approve(a.id, PAY, "payroll_ops", callback_done=True)
    c.advance(40)
    lc.revoke(a.id, PAY, "employee says she did not ask")
    lc.dispatch(a.id)
    show(rec, "P8 approval revoked before dispatch", lc, a.id)

    c, lc = fresh()
    a = lc.propose(LENA, "bank_account", BANK, LENA)
    lc.approve(a.id, PAY, "payroll_ops", callback_done=True)
    c.advance(270)
    lc.dispatch(a.id)
    show(rec, "P9 approval expired", lc, a.id)

    c, lc = fresh()
    lc.hris.inject("overwrite")
    a = lc.propose(LENA, "home_address", NEW, LENA)
    show(rec, "P10 readback mismatch", lc, a.id)
    rec.print("  record now: "
              + lc.hris.read(LENA)["home_address"][:40])

    c, lc = fresh()
    lc.hris.inject("normalize")
    a = lc.propose(LENA, "home_address", NEW, LENA)
    show(rec, "P11 system rewrites the value", lc, a.id)
    rec.print("  stored: " + lc.hris.read(LENA)["home_address"])
    rec.print(f"  exact compare would say: "
              f"{lc.hris.read(LENA)['home_address'] == NEW}")

    c, lc = fresh()
    a = lc.propose(LENA, "home_address", NEW, LENA)
    c.advance(90)
    r = lc.reverse(a.id, "HR-DEN-ADV-031",
                   "employee typed the wrong unit")
    b = lc.propose(LENA, "bank_account", BANK, LENA)
    lc.approve(b.id, PAY, "payroll_ops", callback_done=True)
    lc.dispatch(b.id)
    rb = lc.reverse(b.id, "HR-DEN-ADV-031",
                    "change was not the employee's")
    show(rec, "P12 reversal is a new action", lc, r.id, rb.id)

    rec.print("== P13 lost reply, system ignores keys")
    for mode in ("blind retry", "lifecycle"):
        c, lc = fresh(honor_keys=False)
        lc.hris.inject("lose_reply")
        if mode == "blind retry":
            k = idem_key(LENA, "bank_account", BANK)
            for _ in range(2):
                try:
                    lc.hris.write(LENA, "bank_account", BANK,
                                  actor="agent", action_id="X",
                                  key=k)
                    break
                except Timeout:
                    continue
        else:
            a = lc.propose(LENA, "bank_account", BANK, LENA)
            lc.approve(a.id, PAY, "payroll_ops",
                       callback_done=True)
            lc.dispatch(a.id)
        rec.print(f"  {mode:<12} writes "
                  f"{len(lc.hris.audit)}, change notices "
                  f"{len(lc.hris.notices)}")
    rec.save()


if __name__ == "__main__":
    main()
