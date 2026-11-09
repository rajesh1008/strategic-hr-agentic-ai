"""Chapter 5: the horizon scan, read from the rules as data.

Lists every recorded rule whose date falls in the window, and the
rules that are pending with no date. Deterministic; no model.

Run: HRAI_MODEL=no-model python -m chapters.ch05_jurisdiction_map.horizon
(writes runs/ch05/horizon/...)
"""
from __future__ import annotations

from datetime import date

from hrai import law
from hrai.llm import RunRecorder

START, END = date(2026, 11, 9), date(2027, 12, 31)


def main() -> None:
    rules = law.load_rules()
    rec = RunRecorder("ch05", "horizon")
    rows = law.horizon(rules, START, END)
    rec.print(f"Horizon {START} to {END}: {len(rows)} dated items")
    for r in rows:
        mark = "~" if r["basis"] == "expected" else (
            "?" if "secondary" in r["date_basis"] else " ")
        rec.print(f"{r['date']}{mark} {r['lane']:<6} {r['id']}")
        rec.note(**{**r, "date": r["date"].isoformat()})
    rec.print("~ expected or target date, not a fixed one")
    rec.print("? date from a secondary source only")
    undated = [r for r in rules if r["status"] in
               ("pending", "proposed") and not r.get("in_force")
               and not r.get("expected")]
    rec.print(f"Pending with no date: {len(undated)}")
    for r in undated:
        rec.print(f"  {r['lane']:<6} {r['id']}")
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
