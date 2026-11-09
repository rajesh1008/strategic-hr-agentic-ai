"""Chapter 29: what happens when a model calculates pay.

Book section "Rules calculate, the agent explains". The same
24 timesheets as the deterministic rule, given to a model
one at a time with the full rule written out in words, as a
pay copilot would be. The model is asked for the gross pay.
Code compares each answer with the rule, to the cent.

This is the design the chapter rejects. It is run so the
rejection rests on a record rather than on a belief.

Run:  python -m chapters.ch29_pay.model_calc
      (needs ANTHROPIC_API_KEY; writes runs/ch29/model_calc/)
"""
from __future__ import annotations

import re
from decimal import Decimal as D

from hrai.llm import RunRecorder, model
from .rules import compute
from .sheets import sheets

THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SYSTEM = (
    "You are a payroll assistant for Hartwell. Compute gross"
    " pay for one weekly timesheet under these rules (US-PAY"
    " v1.2).\n"
    "1. Straight-time pay = all hours x base rate + night"
    " hours x night premium + weekly bonus.\n"
    "2. Regular rate = straight-time pay / total hours,"
    " rounded to 4 decimals.\n"
    "3. TX: overtime hours = hours over 40 in the week.\n"
    "4. CO: overtime hours = the greater of hours over 40 in"
    " the week and the total of hours over 12 in each day.\n"
    "5. CA: daily overtime = hours over 8 and up to 12 in"
    " each day; double time = hours over 12 in each day;"
    " weekly overtime = hours over 40 among hours that are"
    " not daily overtime or double time; overtime hours ="
    " daily overtime + weekly overtime.\n"
    "6. Overtime premium = overtime hours x 0.5 x regular"
    " rate. Double-time premium = double-time hours x 1.0 x"
    " regular rate.\n"
    "7. Round each amount to the cent, half up. Gross ="
    " straight-time pay + premiums.\n"
    "End your reply with one line: GROSS: $<amount>")
ANS = re.compile(r"GROSS:\s*\$?\s*([\d,]+\.\d{2})")


def card(s) -> str:
    days = ", ".join(f"{d} {h}" for d, h in zip(DAYS, s.days))
    return (f"Employee {s.emp}, state {s.state}\n"
            f"Base rate ${s.base}/h\nHours: {days}\n"
            f"Night hours {s.night}, night premium "
            f"${s.premium}/h\nWeekly bonus ${s.bonus}")


def main() -> None:
    rec = RunRecorder("ch29", "model_calc")
    right = 0
    rows = sheets()
    for s in rows:
        truth = compute(s).gross
        kw = {}
        if model() in THINK:
            kw["thinking"] = THINK[model()]
        resp = rec.create(max_tokens=2500, system=SYSTEM,
                          messages=[{"role": "user",
                                     "content": card(s)}], **kw)
        text = "".join(b.text for b in resp.content
                       if b.type == "text")
        m = ANS.findall(text)
        got = D(m[-1].replace(",", "")) if m else None
        ok = got == truth
        right += ok
        diff = "" if got is None else f"{got - truth:+}"
        rec.print(f"{s.emp} rule {truth:>8} model "
                  f"{str(got):>8} {'ok' if ok else 'WRONG'}"
                  f" {'' if ok else diff}".rstrip())
        rec.note(emp=s.emp, truth=str(truth),
                 got=None if got is None else str(got), ok=ok)
    rec.print(f"right to the cent: {right} of {len(rows)}")
    print(rec.save())


if __name__ == "__main__":
    main()
