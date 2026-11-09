"""Answering a freedom-of-information request about an
algorithm from the records already kept.

Book section: "Westbridge answers a request". The deadline is
counted in working days from the day after receipt, skipping
weekends and bank holidays. Each item of the request is mapped
to the record that answers it and any exemption to weigh, and
the hours are compared with the cost limit, once with the
assistant's trail and once without it. No model is called.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"


def working_day(start: date, n: int, holidays: set) -> date:
    d, k = start, 0
    while k < n:
        d += timedelta(days=1)
        if d.weekday() < 5 and d.isoformat() not in holidays:
            k += 1
    return d


def main() -> None:
    req = yaml.safe_load((DATA / "westbridge_foi.yaml")
                         .read_text())
    rec = RunRecorder("ch23", "foi")
    got = date.fromisoformat(req["received"])
    due = working_day(got, 20, set(req["bank_holidays"]))
    rec.print(f"WCC-FOI-2027-1184 received {got:%a %b %d, %Y}; "
              f"20 working days: due {due:%a %b %d, %Y}")
    limit_h = req["limit_gbp"] / req["rate_per_hour_gbp"]
    t = w = 0.0
    for it in req["items"]:
        t += it["hours_trail"]
        w += it["hours_without"]
        rec.print(f"  {it['id']} {it['asks']:<44} "
                  f"{it['hours_trail']:>5.2f} h "
                  f"{it['hours_without']:>5.2f} h")
        rec.print(f"     from: {it['source']}")
        if it["exemption"] != "none":
            rec.print(f"     weigh: {it['exemption']}")
    rec.print(f"hours with the trail {t:.2f}, without {w:.1f}; "
              f"cost limit {limit_h:.0f} h (rule to verify)")
    rec.print("with the trail: answer all six items" if
              t <= limit_h else "with the trail: over the limit")
    rec.print("without it: over the limit, refuse or narrow"
              if w > limit_h else "without it: inside the limit")
    print(rec.save())


if __name__ == "__main__":
    main()
