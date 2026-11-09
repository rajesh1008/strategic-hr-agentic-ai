"""Onboarding and offboarding as state machines.

Book section: "Onboarding and offboarding are journeys, not
tickets". Each journey is a list of steps with the steps
that must be done first. The agent may only take a step
whose prerequisites are done and whose catalog row is live;
three steps are never the agent's (right to work, the last
day and final pay). We replay a seeded quarter of starters and leavers
recorded under the old ticket process (synthetic) and count
the steps the state machine would have held.

Run: HRAI_MODEL=no-model python -m chapters.ch26_service.journeys
"""
from __future__ import annotations

import random

from hrai.llm import RunRecorder

ONBOARD = {   # step: (prerequisites, who)
    "offer_signed": ((), "recruiter"),
    "record_created": (("offer_signed",), "agent"),
    "right_to_work": (("record_created",), "person"),
    "equipment_ordered": (("record_created",), "agent"),
    "access_granted": (("right_to_work",), "agent"),
    "training_booked": (("record_created",), "agent"),
    "first_day": (("access_granted", "equipment_ordered"),
                  "manager"),
}
OFFBOARD = {
    "resignation_recorded": ((), "agent"),
    "last_day_set": (("resignation_recorded",), "person"),
    "final_pay": (("last_day_set",), "person"),
    "access_end_scheduled": (("last_day_set",), "agent"),
    "equipment_return": (("last_day_set",), "agent"),
    "exit_letter": (("last_day_set",), "agent"),
}


FORGOTTEN = {"training_booked", "access_end_scheduled",
             "equipment_return"}


def held(journey: dict, order: list[tuple[str, str]]):
    """Steps taken before their prerequisites, by the wrong
    hand, or never taken. Returns (step, why) pairs."""
    done, out = set(), []
    for step, who in order:
        pre, owner = journey[step]
        missing = [p for p in pre if p not in done]
        if missing:
            out.append((step, "before " + missing[0]))
        elif owner == "person" and who == "agent":
            out.append((step, "agent may not"))
        done.add(step)
    out += [(s, "never done") for s in journey if s not in done]
    return out


def legacy(journey: dict, rng: random.Random, p_early: float,
           p_skip: float) -> list[tuple[str, str]]:
    """A seeded journey as the old ticket queue ran it: the
    planned order, except that a quick step is sometimes done
    as soon as it is asked for (moved to the front) and a
    step nobody waits for is sometimes forgotten."""
    steps = [s for s in journey
             if s not in FORGOTTEN or rng.random() >= p_skip]
    for s in list(steps)[1:]:
        if journey[s][1] == "agent" and rng.random() < p_early:
            steps.remove(s)
            steps.insert(1, s)
    return [(s, journey[s][1]) for s in steps]


def replay(rec, name, journey, n, p_early, p_skip, seed):
    rng = random.Random(seed)
    counts, people = {}, 0
    for _ in range(n):
        h = held(journey, legacy(journey, rng, p_early, p_skip))
        people += bool(h)
        for step, why in h:
            counts[(step, why)] = counts.get((step, why), 0) + 1
    rec.print(f"== {name}: {n} journeys (synthetic),"
              f" {people} with a step held or missing"
              f" ({100 * people / n:.1f}%)")
    for (step, why), c in sorted(counts.items(),
                                 key=lambda kv: (-kv[1], kv[0])):
        rec.print(f"  {step:<22} {why:<26} {c:>4}")


def main() -> None:
    rec = RunRecorder("ch26", "journeys")
    replay(rec, "onboarding Q4 2027", ONBOARD, 412,
           0.05, 0.04, 2604)
    replay(rec, "offboarding Q4 2027", OFFBOARD, 268,
           0.06, 0.09, 2605)
    print(rec.save())


if __name__ == "__main__":
    main()
