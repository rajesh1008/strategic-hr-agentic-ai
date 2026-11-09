"""Chapter 27: three second organizations (no model).

Book sections "Hollis Precision: a matrix someone signs",
"Thorne Kessler: utilization is not performance" and
"Brightwater India: location is not a sales result". All
synthetic and seeded; the rule that shapes each number is
stated beside its generator.

Run:  HRAI_MODEL=no-model python -m chapters.ch27_skills.sectors
"""
from __future__ import annotations

import random
from datetime import date

from hrai.llm import RunRecorder

SEED = 27
AS_OF = date(2028, 1, 31)


# --- Hollis: CNC and maintenance skills matrix, Grand Rapids
# 212 people x 18 tasks. A cell counts only with a level,
# an assessor and a sign-off date; a sign-off older than 24
# months reads "refresh". A critical task is covered on a
# shift when 2 or more people hold level 3 or 4 on it.
# Tasks 1 to 6 are the critical machines; 7% are trained.
def hollis_cell(rng: random.Random, crit: bool) -> dict | None:
    if rng.random() < (.93 if crit else .55):
        return None                     # not trained
    lvl = rng.choices([1, 2, 3, 4], [2, 3, 4, 1])[0]
    who = None if rng.random() < .14 else "assessor"
    months = rng.choice([3, 8, 14, 20, 27, 34, 41]) \
        if who else None
    return {"level": lvl, "assessor": who,
            "months": months}


def hollis(rec: RunRecorder) -> None:
    rng = random.Random(SEED)
    shifts = {s: [[hollis_cell(rng, t < 6) for t in range(18)]
                  for _ in range(n)]
              for s, n in (("days", 84), ("afters", 72),
                           ("nights", 56))}
    cells = [c for rows in shifts.values() for r in rows
             for c in r if c]
    unsigned = sum(c["assessor"] is None for c in cells)
    stale = sum(bool(c["assessor"]) and c["months"] > 24
                for c in cells)
    rec.print("Hollis Grand Rapids: 212 people x 18 tasks")
    rec.print(f"  cells with a level      {len(cells):,}")
    rec.print(f"  no assessor or date     {unsigned:,}")
    rec.print(f"  signed over 24 months   {stale:,}")
    crit = range(6)                     # tasks 1 to 6
    for rule in ("as written", "signed and current"):
        gaps = 0
        for s, rows in shifts.items():
            for t in crit:
                n = 0
                for r in rows:
                    c = r[t]
                    if not c or c["level"] < 3:
                        continue
                    if rule != "as written" and (
                            c["assessor"] is None
                            or c["months"] > 24):
                        continue
                    n += 1
                gaps += n < 2
        rec.print(f"  critical task-shifts under 2 qualified"
                  f" ({rule}): {gaps} of 18")


# --- Thorne Kessler: utilization against a 75% target ---
# 1,200 associates. Chargeable hours come from timesheets
# the person keeps; leave, firm training and approved firm
# work are removed from available hours before the ratio.
def thorne(rec: RunRecorder) -> None:
    rng = random.Random(SEED + 1)
    raw = adj = 0
    for _ in range(1200):
        avail = 1650.0
        leave = rng.choice([0, 0, 0, 40, 80, 300])
        train = rng.choice([20, 40, 80])
        firm = rng.choice([0, 0, 60, 150])
        busy = rng.gauss(.81, .06)
        charge = (avail - leave - train - firm) * busy
        raw += charge / avail < .75
        adj += charge / (avail - leave - train - firm) < .75
    rec.print("Thorne Kessler: 1,200 associates, 75% target")
    rec.print(f"  below target, raw hours      {raw}")
    rec.print(f"  below target, adjusted hours {adj}")


# --- Brightwater Brands Asia: India field sales ---
# 2,100 reps. Results (orders against outlet potential) are
# independent of GPS "beat adherence", which falls with
# rural routes, two-wheeler breakdowns and phone signal.
def brightwater(rec: RunRecorder) -> None:
    rng = random.Random(SEED + 2)
    reps = []
    for i in range(2100):
        rural = rng.random() < .4
        adh = rng.gauss(.78 - .12 * rural, .1)
        res = rng.gauss(1.0, .18)
        reps.append((i, adh, res, rural))
    k = len(reps) // 10
    by_adh = {r[0] for r in sorted(reps, key=lambda r: r[1])[:k]}
    by_res = {r[0] for r in sorted(reps, key=lambda r: r[2])[:k]}
    rural = sum(1 for r in reps if r[0] in by_adh and r[3])
    rec.print("Brightwater India: 2,100 field-sales reps")
    rec.print(f"  bottom tenth by GPS adherence {len(by_adh)},"
              f" rural {rural}")
    rec.print(f"  also bottom tenth by results  "
              f"{len(by_adh & by_res)}")


def main() -> None:
    rec = RunRecorder("ch27", "sectors")
    hollis(rec)
    thorne(rec)
    brightwater(rec)
    rec.save()


if __name__ == "__main__":
    main()
