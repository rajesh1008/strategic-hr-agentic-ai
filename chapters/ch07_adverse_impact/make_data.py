"""Build the synthetic records for Chapter 7 (seeded; every
reader gets byte-identical files).

  data/hartwell-q4-2026.csv      Hartwell field-technician
      applications, October to December 2026, 30 requisitions;
      attributes drawn with the book generator's own helpers
      (fixtures/generate.py), so gaps fall more often on women
      and on applicants 40 and over, as in Chapter 1
  data/hartwell-q4-2026-self-id.csv   voluntary self-ID, kept
      apart from the screening data as an ATS keeps it
  data/crossfield-nyc.csv        a Crossfield client's
      warehouse assessment in New York City, 12 months
  data/calder-tellers.csv        Cobbleford Bank branch-teller test,
      six regions x four quarters of 2026
  data/pennant-associates.csv    Pennant seasonal store-associate
      applicants, US and Canada, with the work-style test
  data/lakemont-rn.csv           Lakemont registered-nurse
      assessment, 2026 (before) and 2027 Q1 (after redesign)

Everything is invented. The mechanisms are written in the
code below so a reader can see what the tables recover.
Run:  python -m chapters.ch07_adverse_impact.make_data [--check]
"""
from __future__ import annotations

import csv
import io
import random
import sys
from pathlib import Path

from fixtures import generate as gen

HERE = Path(__file__).resolve().parent / "data"
SEED = 7
HEAD = gen.CSV_HEAD


def _csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    buf.write(HEAD)
    w = csv.DictWriter(buf, fieldnames=list(rows[0]),
                       lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode()


def hartwell(rng: random.Random):
    """6,000 applications on 30 field-technician requisitions."""
    sites = ["Denver, CO", "Joliet, IL", "Houston, TX",
             "Queens, NY", "Fresno, CA", "Phoenix, AZ"]
    apps, ids = [], []
    for q in range(30):
        req = f"REQ-FT-2026-{410 + q:04d}"
        site = sites[q % len(sites)]
        for k in range(200):
            cid = f"C-Q4-{q:02d}{k:03d}"
            sid = gen._self_id(rng)
            a = gen._cand_attrs(rng, sid["_older"], sid["_female"])
            apps.append(dict(
                candidate_id=cid, requisition=req, site=site,
                years_field_service=a["years_field_service"],
                longest_gap_months=a["employment_gap_months"],
                certifications="; ".join(a["certifications"])))
            ids.append(dict(candidate_id=cid, sex=sid["sex"],
                            age_40_plus=sid["age_40_plus"],
                            race_ethnicity=sid["race_ethnicity"],
                            disability=sid["disability"],
                            veteran=sid["veteran"]))
    pick = set(rng.sample([a["candidate_id"] for a in apps],
                          1200))
    for a in apps:
        a["agent_sample"] = "Y" if a["candidate_id"] in pick \
            else "N"
    return apps, ids


NYC_RACE = {"Hispanic or Latino": 30, "White": 24,
            "Black or African American": 27, "Asian": 12,
            "Native Hawaiian or Pacific Islander": 0.6,
            "Native American or Alaska Native": 0.7,
            "Two or more races": 2.2, "unknown": 3.5}


def crossfield(rng: random.Random) -> list[dict]:
    """The client's vendor assessment, cut score 60. The score
    runs 2.5 points lower for Black applicants and a further
    2.0 lower for Black women (the synthetic mechanism)."""
    rows = []
    for i in range(9000):
        race = gen._pick(rng, NYC_RACE)
        sex = gen._pick(rng, {"Female": 41, "Male": 56,
                              "unknown": 3})
        s = rng.gauss(64, 11)
        if race == "Black or African American":
            s -= 2.5 + (2.0 if sex == "Female" else 0)
        if race == "Hispanic or Latino":
            s -= 0.8
        s = max(0, min(100, round(s)))
        rows.append(dict(applicant=f"XF-NYC-{i:05d}", sex=sex,
                         race_ethnicity=race, score=s,
                         selected="Y" if s >= 60 else "N"))
    return rows


def calder(rng: random.Random) -> list[dict]:
    """Branch-teller test; the true pass rate barely differs
    by age (0.46 under 40, 0.44 at 40 and over)."""
    regions = {"Charlotte": 22, "Raleigh": 14, "Atlanta": 18,
               "Richmond": 10, "Nashville": 12, "Columbia": 9}
    rows, i = [], 0
    for q in ("2026Q1", "2026Q2", "2026Q3", "2026Q4"):
        for reg, size in regions.items():
            for _ in range(int(size * 2.4 + rng.randrange(8))):
                older = rng.random() < 0.28
                p = 0.44 if older else 0.46
                rows.append(dict(
                    applicant=f"CB-T-{i:05d}", quarter=q,
                    region=reg,
                    age_40_plus="Y" if older else "N",
                    passed="Y" if rng.random() < p else "N"))
                i += 1
    return rows


def pennant(rng: random.Random) -> list[dict]:
    """Work-style test for seasonal associates. Its 'open
    availability' items fall hardest on women 40 and over,
    who carry most caregiving in this synthetic pool."""
    p = {("F", "N"): 0.62, ("F", "Y"): 0.47,
         ("M", "N"): 0.63, ("M", "Y"): 0.62}
    rows = []
    for i in range(14000):
        country = "US" if rng.random() < 0.64 else "Canada"
        sex = "F" if rng.random() < 0.58 else "M"
        older = "Y" if rng.random() < 0.24 else "N"
        passed = rng.random() < p[(sex, older)]
        no_id = rng.random() < (0.29 if country == "Canada"
                                else 0.12)
        rows.append(dict(
            applicant=f"PS-{i:05d}", country=country,
            sex="declined" if no_id else sex,
            age_40_plus="declined" if no_id else older,
            passed="Y" if passed else "N"))
    return rows


def lakemont(rng: random.Random) -> list[dict]:
    """RN assessment. Disabled applicants who get the adjustment
    they need pass at close to the usual rate; those who do not
    pass far less often. The redesign moved the request route
    from page 4 of the instructions to the invitation itself."""
    rows = []
    for period, n, ask in (("2026", 2400, 0.18),
                           ("2027Q1", 640, 0.61)):
        for i in range(n):
            dis = gen._pick(rng, {"Y": 6, "N": 88, "declined": 6})
            asked = dis == "Y" and rng.random() < ask
            granted = asked and rng.random() < (
                0.55 if period == "2026" else 0.95)
            p = 0.71 if dis != "Y" else (0.69 if granted else 0.50)
            rows.append(dict(
                applicant=f"LK-{period}-{i:04d}", period=period,
                disability=dis,
                asked="Y" if asked else "N",
                adjusted="Y" if granted else "N",
                days_to_decide=(rng.choice([3, 4, 6, 6, 8, 11])
                                if period == "2026" else
                                rng.choice([0, 1, 1, 1, 2]))
                if asked else "",
                passed="Y" if rng.random() < p else "N"))
    return rows


def build() -> dict[str, bytes]:
    rng = random.Random(SEED)
    apps, ids = hartwell(rng)
    return {
        "hartwell-q4-2026.csv": _csv(apps),
        "hartwell-q4-2026-self-id.csv": _csv(ids),
        "crossfield-nyc.csv": _csv(crossfield(rng)),
        "calder-tellers.csv": _csv(calder(rng)),
        "pennant-associates.csv": _csv(pennant(rng)),
        "lakemont-rn.csv": _csv(lakemont(rng)),
    }


def load(name: str) -> list[dict]:
    with open(HERE / name, newline="") as f:
        next(f)
        return list(csv.DictReader(f))


def main(argv: list[str]) -> int:
    files = build()
    bad = 0
    for name, data in files.items():
        p = HERE / name
        if "--check" in argv:
            if not p.exists() or p.read_bytes() != data:
                print(f"differs: {name}")
                bad += 1
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            print(f"wrote {name} ({len(data):,} bytes)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
