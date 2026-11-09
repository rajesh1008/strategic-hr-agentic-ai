"""Chapter 29: one payslip, traced rule by rule.

Book section "The deterministic pay rule". Prints the rule
trace for the opening's week (Rosa Elizondo, HES-40217,
Pasadena, Texas), the provider's figure computed the 2019
way, the same trace for one Colorado and one California
week from the seeded timesheets, so the daily rules show, and
a Colorado night-crew week whose shifts cross midnight, so
the consecutive-hours test (US-PAY v1.3) shows.
Each week's hours print under its own header line.
No model is called. All synthetic.

Run:  HRAI_MODEL=no-model python -m chapters.ch29_pay.payslip
"""
from __future__ import annotations

from dataclasses import replace

from hrai.llm import RunRecorder

from . import rules
from .sheets import NIGHT_CREW_CO, OPENING_WEEK, sheets


def main() -> None:
    rec = RunRecorder("ch29", "payslip")
    s = OPENING_WEEK
    r = rules.compute(s)
    for line in rules.trace(s, r):
        rec.print(line)
    old = rules.legacy(s)
    rec.print(f"provider (2019 setup, 1.5 x base)    ${old:>9}")
    rec.print(f"difference: paid ${r.gross - old} less than the rule")
    by_state = {x.state: x for x in reversed(sheets())}
    for st in ("CO", "CA"):
        x = by_state[st]
        x = replace(x, base=rules.money(x.base),
                    premium=rules.money(x.premium))
        rx = rules.compute(x)
        days = " ".join(f"{h:g}" for h in x.days)
        head, *rest = rules.trace(x, rx)
        rec.print(head)
        rec.print(f"hours by day, Monday to Sunday: {days}")
        for line in rest:
            rec.print(line)
        rec.print(f"provider (2019 setup, 1.5 x base)    "
                  f"${rules.legacy(x):>9}")
    n = NIGHT_CREW_CO
    rn = rules.compute(n)
    head, *rest = rules.trace(n, rn)
    rec.print(head)
    rec.print("hours by day, Monday to Sunday: "
              + " ".join(f"{h:g}" for h in n.days))
    rec.print("consecutive hours per shift: "
              + " ".join(f"{h:g}" for h in n.spans))
    for line in rest:
        rec.print(line)
    v12 = rules.compute(replace(n, spans=None))
    rec.print(f"without the consecutive-hours test (v1.2)  "
              f"${v12.gross:>9}")
    rec.print(f"provider (2019 setup, 1.5 x base)    "
              f"${rules.legacy(n):>9}")
    rec.note(gross=str(r.gross), legacy=str(old),
             night_crew_gross=str(rn.gross),
             night_crew_v12=str(v12.gross))
    print(rec.save())


if __name__ == "__main__":
    main()
