"""Chapter 24: three sector cases (no model).

Book section "Other employers, the same path".
  restonmere  knock-out questions for summer hiring across
              40 hotels, read with Chapter 7's impact table
  straits     Straits Ledger's Fair Consideration Framework
              check before an Employment Pass application
  pennant     Pennant Stores, Ontario: days from interview to
              the candidate being told, before and after the
              agent drafts the notice a manager has decided

All data synthetic and seeded.

Run:  HRAI_MODEL=no-model python -m chapters.ch24_candidate_path.sectors
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from hrai.llm import RunRecorder

from chapters.ch07_adverse_impact import impact as ai

SEED = 4024

# Restonmere: (question, pass chance women, men)
KNOCKOUTS = {
    "K1 right to work": (0.97, 0.97),
    "K2 lift 23 kg unaided": (0.61, 0.90),
    "K3 weekends and evenings": (0.84, 0.88),
}
APPLICANTS = 3000
WOMEN = 0.58


def restonmere(rng: random.Random) -> list[dict]:
    out = []
    for i in range(APPLICANTS):
        sex = "female" if rng.random() < WOMEN else "male"
        r = {"id": f"RH-{i:04d}", "sex": sex}
        for q, (pw, pm) in KNOCKOUTS.items():
            r[q] = rng.random() < (pw if sex == "female" else pm)
        out.append(r)
    return out


# Straits Ledger: (req, MyCareersFuture post date, days the
# advert actually ran, planned EP application date)
REQS = [
    ("SL-EP-01", date(2028, 1, 10), 21, date(2028, 2, 7)),
    ("SL-EP-02", date(2028, 1, 17), 14, date(2028, 2, 1)),
    ("SL-EP-03", date(2028, 1, 24), 9, date(2028, 2, 3)),
    ("SL-EP-04", date(2028, 2, 1), 30, date(2028, 3, 6)),
    ("SL-EP-05", date(2028, 2, 7), 14, date(2028, 2, 18)),
    ("SL-EP-06", date(2028, 2, 14), 28, date(2028, 3, 20)),
    ("SL-EP-07", date(2028, 2, 21), 16, date(2028, 3, 13)),
    ("SL-EP-08", date(2028, 3, 1), 21, date(2028, 3, 27)),
]
LOCAL_REVIEWED = {"SL-EP-01": 14, "SL-EP-02": 6, "SL-EP-03": 3,
                  "SL-EP-04": 22, "SL-EP-05": 0, "SL-EP-06": 9,
                  "SL-EP-07": 11, "SL-EP-08": 0}
FCF_DAYS = 14


def straits() -> list[tuple[str, list[str]]]:
    out = []
    for req, posted, ran, ep in REQS:
        why = []
        if ran < FCF_DAYS:
            why.append(f"advert ran {ran} days")
        if (ep - posted).days < FCF_DAYS:
            why.append(f"EP filed day {(ep - posted).days}")
        if LOCAL_REVIEWED[req] == 0:
            why.append("no local applicant reviewed")
        out.append((req, why))
    return out


# Pennant: days from interview to the candidate being told
INTERVIEWED = 1200
TOLD_BY = 45   # [VERIFY] Ontario post-interview response window


def pennant(rng: random.Random, agent: bool) -> list[int | None]:
    """None = never told. Before: the store manager tells
    each candidate. After: the manager records the decision
    and the agent drafts and sends the notice."""
    days = []
    for _ in range(INTERVIEWED):
        decide = rng.choice(range(2, 22))
        if agent:
            days.append(decide + rng.choice((0, 1)))
        elif rng.random() < 0.31:
            days.append(None)          # never told
        else:
            days.append(decide + int(rng.expovariate(1 / 12)))
    return days


def main() -> None:
    rng = random.Random(SEED)
    rec = RunRecorder("ch24", "sectors")
    rows = restonmere(rng)
    rec.print(f"Restonmere summer hiring, {len(rows)} applications")
    for q in KNOCKOUTS:
        t, _ = ai.table(rows, lambda r: r["sex"], lambda r, q=q: r[q])
        for line in ai.render(t, f"{q}: pass rate by sex"):
            rec.print(line)
    t, _ = ai.table(rows, lambda r: r["sex"],
                    lambda r: all(r[q] for q in KNOCKOUTS))
    for line in ai.render(t, "all three knock-outs: pass by sex"):
        rec.print(line)
    rec.print()
    rec.print(f"Straits Ledger FCF check, {len(REQS)} EP requisitions")
    flagged = 0
    for req, why in straits():
        flagged += bool(why)
        rec.print(f"{req}  {'HOLD ' + '; '.join(why) if why else 'ok'}")
    rec.print(f"held before filing: {flagged} of {len(REQS)}")
    rec.print()
    rec.print(f"Pennant Ontario, {INTERVIEWED} interviewed per design")
    for agent in (False, True):
        d = pennant(random.Random(SEED + agent), agent)
        never = sum(x is None for x in d)
        late = sum(x is not None and x > TOLD_BY for x in d)
        told = sorted(x for x in d if x is not None)
        med = told[len(told) // 2]
        rec.print(f"{'agent drafts' if agent else 'manager tells'}: "
                  f"never told {never}, told after day {TOLD_BY} "
                  f"{late}, median day {med}")
    rec.note(seed=SEED, knockouts=KNOCKOUTS)
    print(rec.save())


if __name__ == "__main__":
    main()
