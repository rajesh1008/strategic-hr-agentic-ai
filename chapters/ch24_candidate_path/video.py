"""Chapter 24: the one-way video step in Australia (no model).

Book section "The fall: a video step in Brisbane". Hartwell
Australia's camp services roles, 18 weekly cohorts of
applicants a recruiter had advanced, from Monday, January
3, 2028. Weeks 1 to 6: a recruiter books a phone screen.
Weeks 7 to 12: a one-way video (recorded answers, watched by
a recruiter, never scored) replaces it. Weeks 13 to 18: the
applicant chooses video, a phone call the scheduling agent
books, or written answers.

The step counts as completed if done within seven days of
the invitation. Completion chances are fixed by phase and
group below (synthetic); everything printed is counted from
the seeded log, then read with Chapter 7's table.

Run:  HRAI_MODEL=no-model python -m chapters.ch24_candidate_path.video
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from hrai.llm import RunRecorder

from chapters.ch07_adverse_impact import impact as ai

SEED = 2024
START = date(2028, 1, 3)
WEEKLY = 45
OLDER, CAMP, ASKS = 0.38, 0.30, 0.04

# (base, minus if 40+, minus if applying from a camp site)
PHASES = {
    "phone": (1, 6, 0.85, 0.01, 0.07),
    "video": (7, 12, 0.73, 0.19, 0.30),
    "choice": (13, 18, 0.86, 0.02, 0.06),
}
# in the choice phase, the route people took, by camp or not
ROUTES = {False: (("video", .46), ("phone", .43),
                  ("written", .11)),
          True: (("video", .18), ("phone", .64),
                 ("written", .18))}


def phase(week: int) -> str:
    return next(p for p, (a, b, *_) in PHASES.items()
                if a <= week <= b)


def make(seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for week in range(1, 19):
        ph = phase(week)
        _, _, base, old_cut, camp_cut = PHASES[ph]
        for i in range(WEEKLY):
            r = {"id": f"AU{week:02d}-{i:02d}", "week": week,
                 "phase": ph,
                 "age": "40+" if rng.random() < OLDER
                 else "under 40",
                 "site": "camp" if rng.random() < CAMP
                 else "metro",
                 "asked_adjustment": rng.random() < ASKS}
            p = base - (old_cut if r["age"] == "40+" else 0) \
                - (camp_cut if r["site"] == "camp" else 0)
            if r["asked_adjustment"]:
                # video: the request went to a shared inbox;
                # otherwise a named coordinator decides
                p = 0.25 if ph == "video" else 0.80
            r["done"] = rng.random() < max(p, 0.10)
            r["route"] = ph
            if ph == "choice":
                x, acc = rng.random(), 0.0
                for name, share in ROUTES[r["site"] == "camp"]:
                    acc += share
                    if x < acc:
                        r["route"] = name
                        break
            out.append(r)
    return out


def main() -> None:
    rec = RunRecorder("ch24", "video")
    recs = make()
    rec.print("Hartwell Australia, camp services, advanced "
              "applicants")
    rec.print("completed the step within 7 days, by week:")
    weekly = []
    for w in range(1, 19):
        s = [r for r in recs if r["week"] == w]
        k = sum(r["done"] for r in s)
        weekly.append((w, k, len(s)))
        wk = START + timedelta(weeks=w - 1)
        if w in (1, 6, 7, 12, 13, 18):
            rec.print(f"  week {w:>2} ({wk:%b} {wk.day:>2}) "
                      f"{phase(w):<7}{k:>3} of {len(s)} "
                      f"{k / len(s):.0%}")
    for ph in PHASES:
        s = [r for r in recs if r["phase"] == ph]
        k = sum(r["done"] for r in s)
        rec.print(f"== {ph}: {k} of {len(s)} "
                  f"({k / len(s):.1%}); drop-out "
                  f"{len(s) - k}")
        for label, key in (("age", "age"), ("site", "site")):
            rows, _ = ai.table(s, lambda r, k=key: r[k],
                               lambda r: r["done"])
            for line in ai.render(rows, f"  by {label}")[2:]:
                rec.print("  " + line)
        a = [r for r in s if r["asked_adjustment"]]
        rec.print(f"  asked for an adjustment: "
                  f"{sum(r['done'] for r in a)} of {len(a)} "
                  f"completed")
    s = [r for r in recs if r["phase"] == "choice"]
    for site in ("metro", "camp"):
        g = [r for r in s if r["site"] == site]
        mix = {n: sum(r["route"] == n for r in g)
               for n in ("video", "phone", "written")}
        rec.print(f"choice routes, {site}: " + ", ".join(
            f"{n} {v}" for n, v in mix.items()))
    rec.note(weekly=weekly, phases=PHASES, start=str(START))
    print(rec.save())


if __name__ == "__main__":
    main()
