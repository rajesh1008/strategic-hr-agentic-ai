"""Chapter 12: build the synthetic job catalog and local job codes.

HartwellOne holds three job architectures (synthetic): the Hartwell
Grades written in Denver for the 2016 go-live (HG), the UK legacy
bands that came with Hartwell UK (UKB), and the collective-agreement
pay groups used in the Netherlands and Germany (EUCA). Defects are
injected at fixed counts so the quality scorecard has something to
find. Seeded; rerunning gives the same files.

Run: python -m chapters.ch12_data_readiness.make_data
"""
from __future__ import annotations

import csv
import gzip
import random
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "data"
SEED = 20270322
TAG = "# _synthetic: Invented for the book. No real employer.\n"
COLS = ["code", "architecture", "entity", "title", "desc",
        "mapped_grade", "last_reviewed", "status"]


def hg_rows() -> list[dict]:
    fams = ["Field Service", "Facilities", "Energy", "Engineering",
            "Operations", "Finance", "HR", "IT", "Projects"]
    rows = []
    for f in fams:
        field = f in ("Field Service", "Facilities", "Energy")
        for g in (["F1", "F2", "F3", "F4"] if field else
                  ["G3", "G4", "G5", "G6", "G7", "G8"]):
            rows.append({"code": f"HG-{f[:3].upper()}-{g}",
                         "architecture": "HG", "entity": "Group",
                         "title": f"{f} {g}", "desc": f"{f} at {g}",
                         "mapped_grade": g, "last_reviewed": "2026-10",
                         "status": "active"})
    return rows


def main() -> None:
    rng = random.Random(SEED)
    prof = yaml.safe_load((HERE / "profiles.yaml").read_text())
    rows = hg_rows()
    for p in prof["profiles"]:
        arch = "UKB" if p["code"].startswith("UK") else "EUCA"
        ent = {"UK": "Hartwell UK", "DE": "Hartwell Germany",
               "NL": "Hartwell Netherlands"}[p["code"][:2]]
        rows.append({"code": p["code"], "architecture": arch,
                     "entity": ent, "title": p["title"],
                     "desc": p["desc"], "mapped_grade": p["mapped"],
                     "last_reviewed": "2016-05" if arch == "UKB"
                     else "2025-06", "status": "active"})
    # Further UK and EU codes, with defects at fixed counts.
    for i in range(16):
        rows.append({"code": f"UK-X{i + 1:02d}", "architecture": "UKB",
                     "entity": "Hartwell UK",
                     "title": f"Contract role {i + 1}",
                     "desc": "" if i < 9 else "Contract-specific role",
                     "mapped_grade": "" if i in (2, 5, 8, 11) else
                     rng.choice(["F2", "F3", "G4", "G5"]),
                     "last_reviewed": "2016-05",
                     "status": "active"})
    for i in range(10):
        c = "DE" if i < 5 else "NL"
        rows.append({"code": f"{c}-X{i + 1:02d}", "architecture": "EUCA",
                     "entity": "Hartwell Germany" if c == "DE"
                     else "Hartwell Netherlands",
                     "title": f"Tarif role {i + 1}",
                     "desc": "Pay group per collective agreement",
                     "mapped_grade": "" if i in (3, 7) else
                     rng.choice(["F2", "F3", "G4"]),
                     "last_reviewed": "2025-06", "status": "active"})
    # Four UK titles duplicated under a second band.
    for src in ("UK-B01", "UK-B03", "UK-C01", "UK-D01"):
        r = dict(next(x for x in rows if x["code"] == src))
        r["code"] = src.replace("-", "-Z")
        r["mapped_grade"] = {"UK-B01": "F2", "UK-B03": "G5",
                             "UK-C01": "F3", "UK-D01": "G7"}[src]
        rows.append(r)
    # Two codes the catalog keeps but HR retired in 2021.
    rows.append({"code": "UK-R01", "architecture": "UKB",
                 "entity": "Hartwell UK", "title": "Relief Engineer",
                 "desc": "", "mapped_grade": "G4",
                 "last_reviewed": "2016-05", "status": "retired"})
    rows.append({"code": "UK-R02", "architecture": "UKB",
                 "entity": "Hartwell UK", "title": "Night Porter",
                 "desc": "", "mapped_grade": "F1",
                 "last_reviewed": "2016-05", "status": "retired"})
    OUT.mkdir(exist_ok=True)
    with (OUT / "job_catalog.csv").open("w", newline="") as f:
        f.write(TAG)
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(rows)

    # Local job codes for UK, NL and DE employees.
    emp_path = REPO / "fixtures" / "hartwell" / "employees.csv.gz"
    with gzip.open(emp_path, "rt") as f:
        emps = list(csv.DictReader(l for l in f if not l.startswith("#")))
    active = [r for r in rows if r["status"] == "active"]
    by_ent = {}
    for r in active:
        by_ent.setdefault(r["entity"], []).append(r["code"])
    out = []
    ents = ("Hartwell UK", "Hartwell Netherlands", "Hartwell Germany")
    by_grade = {}
    for r in active:
        by_grade.setdefault((r["entity"], r["mapped_grade"]),
                            []).append(r["code"])
    for e in emps:
        if e["entity"] not in ents:
            continue
        pool = by_grade.get((e["entity"], e["grade"]))
        code = rng.choice(pool or by_ent[e["entity"]])
        out.append({"employee_id": e["employee_id"],
                    "entity": e["entity"], "grade": e["grade"],
                    "local_code": code})
    uk = [o for o in out if o["entity"] == "Hartwell UK"]
    de = [o for o in out if o["entity"] == "Hartwell Germany"]
    for o in rng.sample(uk, 97):          # people on retired codes
        o["local_code"] = rng.choice(["UK-R01", "UK-R02"])
    for o in rng.sample(de, 41):          # no local code at all
        o["local_code"] = ""
    with (OUT / "local_codes.csv").open("w", newline="") as f:
        f.write(TAG)
        w = csv.DictWriter(f, ["employee_id", "entity", "grade",
                               "local_code"])
        w.writeheader()
        w.writerows(out)
    print(f"catalog {len(rows)} codes; local codes {len(out)} people")


if __name__ == "__main__":
    main()
