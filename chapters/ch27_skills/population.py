"""Chapter 27: the 9,000 salaried staff in the inventory.

A seeded synthetic population for the inventory, mobility
and coverage runs (no model). Entity sizes are fixed; the
rates below shape the profiles and are stated, not hidden:

- Employees fill 2 to 7 entries; people back from long
  leave in the last six months, part-time staff and joiners
  of under a year fill fewer (the profile was never updated,
  or there was no time to).
- Grade bands G3 to G9 as in Chapter 12.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

SEED = 27
ENTITIES = [("US", 5400), ("CA", 850), ("UK", 760),
            ("NL", 310), ("DE", 420), ("AU", 340),
            ("IN", 920)]
N_SKILLS = 60          # full catalog size (Chapter 27 extract: 26)


@dataclass
class Emp:
    eid: str
    entity: str
    grade: int
    back_from_leave: bool
    part_time: bool
    joiner: bool
    age50: bool
    skills: frozenset


def build() -> list[Emp]:
    rng = random.Random(SEED)
    out = []
    n = 0
    for ent, size in ENTITIES:
        for _ in range(size):
            n += 1
            back = rng.random() < .05
            part = rng.random() < .08
            join = rng.random() < .12
            old = rng.random() < .27
            mean = 5.0 - 1.8 * back - 1.2 * part - 1.5 * join
            k = max(1, min(8, round(rng.gauss(mean, 1.2))))
            fam = rng.randrange(6)       # job family
            pool = list(range(fam * 10, fam * 10 + 10))
            sk = frozenset(rng.sample(pool, min(k, 10)))
            out.append(Emp(f"HW-{ent}{n:05d}", ent,
                           rng.randint(3, 9), back, part,
                           join, old, sk))
    return out


def vacancies(rng: random.Random, n: int = 180) -> list[dict]:
    out = []
    for i in range(n):
        fam = rng.randrange(6)
        req = frozenset(rng.sample(
            range(fam * 10, fam * 10 + 10), 3))
        ent = rng.choices([e for e, _ in ENTITIES],
                          [s for _, s in ENTITIES])[0]
        out.append({"vid": f"V-28{i + 1:03d}", "entity": ent,
                    "grade": rng.randint(4, 9), "req": req})
    return out
