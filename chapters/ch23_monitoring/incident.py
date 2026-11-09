"""Incident timelines measured against the runbook.

Book section: "The first 24 hours". An incident record is a
list of timed events, each naming the record it comes from
(feed log, ledger, PR-1 report, tickets). This module computes
the runbook targets from those events, so "did we meet the
runbook" is a calculation, not a recollection. No model is
called.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"


def load(name: str) -> dict:
    return yaml.safe_load((DATA / name).read_text())


def when(inc: dict) -> dict[str, datetime]:
    return {e["key"]: datetime.strptime(e["t"],
                                        "%Y-%m-%d %H:%M")
            for e in inc["events"]}


def hm(minutes: float) -> str:
    m = int(round(minutes))
    sign = "-" if m < 0 else ""
    return f"{sign}{abs(m) // 60} h {abs(m) % 60:02d} min"


def score(inc: dict, book: dict) -> list[dict]:
    """One row per runbook target the record can measure."""
    at, rows = when(inc), []
    for t in book["targets"]:
        if t["from"] not in at or t["to"] not in at:
            continue
        gap = (at[t["to"]] - at[t["from"]]).total_seconds() / 60
        ok = (gap <= t["max_min"] if "max_min" in t
              else gap >= t["min_min"])
        rows.append({"id": t["id"], "what": t["what"],
                     "took": gap, "met": ok})
    return rows


def show(inc: dict, book: dict, rec: RunRecorder) -> None:
    rec.print(f"== {inc['id']}: {inc['title']}")
    for e in sorted(inc["events"], key=lambda e: e["t"]):
        rec.print(f"  {e['t'][5:]}  {e['what']}  [{e['src']}]")
    at = when(inc)
    rows = score(inc, book)
    rec.print(f"-- runbook v{book['version']} targets")
    for r in rows:
        mark = "met " if r["met"] else "MISS"
        rec.print(f"  {r['id']} {mark} {hm(r['took']):>14}  "
                  f"{r['what']}")
    if "last_reversal" in at:
        span = at["last_reversal"] - at["harm"]
        rec.print(f"  first harm to last reversal read back: "
                  f"{hm(span.total_seconds() / 60)}")
    if "first_call" in at and "detected" in at:
        lead = at["detected"] - at["first_call"]
        rec.print(f"  first call to detection: "
                  f"{hm(lead.total_seconds() / 60)}")
    if "stop_requested" in at:
        stop = at["contained"] - at["stop_requested"]
        rec.print(f"  stop requested to agent stopped: "
                  f"{hm(stop.total_seconds() / 60)}")
    missed = [r["id"] for r in rows if not r["met"]]
    rec.print(f"  targets met {len(rows) - len(missed)} of "
              f"{len(rows)}; missed: {', '.join(missed) or 'none'}")


def main() -> None:
    rec = RunRecorder("ch23", "incident")
    book = load("runbook.yaml")
    for name in ("inc-2027-031.yaml", "inc-aurelia-2027-019.yaml"):
        show(load(name), book, rec)
    print(rec.save())


if __name__ == "__main__":
    main()
