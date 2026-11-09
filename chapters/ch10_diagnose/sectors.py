"""Chapter 10: the diagnostic at three sector organizations.

Lakemont Health: HR tickets by ward against roster lead time.
Brightwater Brands, plant OH-2: hours to a first human answer by
shift, and what night-shift workers ask about.
Westbridge City Council: process mining on HR casework.
All synthetic. No model is used.

Run: HRAI_MODEL=no-model python -m chapters.ch10_diagnose.sectors
"""
from __future__ import annotations

import csv
import statistics as st
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "sectors"


def rows(name: str) -> list[dict]:
    with (DATA / name).open() as f:
        return list(csv.DictReader(f))


def lakemont(p) -> None:
    w = rows("lakemont_wards.csv")
    for r in w:
        r["rate"] = 100 * int(r["scheduling_tickets"]) / int(r["staff"])
    late = [r for r in w if int(r["roster_lead_days"]) < 14]
    early = [r for r in w if int(r["roster_lead_days"]) >= 14]
    sched = sum(int(r["scheduling_tickets"]) for r in w)
    allt = sched + sum(int(r["other_tickets"]) for r in w)
    p(f"Lakemont Health: {len(w)} wards, {allt:,} HR tickets, "
      f"scheduling {100 * sched / allt:.0f}%")
    p("  Scheduling tickets per 100 staff, by roster lead time:")
    p(f"    under 14 days: {len(late):>2} wards, "
      f"{st.mean(r['rate'] for r in late):.0f}")
    p(f"    14 days or more: {len(early):>2} wards, "
      f"{st.mean(r['rate'] for r in early):.0f}")


def brightwater(p) -> None:
    q = rows("brightwater_oh2.csv")
    p(f"Brightwater OH-2: {len(q):,} HR queries, Q4 2026")
    for s in ("day", "evening", "night"):
        qs = [r for r in q if r["shift"] == s]
        hrs = [float(r["hours_to_first_human"]) for r in qs]
        top = Counter(r["category"] for r in qs).most_common(1)[0]
        p(f"  {s:<8}{len(qs):>4} queries, {st.median(hrs):>4.1f} h "
          f"to human; top {top[0]} "
          f"{100 * top[1] / len(qs):.0f}%")


def westbridge(p) -> None:
    ev = rows("westbridge_cases.csv")
    cases: dict[str, list] = defaultdict(list)
    for r in ev:
        cases[r["case"]].append(r)
    waits: dict[str, list] = defaultdict(list)
    for evs in cases.values():
        for a, b in zip(evs, evs[1:]):
            d = (date.fromisoformat(b["date"])
                 - date.fromisoformat(a["date"])).days
            waits[f"{a['activity']} > {b['activity']}"].append(d)
    open_ = [c for c in cases.values()
             if c[-1]["activity"] != "Case closed"]
    stuck = Counter(c[-1]["activity"] for c in open_)
    p(f"Westbridge casework: {len(cases)} cases opened "
      f"July to December 2026")
    p(f"  open on December 31: {len(open_)}; median wait:")
    for k, v in waits.items():
        p(f"  {k:<42}{st.median(v):>5.1f} days")
    p("  Open cases by last step:")
    for k, v in stuck.most_common():
        p(f"    {k:<38}{v:>4}")


def main() -> None:
    from hrai.llm import RunRecorder
    rec = RunRecorder("ch10", "sectors")
    lakemont(rec.print)
    brightwater(rec.print)
    westbridge(rec.print)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
