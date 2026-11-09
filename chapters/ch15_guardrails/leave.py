"""Leave conditions computed from the calendar (Chapter 3 gap).

Book section: "Closing the split-request gap". Version 2.1
checked each request alone, so five days asked for as three
and two passed the rule. Version 2.2 counts the run of
consecutive working days off, joining the person's own
adjacent bookings across weekends and holidays.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import yaml

DATA = Path(__file__).parent / "data" / "leave.yaml"


def d(s: str) -> date:
    return date.fromisoformat(s)


class Calendar:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or yaml.safe_load(DATA.read_text())
        self.hol = set(self.cfg["holidays"])
        self.booked = [dict(b) for b in self.cfg["existing"]]
        self.bal = {k: dict(v) for k, v in
                    self.cfg["balances"].items()}

    def working(self, x: date) -> bool:
        return x.weekday() < 5 and x.isoformat() not in self.hol

    def days(self, a: str, b: str) -> list[date]:
        out, x = [], d(a)
        while x <= d(b):
            if self.working(x):
                out.append(x)
            x += timedelta(days=1)
        return out

    def off(self, emp: str) -> set[date]:
        return {x for b in self.booked if b["employee"] == emp
                for x in self.days(b["start"], b["end"])}

    def run(self, emp: str, a: str, b: str) -> int:
        """Working days in the longest unbroken run off."""
        off = self.off(emp) | set(self.days(a, b))
        lo, hi = d(a), d(b)
        while True:                 # walk back over gaps
            x = lo - timedelta(days=1)
            while not self.working(x) and x > lo - timedelta(9):
                x -= timedelta(days=1)
            if x in off:
                lo = x
            else:
                break
        while True:                 # walk forward
            x = hi + timedelta(days=1)
            while not self.working(x) and x < hi + timedelta(9):
                x += timedelta(days=1)
            if x in off:
                hi = x
            else:
                break
        return len([x for x in off if lo <= x <= hi])

    def crew_ok(self, a: str, b: str) -> bool:
        spare = self.cfg["crew_size"] - \
            self.cfg["minimum_on_shift"]
        for x in self.days(a, b):
            n = sum(1 for bk in self.booked
                    if x in self.days(bk["start"], bk["end"]))
            if n + 1 > spare:
                return False
        return True

    def book(self, emp: str, a: str, b: str) -> None:
        self.booked.append({"employee": emp, "start": a,
                            "end": b})
        self.bal[emp]["vacation"] -= len(self.days(a, b))


def conditions(cal: Calendar, today: str) -> dict:
    n = lambda r: len(cal.days(r["start"], r["end"]))
    return {
        "vacation": lambda r: r["type"] == "vacation",
        "sick": lambda r: r["type"] == "sick",
        "request_le_3_days": lambda r: n(r) <= 3,
        "run_le_3_days": lambda r: cal.run(
            r["employee"], r["start"], r["end"]) <= 3,
        "notice_ge_7_days": lambda r: (
            d(r["start"]) - d(today)).days >= 7,
        "within_balance": lambda r: n(r) <= cal.bal[
            r["employee"]]["vacation"],
        "crew_at_minimum": lambda r: cal.crew_ok(
            r["start"], r["end"]),
    }
