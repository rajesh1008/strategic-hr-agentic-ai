"""Chapter 7: Hartwell's field-screening audit (no model).

Book section "Hartwell's field-screening audit". Two steps:
  1. the Smart Shortlist batch of February 5, 2027 (Chapter 1):
     824 ranked applications, kept or moved to not_progressed;
  2. the criterion inside it, "hold back any gap over six
     months", applied to 6,000 Q4 2026 applications.
Self-ID is joined only here, by candidate ID, after the step;
no screening step ever sees it.

Run:  HRAI_MODEL=no-model python -m chapters.ch07_adverse_impact.audit
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from hrai.llm import REPO, RunRecorder

from . import impact as ai
from .make_data import load

FX = REPO / "fixtures" / "hartwell"
AXES = [("age", "age"), ("sex", "sex_"),
        ("race/ethnicity", "race_ethnicity"),
        ("disability", "disability_")]
WORDS = {"age": ("age_40_plus", {"Y": "40+", "N": "under 40"}),
         "sex_": ("sex", {"F": "women", "M": "men"}),
         "disability_": ("disability",
                         {"Y": "disabled", "N": "not disabled"})}


def _fixture(name: str) -> list[dict]:
    with open(FX / name, newline="") as f:
        next(f)
        return list(csv.DictReader(f))


def joined(apps: list[dict], ids: list[dict]) -> list[dict]:
    sid = {r["candidate_id"]: r for r in ids}
    out = [{**a, **sid[a["candidate_id"]]} for a in apps]
    for r in out:
        for new, (old, words) in WORDS.items():
            r[new] = words.get(r[old], r[old])
    return out


def feb_batch() -> list[dict]:
    apps = [a for a in _fixture("field-tech-applicants.csv")
            if a["status_fri"] in ("applied", "not_progressed")]
    return joined(apps, _fixture("applicant-self-id.csv"))


def q4_pool() -> list[dict]:
    return joined(load("hartwell-q4-2026.csv"),
                  load("hartwell-q4-2026-self-id.csv"))


def no_long_gap(r: dict) -> bool:
    gap = r.get("longest_gap_months",
                r.get("employment_gap_months"))
    return int(gap) <= 6


def run_step(rec, label, recs, sel, axes, out, inter=True):
    rec.print(f"== {label}: {len(recs)} applications")
    for name, key in axes:
        rows, miss = ai.table(recs, lambda r: r[key], sel)
        for line in ai.render(rows, f"-- {name}", miss):
            rec.print(line)
        out[f"{label}|{name}"] = [ai.as_dict(r) for r in rows]
    if inter:
        g = ai.intersect("sex_", "age")
        rows, miss = ai.table(recs, g, sel)
        for line in ai.render(rows, "-- sex & age", miss):
            rec.print(line)
        out[f"{label}|sex & age"] = [ai.as_dict(r)
                                     for r in rows]
    rec.print()


def main() -> None:
    rec = RunRecorder("ch07", "audit")
    out: dict = {}
    feb = feb_batch()
    run_step(rec, "Smart Shortlist, Feb 5 2027", feb,
             lambda r: r["status_fri"] == "applied", AXES, out)
    kept = [r for r in feb if r["status_fri"] == "applied"]
    moved = [r for r in feb if r["status_fri"] != "applied"]
    rec.print(f"gap over 6 months: kept "
              f"{sum(not no_long_gap(r) for r in kept)}, moved "
              f"{sum(not no_long_gap(r) for r in moved)}")
    rec.print()
    run_step(rec, "Gap rule, Q4 2026 pool", q4_pool(),
             no_long_gap, AXES, out)
    allrows = [ai.Row(**d) for v in out.values() for d in v]
    for line in ai.legend(allrows):
        rec.print(line)
    path = Path(rec.save())
    side = path.with_name(path.name.split("-")[0]
                          + ".tables.json")
    side.write_text(json.dumps(out, indent=1) + "\n")
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
