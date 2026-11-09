"""Chapter 27: who sees an internal vacancy (no model).

Book section "Mobility the employee steers". Line row F05
(Chapter 11, v1.1) is Keep at recommend. Two designs over
the same 180 vacancies (Q1 2028) and the same staff:

  A  "matched": each vacancy is pushed to the 10 eligible
     people whose profiles best match it; anyone else sees it
     only by browsing the jobs board (15% a quarter).
  B  "every vacancy": every eligible person sees every
     vacancy in their feed; the match is a sort order the
     employee chooses, and can switch off.

Eligible: same entity, grade within one band. Relevant: the
person holds 2 or more of the vacancy's 3 skills on a full
profile; the fixture knows the full set, the matcher only
the profile. The measure is the share of people with at
least one relevant vacancy who saw one, by group, and under
B also the share with a relevant vacancy in the top 10 of
their own feed when it is sorted by match on their profile.

Run:  HRAI_MODEL=no-model python -m chapters.ch27_skills.mobility
"""
from __future__ import annotations

import random

from hrai.llm import RunRecorder

from .population import SEED, build, vacancies

PUSH = 10
BROWSE = .15


def profile(e, rng: random.Random) -> frozenset:
    """What the profile shows: back-from-leave, part-time and
    new staff have entered fewer of the skills they hold."""
    keep = 1.0
    if e.back_from_leave:
        keep = .45
    elif e.joiner or e.part_time:
        keep = .6
    return frozenset(s for s in e.skills if rng.random() < keep)


def run() -> dict:
    rng = random.Random(SEED + 1)
    staff = build()
    shown = {e.eid: profile(e, rng) for e in staff}
    vac = vacancies(rng)
    by_ent: dict[str, list] = {}
    for e in staff:
        by_ent.setdefault(e.entity, []).append(e)
    relevant, saw_a, saw_b = set(), set(), set()
    feed: dict[str, list] = {}
    browse = {e.eid for e in staff if rng.random() < BROWSE}
    for v in vac:
        elig = [e for e in by_ent[v["entity"]]
                if abs(e.grade - v["grade"]) <= 1]
        rel = [e for e in elig if len(e.skills & v["req"]) >= 2]
        relevant |= {e.eid for e in rel}
        ranked = sorted(elig, key=lambda e: (
            -len(shown[e.eid] & v["req"]), e.eid))
        pushed = {e.eid for e in ranked[:PUSH]}
        for e in rel:
            if e.eid in pushed or e.eid in browse:
                saw_a.add(e.eid)
            saw_b.add(e.eid)
        for e in elig:
            feed.setdefault(e.eid, []).append(
                (-len(shown[e.eid] & v["req"]), v["vid"],
                 len(e.skills & v["req"]) >= 2))
    top = {k for k, f in feed.items()
           if any(x[2] for x in sorted(f)[:PUSH])}
    return {"staff": staff, "relevant": relevant,
            "a": saw_a, "b": saw_b, "top": top, "vac": vac}


GROUPS = [("all", lambda e: True),
          ("back from leave", lambda e: e.back_from_leave),
          ("part-time", lambda e: e.part_time),
          ("joined < 1 year", lambda e: e.joiner),
          ("aged 50+", lambda e: e.age50),
          ("none of these", lambda e: not (
              e.back_from_leave or e.part_time or e.joiner))]


def main() -> None:
    r = run()
    rec = RunRecorder("ch27", "mobility")
    P = rec.print
    P(f"{len(r['vac'])} vacancies, {len(r['staff']):,} staff; "
      f"{len(r['relevant']):,} with a relevant vacancy")
    P("group            relevant  A pushed  B feed  B top 10")
    for name, f in GROUPS:
        rel = [e for e in r["staff"]
               if e.eid in r["relevant"] and f(e)]
        a = sum(e.eid in r["a"] for e in rel)
        b = sum(e.eid in r["b"] for e in rel)
        t = sum(e.eid in r["top"] for e in rel)
        n = len(rel)
        P(f"{name:16s} {n:8,d}  {a / n:8.1%}  {b / n:6.1%}"
          f"  {t / n:8.1%}")
        rec.note(group=name, relevant=n, a=a, b=b, top=t)
    rec.save()


if __name__ == "__main__":
    main()
