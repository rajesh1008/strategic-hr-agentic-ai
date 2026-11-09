"""Chapter 24: the candidate's path, counted (no model).

Book sections "The candidate's path, counted" and
"Hire-to-onboard, redesigned". Builds a seeded event log for
two samples of 10,000 started applications for Hartwell US
field service technician roles, March 2027 (the old path)
and November 2027 (the redesigned path), then counts, for
each step, how many people reached it, how many Hartwell
turned away and how many simply left.

How the log is generated (all synthetic, stated so a reader
can argue with it): a form completes with a fixed chance
per design and device; every day a candidate waits for
Hartwell carries the same small chance that they take
another job (WAIT_HAZARD); recruiters advance, interviewers
offer and background checks clear at fixed rates that do
not change between designs. Only the waits, the form and
the booking route change.

Run:  HRAI_MODEL=no-model python -m chapters.ch24_candidate_path.path
"""
from __future__ import annotations

import json
import random
import statistics as st
from pathlib import Path

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
SEED = 24
N = 10_000
WAIT_HAZARD = 0.02      # chance a waiting candidate leaves, per day
ADVANCE = 0.46          # recruiter advances (A04, Keep)
OFFER = 0.70            # interviewer recommends an offer
CLEAR = 0.97            # background check clears
TURN = {"advanced": ADVANCE, "offered": OFFER,
        "cleared": CLEAR}
PHONE = 0.71            # share of applications started on a phone

STEPS = ["started", "submitted", "advanced", "booked",
         "attended", "offered", "accepted", "cleared",
         "first_day"]

# The two designs. Waits are days a candidate waits for
# Hartwell before the step (mean of an exponential draw).
DESIGNS = {
    "2027-03 old path": {
        "form_minutes": 38, "account": True,
        "submit": {"phone": 0.52, "desktop": 0.72},
        "wait": {"advanced": 9.0, "booked": 4.0, "attended": 6.0,
                 "offered": 5.0, "cleared": 11.0,
                 "first_day": 7.0},
        "no_show": 0.14, "accept": 0.86},
    "2027-11 redesigned": {
        "form_minutes": 12, "account": False,
        "submit": {"phone": 0.71, "desktop": 0.77},
        "wait": {"advanced": 2.0, "booked": 0.5, "attended": 4.0,
                 "offered": 1.0, "cleared": 6.0,
                 "first_day": 5.0},
        "no_show": 0.09, "accept": 0.90},
}


def _waits(rng: random.Random, mean: float) -> int:
    return round(rng.expovariate(1 / mean)) if mean else 0


def _left(rng: random.Random, days: int) -> bool:
    return rng.random() > (1 - WAIT_HAZARD) ** days


def simulate(design: str, seed: int = SEED) -> list[dict]:
    """One record per started application: the last step
    reached, why it stopped and the days spent waiting."""
    d = DESIGNS[design]
    rng = random.Random(f"{seed}-{design}")
    out = []
    for i in range(N):
        dev = "phone" if rng.random() < PHONE else "desktop"
        r = {"id": f"S{i:05d}", "device": dev,
             "reached": "started", "stop": None, "days": 0}
        out.append(r)
        for step in STEPS[1:]:
            if step == "submitted":
                gone = rng.random() > d["submit"][dev]
            else:
                wait = _waits(rng, d["wait"].get(step, 0))
                r["days"] += wait
                gone = _left(rng, wait) or (
                    step == "attended"
                    and rng.random() < d["no_show"]) or (
                    step == "accepted"
                    and rng.random() > d["accept"])
            if gone:
                r["stop"] = "left"
                break
            if rng.random() > TURN.get(step, 1.0):
                r["stop"] = "turned_away"
                break
            r["reached"] = step
        if r["reached"] == "first_day":
            r["stop"] = "hired"
    return out


def funnel(recs: list[dict]) -> list[dict]:
    """Per step: how many reached it, and how many were lost
    on the way to it, split into 'left' (the candidate went:
    drop-out) and 'turned away' (a decision Hartwell made).
    The two are never added together."""
    idx = {s: i for i, s in enumerate(STEPS)}
    rows = []
    for k, step in enumerate(STEPS):
        here = sum(1 for r in recs if idx[r["reached"]] >= k)
        prev = STEPS[k - 1] if k else None
        lost = [r for r in recs if r["reached"] == prev]
        rows.append({
            "step": step, "reached": here,
            "left": sum(r["stop"] == "left" for r in lost),
            "turned_away": sum(r["stop"] == "turned_away"
                               for r in lost)})
    return rows


def report(rec: RunRecorder, design: str) -> dict:
    recs = simulate(design)
    rows = funnel(recs)
    rec.print(f"== {design}: {N} started applications")
    rec.print(f"{'step':<11}{'reached':>8}{'left':>7}"
              f"{'left%':>7}{'turned away':>13}")
    prior = None
    for row in rows:
        pct = row["left"] / prior if prior else 0
        rec.print(f"{row['step']:<11}{row['reached']:>8}"
                  f"{row['left']:>7}{pct:>7.1%}"
                  f"{row['turned_away']:>13}")
        prior = row["reached"]
    hired = [r for r in recs if r["stop"] == "hired"]
    left = sum(1 for r in recs if r["stop"] == "left")
    adv = [r for r in recs if r["reached"] in STEPS[2:]]
    after = sum(1 for r in adv if r["stop"] == "left")
    rec.print(f"first day: {len(hired)} of {N}; left at any "
              f"step {left}")
    rec.print(f"advanced by a recruiter {len(adv)}; of them "
              f"left before day one {after} "
              f"({after / len(adv):.1%})")
    rec.print(f"days waiting for Hartwell, hired: median "
              f"{st.median(r['days'] for r in hired):.0f}, "
              f"mean {st.mean(r['days'] for r in hired):.1f}")
    for dev in ("phone", "desktop"):
        s = [r for r in recs if r["device"] == dev]
        sub = sum(1 for r in s if r["reached"] != "started")
        rec.print(f"  form completed on {dev:<8}{sub / len(s):.1%}"
                  f" of {len(s)}")
    return {"design": design, "rows": rows, "hired": len(hired),
            "left": left, "advanced": len(adv),
            "left_after_yes": after}


def main() -> None:
    rec = RunRecorder("ch24", "path")
    out = [report(rec, d) for d in DESIGNS]
    a, b = out
    sa = a["left_after_yes"] / a["advanced"]
    sb = b["left_after_yes"] / b["advanced"]
    rec.print(f"== change: first day {a['hired']} -> "
              f"{b['hired']}; advanced who left "
              f"{sa:.1%} -> {sb:.1%}")
    rec.note(funnels=out, designs=DESIGNS,
             wait_hazard=WAIT_HAZARD)
    print(rec.save())


if __name__ == "__main__":
    main()
