"""Chapter 29: synthetic weekly timesheets (seed 29).

Twenty-four hourly employees of Hartwell Energy Services
(Texas and Colorado) and Hartwell US facilities (California),
one week each, with the patterns that make overtime hard by
hand: night premiums, a weekly bonus, long days, short days.
Rosa Elizondo (HES-40217) is the employee in the chapter's
opening. All synthetic.
"""
from __future__ import annotations

import random
from decimal import Decimal as D

from .rules import Sheet

OPENING_WEEK = Sheet("HES-40217", "TX", D("31.40"),
                [D(12), D(12), D(12), D(12), D(6), D(0), D(0)],
                night=D(48), premium=D("2.75"), bonus=D(150))

# A Colorado night crew: three 14-hour shifts, 6 p.m. to 8 a.m.,
# each split 6 + 8 across the midnight workday boundary. No
# workday reaches 12 hours; each shift is 14 consecutive hours.
NIGHT_CREW_CO = Sheet("HES-CO025", "CO", D("29.60"),
                      [D(6), D(8), D(6), D(8), D(6), D(8), D(0)],
                      night=D(42), premium=D("2.50"),
                      spans=[D(14), D(14), D(14)])



def week(rng: random.Random, state: str) -> list[D]:
    pat = rng.choice(["4x10", "5x8", "4x12", "6x10",
                      "mixed", "5x9"])
    if pat == "4x10":
        d = [10, 10, 10, 10, 0, 0, 0]
    elif pat == "5x8":
        d = [8, 8, 8, 8, 8, 0, 0]
    elif pat == "4x12":
        d = [12, 12, 12, 12, 0, 0, 0]
    elif pat == "6x10":
        d = [10, 10, 10, 10, 10, 6, 0]
    elif pat == "5x9":
        d = [9, 9, 9, 9, 9, 0, 0]
    else:
        d = [rng.choice([8, 9.5, 10, 11, 13]) for _ in range(5)]
        d += [rng.choice([0, 4, 6]), 0]
    return [D(str(h)) for h in d]


def sheets() -> list[Sheet]:
    rng = random.Random(29)
    out = []
    plan = ["TX"] * 12 + ["CO"] * 6 + ["CA"] * 6
    for i, st in enumerate(plan, 1):
        days = week(rng, st)
        hours = sum(days, D(0))
        base = D(str(rng.choice([24.10, 27.85, 29.60,
                                 31.40, 33.25, 36.90])))
        night = D(0)
        prem = D(0)
        if rng.random() < 0.6:
            night = min(hours, D(rng.choice([20, 30, 40])))
            prem = D(str(rng.choice([1.75, 2.50, 2.75])))
        bonus = D(rng.choice([0, 0, 100, 150, 200]))
        pre = {"TX": "HES", "CO": "HES", "CA": "HWF"}[st]
        out.append(Sheet(f"{pre}-{st}{i:03d}", st, base, days,
                         night, prem, bonus))
    return out
