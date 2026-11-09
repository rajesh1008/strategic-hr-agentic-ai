"""The model inventory and the audit calendar.

Book section: "The inventory and the calendar". One row per
system that uses a model or writes to a people system on one's
behalf. Five checks run on every version of the inventory, and
the calendar of evaluations and audits for the next twelve
months is computed from each row's cadence, not kept by hand.
No model is called.

  INV-1 a named owner
  INV-2 a stop route someone can use
  INV-3 every evaluation recorded and inside its cadence
  INV-4 EU high-risk rows keep logs at least six months
  INV-5 an agent that writes lists every downstream system,
        and each one is a row with a readback
"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"
CADENCE = {"golden_set": 7, "shared_day": 31,
           "routing_line": 31, "impact_table": 31,
           "test_set": 92, "changed_rosters": 31,
           "readback_pr1": 1, "seeded_fault": 92,
           "exit_test": 365, "line_rerun": None}
LIVE = {"Production", "Shadow"}


def d(s: str) -> date:
    return date.fromisoformat(str(s))


def check(inv: dict) -> list[str]:
    today, rows = d(inv["as_of"]), inv["systems"]
    ids = {r["id"]: r for r in rows}
    out = []
    for r in rows:
        if not r.get("owner"):
            out.append(f"INV-1 {r['id']}: no named owner")
        if r["gate"] not in LIVE:
            continue
        if r.get("stop") in (None, "", "none"):
            out.append(f"INV-2 {r['id']}: no stop route")
        if not r["evals"]:
            out.append(f"INV-3 {r['id']}: no evaluation recorded")
        for ev, when in r["evals"].items():
            days = CADENCE.get(ev)
            if days and (today - d(when)).days > days:
                out.append(f"INV-3 {r['id']}: {ev} last "
                           f"{when}, due every {days} days")
        if r.get("eu_high_risk") and r.get("log_months", 0) < 6:
            out.append(f"INV-4 {r['id']}: logs kept "
                       f"{r.get('log_months')} months")
        if r.get("writes"):
            down = r.get("downstream")
            if not down:
                out.append(f"INV-5 {r['id']}: downstream "
                           "systems not listed")
            for x in down or []:
                ev = ids.get(x, {}).get("evals", {})
                if not any("readback" in k for k in ev):
                    out.append(f"INV-5 {r['id']}: {x} has no "
                               "readback")
    return out


def calendar(inv: dict, months: int = 12) -> list[tuple]:
    start = d(inv["as_of"])
    end = start + timedelta(days=30 * months)
    items = []
    for r in inv["systems"]:
        if r["gate"] not in LIVE:
            continue
        for ev, when in r["evals"].items():
            days = CADENCE.get(ev)
            if not days or days < 7:
                continue
            nxt = d(when) + timedelta(days=days)
            while nxt < end:
                if nxt >= start:
                    items.append((nxt, r["id"], ev, r["owner"]))
                nxt += timedelta(days=days)
    for f in yaml.safe_load((DATA / "calendar_fixed.yaml")
                           .read_text()):
        if start <= d(f["date"]) < end:
            items.append((d(f["date"]), "-", f["what"],
                          f["owner"]))
    return sorted(items)


def main() -> None:
    rec = RunRecorder("ch23", "inventory")
    for name in ("inventory-2027-10.yaml",
                 "inventory-2027-12.yaml"):
        inv = yaml.safe_load((DATA / name).read_text())
        probs = check(inv)
        rec.print(f"== inventory as of {inv['as_of']}: "
                  f"{len(inv['systems'])} rows, "
                  f"{len(probs)} problems")
        for p in probs:
            rec.print(f"  {p}")
    cal = calendar(inv)
    rec.print(f"== audit calendar, 12 months from {inv['as_of']}"
              f": {len(cal)} dated items")
    by_month = Counter(x[0].strftime("%Y-%m") for x in cal)
    rec.print("  by month: " + ", ".join(
        f"{m[5:]}/{m[2:4]} {n}" for m, n in sorted(
            by_month.items())))
    by_owner = Counter(x[3] for x in cal)
    for o, n in by_owner.most_common():
        rec.print(f"  {o:<32}{n:>4}")
    rec.print("  first ten:")
    for when, sid, what, owner in cal[:10]:
        rec.print(f"    {when:%b %d}  {sid:<9} {what}")
    print(rec.save())


if __name__ == "__main__":
    main()
