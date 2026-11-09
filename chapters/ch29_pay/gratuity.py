"""Chapter 29: end-of-service gratuity as a rule.

Book section "Ghafline Facilities Services: the gratuity".
UAE: a full-time foreign worker with a year or more of
continuous service receives 21 days' basic wage for each of
the first five years and 30 days for each year after, the
total capped at two years' wage (Federal Decree-Law 33 of
2021, Art 51). Saudi Arabia: half a month's wage for each of
the first five years and a month for each year after, cut
to a third, two thirds or nothing on resignation by length
of service (Labor Law Arts 84 and 85). The book marks both
[VERIFY] until counsel signs the reading. Days of unpaid
leave are not service; part years count pro rata; a day's
basic wage is the monthly basic / 30.

The comparison replays Ghafline's 2027 Dubai leavers through
the rule and through the payroll spreadsheet it replaced.
All synthetic.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch29_pay.gratuity
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal as D

from hrai.llm import RunRecorder

AED_PER_USD = D("3.6725")


def money(x: D) -> D:
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def service_years(start: date, end: date, unpaid: int) -> D:
    days = (end - start).days + 1 - unpaid
    return (D(days) / D(365)).quantize(D("0.0001"),
                                       ROUND_HALF_UP)


def uae(basic: D, years: D) -> D:
    """Art 51: 21 days a year to five, 30 after, cap 24 m."""
    if years < 1:
        return D(0)
    day = basic / 30
    first = min(years, D(5)) * 21 * day
    later = max(years - 5, D(0)) * 30 * day
    return money(min(first + later, basic * 24))


def saudi(wage: D, years: D, resigned: bool) -> D:
    """Arts 84 and 85: half a month to five, a month after."""
    full = (min(years, D(5)) * wage / 2
            + max(years - 5, D(0)) * wage)
    if resigned:
        if years < 2:
            return D(0)
        share = (D(1) / 3 if years < 5 else
                 D(2) / 3 if years < 10 else D(1))
        full = full * share
    return money(full)


@dataclass
class Leaver:
    wid: str
    start: date
    end: date
    unpaid: int      # days of unpaid leave in service
    basic: D         # last monthly basic, AED
    basic_hire: D    # basic on the original contract


def leavers(n: int = 214) -> list[Leaver]:
    rng = random.Random(2927)
    out = []
    for i in range(1, n + 1):
        yrs = rng.choice([1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8,
                          9, 11, 13])
        end = date(2027, rng.randint(1, 12), rng.randint(1, 28))
        start = date(end.year - yrs, rng.randint(1, 12),
                     rng.randint(1, 28))
        hire = D(rng.choice([1100, 1250, 1400, 1600, 2000,
                             2500, 3200]))
        raised = rng.random() < 0.35 and yrs >= 3
        basic = hire + (D(rng.choice([150, 200, 300]))
                        if raised else 0)
        unpaid = rng.choice([0] * 7 + [14, 30, 45, 60])
        out.append(Leaver(f"GF-DXB-{i:04d}", start, end,
                          unpaid, basic, hire))
    return out


def spreadsheet(l: Leaver) -> D:
    """The 2019 sheet: 21 days for every year, all calendar
    days as service, the basic on the original contract."""
    yrs = service_years(l.start, l.end, 0)
    if yrs < 1:
        return D(0)
    return money(min(yrs * 21 * l.basic_hire / 30,
                     l.basic_hire * 24))


def usd(aed: D) -> str:
    return f"{(aed / AED_PER_USD):,.0f}"


def main() -> None:
    rec = RunRecorder("ch29", "gratuity")
    rows = leavers()
    under = over = same = 0
    owed = paid_over = D(0)
    cause = {"after year 5": 0, "unpaid leave": 0,
             "old basic": 0}
    worst = None
    for l in rows:
        yrs = service_years(l.start, l.end, l.unpaid)
        rule = uae(l.basic, yrs)
        old = spreadsheet(l)
        d = rule - old
        if d > D("0.5"):
            under += 1
            owed += d
            if worst is None or d > worst[1]:
                worst = (l, d, rule, old, yrs)
        elif d < D("-0.5"):
            over += 1
            paid_over -= d
        else:
            same += 1
        if yrs > 5:
            cause["after year 5"] += 1
        if l.unpaid:
            cause["unpaid leave"] += 1
        if l.basic != l.basic_hire:
            cause["old basic"] += 1
    rec.print("Ghafline Facilities, Dubai: 2027 leavers, "
              "gratuity")
    rec.print(f"leavers {len(rows)}; rule = spreadsheet "
              f"{same}; spreadsheet short {under}; "
              f"spreadsheet over {over}")
    rec.print(f"short by AED {owed:,.0f} (about US$"
              f"{usd(owed)}); over by AED {paid_over:,.0f}")
    for k, v in cause.items():
        rec.print(f"  leavers affected by {k}: {v}")
    l, d, rule, old, yrs = worst
    rec.print(f"largest: {l.wid} {yrs} years, basic AED "
              f"{l.basic:,} (hire {l.basic_hire:,}), unpaid "
              f"{l.unpaid} days")
    rec.print(f"  rule AED {rule:,} sheet AED {old:,} "
              f"short AED {d:,}")
    rec.note(leavers=len(rows), same=same, under=under,
             over=over, owed=str(owed),
             paid_over=str(paid_over), causes=cause)
    sa = saudi(D(4000), D(7), resigned=True)
    rec.print(f"Saudi check: SAR 4,000, 7 years, resigned: "
              f"SAR {sa:,}")
    print(rec.save())


if __name__ == "__main__":
    main()
