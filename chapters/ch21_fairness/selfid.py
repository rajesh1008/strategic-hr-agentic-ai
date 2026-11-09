"""Chapter 21: self-ID for Chapter 16's 400 applications.

Book section "Hartwell's audit, one version at a time". The
400 double-read applications of Chapter 16 carry no
demographic data, and the screening agent never sees any.
This file gives each one a synthetic self-identification
record, the answers an applicant gives on Hartwell Careers'
voluntary form, kept in a separate store and joined by
candidate ID only after the step (Chapter 7).

The draw is seeded and its rules are stated, so a reader can
see why a group's numbers look as they do:
  age 40+     more likely the longer the career shown, and
              for career changers (one recent role)
  veteran     almost always for a US Navy HVAC/R role
  women       more likely where a resume shows a dispatch,
              parts-counter, sales, warehouse or customer-
              service role, and most likely where that role
              is what keeps the applicant short of 24 months
              of field service under guidance v1
  Hispanic    more likely where "Spanish and English" appears
  declined    about one applicant in six answers nothing,
              one in sixteen leaves race/ethnicity blank

Everything is invented. Run:
  python -m chapters.ch21_fairness.selfid [--check]
"""
from __future__ import annotations

import csv
import io
import random
import sys
from pathlib import Path

from chapters.ch16_routing.make_data import NONFIELD, MILITARY, load

OUT = Path(__file__).resolve().parent / "data" / \
    "hartwell-ft-2027-self-id.csv"
SEED = 21
NOW = 2027 * 12 + 4          # May 2027, as in guidance v1
RACES = [("White", .62), ("Black or African American", .17),
         ("Hispanic or Latino", .08), ("Asian", .06),
         ("Two or more races", .04),
         ("Native Hawaiian or Pacific Islander", .02),
         ("Native American or Alaska Native", .01)]
FIELDS = ["candidate_id", "sex", "age_40_plus",
          "race_ethnicity", "veteran", "disability"]


def pick(rng: random.Random, table) -> str:
    x, acc = rng.random(), 0.0
    for name, p in table:
        acc += p
        if x < acc:
            return name
    return table[-1][0]


def one(rng: random.Random, a: dict) -> dict:
    titles = [r["title"] for r in a["roles"]]
    years = (NOW - min(r["start"] for r in a["roles"])) / 12
    p40 = .15 if years < 4 else .35 if years < 8 else .7
    if a["kind"] == "present_near":
        p40 = .55
    nonfield = any(t in NONFIELD for t in titles)
    spanish = "Spanish and English" in a["extra"]
    row = {
        "candidate_id": a["candidate_id"],
        "sex": "F" if rng.random() < (
            (.6 if not a["meets"] else .3) if nonfield
            else .1) else "M",
        "age_40_plus": "Y" if rng.random() < p40 else "N",
        "race_ethnicity": (
            pick(rng, [("Hispanic or Latino", .75),
                       ("White", .15), ("Black or African "
                                        "American", .1)])
            if spanish else pick(rng, RACES)),
        "veteran": "Y" if rng.random() < (
            .95 if MILITARY in titles else .05) else "N",
        "disability": "Y" if rng.random() < .06 else "N",
    }
    u = rng.random()
    if u < 1 / 6:
        row = {k: ("declined" if k != "candidate_id" else v)
               for k, v in row.items()}
    elif u < 1 / 6 + 1 / 16:
        row["race_ethnicity"] = "declined"
    return row


def make() -> bytes:
    rng = random.Random(SEED)
    buf = io.StringIO()
    buf.write("# _synthetic: Invented for the book. No real "
              "person, employer or applicant.\n")
    w = csv.DictWriter(buf, fieldnames=FIELDS,
                       lineterminator="\n")
    w.writeheader()
    for a in load():
        w.writerow(one(rng, a))
    return buf.getvalue().encode()


def read() -> list[dict]:
    with open(OUT, newline="") as f:
        next(f)
        return list(csv.DictReader(f))


if __name__ == "__main__":
    data = make()
    if "--check" in sys.argv:
        ok = OUT.read_bytes() == data
        print("identical" if ok else "DIFFERENT")
        sys.exit(0 if ok else 1)
    OUT.write_bytes(data)
    print(f"wrote {OUT.name}: {len(read())} rows")
