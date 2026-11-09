"""A fake HartwellOne leave module (in memory, synthetic).

Book section: "Read tools and write tools". It holds
balances, the crew calendar and bookings. `book()` can be
told to lose its reply once (the write lands, the caller
sees a timeout), which is the partial failure the chapter
uses. Nothing here calls a model or a real system.
"""
from __future__ import annotations

import itertools
from datetime import date, timedelta
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent / "data/leave.yaml"


class Timeout(Exception):
    """HartwellOne did not answer; the outcome is unknown."""


def days(start: str, end: str, holidays=()) -> list[str]:
    """Working days (Mon to Fri, not holidays), inclusive."""
    d, last, out = date.fromisoformat(start), \
        date.fromisoformat(end), []
    while d <= last:
        if d.weekday() < 5 and d.isoformat() not in holidays:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


class HartwellOne:
    def __init__(self, lose_reply_once: bool = False):
        self.cfg = yaml.safe_load(DATA.read_text())
        self.balances = {k: dict(v) for k, v in
                         self.cfg["balances"].items()}
        self.bookings: list[dict] = [
            dict(b, ref=f"LV-0{i}", by="seed")
            for i, b in enumerate(
                self.cfg["existing_bookings"], 1)]
        self._ids = itertools.count(1001)
        self._lose = lose_reply_once
        self.writes = 0

    # ---- read side ------------------------------------
    def balance(self, emp: str) -> dict:
        return dict(self.balances.get(emp, {}))

    def crew_calendar(self, start: str, end: str) -> dict:
        crew = self.cfg["crew"]
        hol = self.cfg["holidays"]
        out = {}
        for d in days(start, end, hol):
            off = [b["employee"] for b in self.bookings
                   if b["start"] <= d <= b["end"]]
            out[d] = {"off": off,
                      "on_shift": len(crew["members"])
                      - len(off)}
        return out

    def find(self, emp, start, end, kind) -> list[dict]:
        return [b for b in self.bookings
                if (b["employee"], b["start"], b["end"],
                    b["type"]) == (emp, start, end, kind)]

    # ---- write side -----------------------------------
    def book(self, emp, start, end, kind, by,
             idempotency_key: str | None = None) -> dict:
        """Write a booking and deduct the balance. With a
        key, a repeat call returns the first booking."""
        if idempotency_key:
            for b in self.bookings:
                if b.get("key") == idempotency_key:
                    return b
        n = len(days(start, end, self.cfg["holidays"]))
        b = {"employee": emp, "type": kind, "start": start,
             "end": end, "days": n, "by": by,
             "ref": f"LV-{next(self._ids)}",
             "key": idempotency_key}
        self.bookings.append(b)
        bal = self.balances.setdefault(emp, {})
        bal[kind] = bal.get(kind, 0) - n
        self.writes += 1
        if self._lose:
            self._lose = False
            raise Timeout("no reply from HartwellOne in 10 s")
        return b
