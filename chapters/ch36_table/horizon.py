"""Chapter 36: the next three years, dated (deterministic).

Book section "The next three years". Each row is a rule
milestone from the evidence register with its source ID.
The script sorts them against the date the register was
checked: already in force, dated ahead (by year), and
pending with no date. Nothing here is a forecast; the
rows with no date are listed as having none.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch36_table.horizon
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent


def load() -> dict:
    return yaml.safe_load(
        (HERE / "data" / "horizon.yaml").read_text())


def sort(data: dict) -> dict[str, list[dict]]:
    out = {"in force": [], "ahead": [], "no date": []}
    for m in data["milestones"]:
        if m["date"] is None:
            out["no date"].append(m)
        elif m["date"] <= data["as_of"]:
            out["in force"].append(m)
        else:
            out["ahead"].append(m)
    for k in ("in force", "ahead"):
        out[k].sort(key=lambda m: m["date"])
    return out


def main() -> None:
    rec = RunRecorder("ch36", "horizon")
    data = load()
    s = sort(data)
    rec.print(f"Register checked {data['as_of']:%B %-d, %Y}: "
              f"{len(data['milestones'])} milestones")
    rec.print(f"  in force: {len(s['in force'])}")
    by_year = defaultdict(list)
    for m in s["ahead"]:
        by_year[m["date"].year].append(m)
    rec.print(f"  dated ahead: {len(s['ahead'])}")
    for y in sorted(by_year):
        rec.print(f"    {y}: {len(by_year[y])}")
        for m in by_year[y]:
            day = (f"{m['date']:%b}" if m.get("month_only")
                   else f"{m['date']:%b %-d}")
            rec.print(f"      {day:<7} {m['jur']:<6} "
                      f"{m['what']} [{m['r']}]")
    rec.print(f"  pending, no date in the register: "
              f"{len(s['no date'])}")
    for m in s["no date"]:
        rec.print(f"      {m['jur']:<6} {m['what']} [{m['r']}]")
    rec.note(**{k: len(v) for k, v in s.items()},
             by_year={y: len(v) for y, v in by_year.items()})
    rec.save()


if __name__ == "__main__":
    main()
