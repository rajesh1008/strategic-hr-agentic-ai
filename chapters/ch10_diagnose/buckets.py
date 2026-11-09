"""Chapter 10: the Four Buckets, measured by work sampling.

Sixty HR staff were asked, at six random moments a working day
for ten days, which bucket the work in front of them belonged to:
operational, ad hoc, program or strategic. The share of answers
in a bucket estimates the share of time. The interval resamples
whole people (a cluster bootstrap), because one person's answers
are not independent of each other. No model is used.

Run: HRAI_MODEL=no-model python -m chapters.ch10_diagnose.buckets
"""
from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
BUCKETS = ("operational", "ad hoc", "program", "strategic")
ESTIMATE = {"operational": .35, "ad hoc": .10, "program": .25,
            "strategic": .30}  # leadership team, January 2027


def load() -> list[dict]:
    with (DATA / "worksample.csv").open() as f:
        return list(csv.DictReader(f))


def shares(rows: list[dict]) -> dict[str, float]:
    c = Counter(r["bucket"] for r in rows if r["bucket"])
    n = sum(c.values())
    return {b: c[b] / n for b in BUCKETS}


def interval(rows: list[dict], reps: int = 2000,
             seed: int = 7) -> dict[str, tuple[float, float]]:
    by: dict[str, list] = defaultdict(list)
    for r in rows:
        by[r["person"]].append(r)
    people = sorted(by)
    rng = random.Random(seed)
    draws: dict[str, list] = {b: [] for b in BUCKETS}
    for _ in range(reps):
        pick = [r for p in rng.choices(people, k=len(people))
                for r in by[p]]
        for b, v in shares(pick).items():
            draws[b].append(v)
    out = {}
    for b, v in draws.items():
        v.sort()
        out[b] = (v[int(.025 * reps)], v[int(.975 * reps)])
    return out


def main() -> None:
    from hrai.llm import RunRecorder
    rec = RunRecorder("ch10", "buckets")
    p = rec.print
    rows = load()
    asked = len(rows)
    answered = sum(1 for r in rows if r["bucket"])
    people = len({r["person"] for r in rows})
    p(f"Work sampling: {people} people, {asked:,} prompts, "
      f"{answered:,} answered ({100 * answered / asked:.0f}%)")
    s, ci = shares(rows), interval(rows)
    p(f"{'bucket':<12}{'estimate':>9}{'measured':>10}  95% interval")
    for b in BUCKETS:
        lo, hi = ci[b]
        p(f"{b:<12}{100 * ESTIMATE[b]:>8.0f}%{100 * s[b]:>9.1f}%"
          f"  {100 * lo:.1f} to {100 * hi:.1f}")
    p("By group (operational / ad hoc / program / strategic):")
    for g in dict.fromkeys(r["group"] for r in rows):
        gs = shares([r for r in rows if r["group"] == g])
        p(f"  {g:<22}" + " / ".join(f"{100 * gs[b]:.0f}"
                                     for b in BUCKETS))
    ah = Counter(r["adhoc_kind"] for r in rows if r["adhoc_kind"])
    n = sum(ah.values())
    p("Inside ad hoc: " + ", ".join(
        f"{k} {100 * v / n:.0f}%" for k, v in ah.most_common()))
    rec.note(shares=s, interval=ci, estimate=ESTIMATE,
             groups={g: shares([r for r in rows if r["group"] == g])
                     for g in dict.fromkeys(r["group"]
                                            for r in rows)})
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
