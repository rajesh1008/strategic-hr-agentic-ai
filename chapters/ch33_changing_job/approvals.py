"""Chapter 33: manager approvals, card v1 against card v2.

Book sections "Managers as approvers" and "Adoption that
counts". Two parts, both no model:
1. The trail of Ruth Okonjo's queue on January 10, 2028,
   under approval card v1 (summary only, batch approve).
2. A seeded, illustrative simulation of 212 US field
   supervisors: card v1 from November 29, 2027; card v2
   from March 6, 2028 (failed checks shown first, a reason
   required to approve a flagged proposal, no batch approve
   on flagged). It reports outcome measures, not logins,
   and a weekly adoption curve in three states.
The simulation parameters are assumptions for the book,
not measurements.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch33_changing_job.approvals
"""
from __future__ import annotations

import math
import random
import statistics
from datetime import date, timedelta

from hrai.llm import RunRecorder

from .checks import flagged, load

SUPERVISORS = 212
PER_WEEK = 70           # proposals per supervisor-week
FLAG = 0.15             # share with a failed check
V1 = date(2027, 11, 29)
V2 = date(2028, 3, 6)
END = date(2028, 4, 24)  # last week counted


def trail(rec: RunRecorder) -> None:
    d = load()
    t0 = t = 6 * 3600 + 41 * 60 + 2
    secs = [4, 3, 2, 3]

    def hms(s: int) -> str:
        return f"{s // 3600:02}:{s % 3600 // 60:02}:{s % 60:02}"

    rec.print("trail CREW-DEN-07 2028-01-10 approver HW-012927"
              " card v1")
    rec.print(f"{hms(t)}  queue opened, 12 proposals")
    ps = d["proposals"]
    for p, s in zip(ps[:4], secs):
        t += s
        f = flagged(p, d["as_of"])
        rec.print(f"{hms(t)}  {p['id']} {p['kind']:10}approve "
                  f"{s:>3}s  failed: {', '.join(f) or '-'}")
    t += 9
    rest = ps[4:]
    nf = sum(1 for p in rest if flagged(p, d["as_of"]))
    rec.print(f"{hms(t)}  batch approve P05-P12 (8)  "
              f"failed: {nf}")
    tot = sum(1 for p in ps if flagged(p, d["as_of"]))
    rec.print(f"queue closed after {t - t0}s; 12 approved, "
              f"{tot} with a failed check")


def week_starts() -> list[date]:
    w, out = V1, []
    while w <= END:
        out.append(w)
        w += timedelta(days=7)
    return out


def simulate(rng: random.Random) -> dict:
    weeks = week_starts()
    rows, curve = {"v1": [], "v2": []}, []
    for i, w in enumerate(weeks):
        card = "v2" if w >= V2 else "v1"
        if w == V2 - timedelta(days=7):
            curve.append((w, None))
            continue        # training week for card v2
        p_use = 0.35 + 0.57 * (1 - math.exp(-i / 3))
        p_batch = min(0.65, 0.2 + 0.05 * i)
        state = [0, 0, 0]   # not using, without, with evidence
        for _ in range(SUPERVISORS):
            if rng.random() > p_use:
                state[0] += 1
                continue
            n = PER_WEEK + rng.randint(-15, 15)
            nf = sum(1 for _ in range(n) if rng.random() < FLAG)
            if card == "v1":
                batch = rng.random() < p_batch
                if batch:
                    a_f, s_f, s_u = nf, 3, 3
                else:
                    a_f = sum(1 for _ in range(nf)
                              if rng.random() < 0.45)
                    s_f, s_u = 25, 12
                evid = (not batch) and rng.random() < 0.3
            else:
                a_f = sum(1 for _ in range(nf)
                          if rng.random() < 0.12)
                s_f = rng.lognormvariate(math.log(600), 0.4)
                s_u = rng.choice([3, 15, 15, 20])
                evid = rng.random() < 0.88
            state[2 if evid else 1] += 1
            rows[card].append(
                {"n": n, "nf": nf, "a_f": a_f,
                 "mins": (nf * s_f + (n - nf) * s_u) / 60,
                 "sec": [s_f] * nf + [s_u] * (n - nf)})
        curve.append((w, state))
    return {"rows": rows, "curve": curve}


def summary(rows: list[dict]) -> dict:
    n = sum(r["n"] for r in rows)
    nf = sum(r["nf"] for r in rows)
    af = sum(r["a_f"] for r in rows)
    appr = (n - nf) + af
    secs = [s for r in rows for s in r["sec"]]
    return {"decisions": n, "approve": appr / n,
            "flagged": nf / n, "approved_failed": af / nf,
            "median_s": statistics.median(secs),
            "mins_week": statistics.mean(r["mins"]
                                         for r in rows)}


def main() -> None:
    rec = RunRecorder("ch33", "approvals")
    trail(rec)
    sim = simulate(random.Random(33))
    rec.print("")
    rec.print(f"Illustrative simulation, {SUPERVISORS} field "
              "supervisors (synthetic)")
    rec.print(f"{'measure':34}{'card v1':>12}{'card v2':>12}")
    s1 = summary(sim["rows"]["v1"])
    s2 = summary(sim["rows"]["v2"])
    lines = [
        ("decisions", "decisions", "{:,}"),
        ("approve rate", "approve", "{:.1%}"),
        ("proposals with a failed check", "flagged", "{:.1%}"),
        ("approved despite a failed check", "approved_failed",
         "{:.1%}"),
        ("median seconds per decision", "median_s", "{:.0f}"),
        ("decision minutes per user-week", "mins_week",
         "{:.0f}")]
    for label, k, f in lines:
        rec.print(f"{label:34}{f.format(s1[k]):>12}"
                  f"{f.format(s2[k]):>12}")
    rec.print("adoption by week: not using / without evidence /"
              " with")
    for w, st in sim["curve"]:
        if st is None:
            rec.print(f"  {w}  training week for card v2")
            continue
        rec.print(f"  {w}  {st[0]:>4}{st[1]:>5}{st[2]:>5}")
    rec.note(v1=s1, v2=s2,
             curve=[(str(w), s) for w, s in sim["curve"]])
    print(rec.save())


if __name__ == "__main__":
    main()
