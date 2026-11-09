"""Seeded generator for every synthetic organization in the book.

Book use: Chapter 1 (the 412 replay) builds on these files, and later
chapters read them for workforce, requisition and sector examples.

Everything here is invented. No real person, employer or applicant
appears. Each JSON file carries a "_synthetic" key and each CSV starts
with a "# _synthetic" comment line. The seed is fixed, so a re-run
writes byte-identical files (tests/test_fixtures.py checks this).

Run:  python3 fixtures/generate.py          (writes fixtures/...)
      python3 fixtures/generate.py --check  (verify, write nothing)

Sizes follow 00-plan/running-cases.md and continuity.md:
  Hartwell Group 38,000 employees (January 1, 2027)
  the 412 Smart Shortlist batch on REQ-FT-2027-0118 and -0131,
  1,031 applicants on those two requisitions by close
  sector organizations at their stated sizes (CSV gzipped)
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20270101
SYN = "Invented for the book. No real person, employer or applicant."
CSV_HEAD = "# _synthetic: " + SYN + "\n"

# ---------------------------------------------------------------- helpers


def _csv_bytes(rows: list[dict], cols: list[str]) -> bytes:
    buf = io.StringIO()
    buf.write(CSV_HEAD)
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return buf.getvalue().encode()


def _json_bytes(obj) -> bytes:
    return (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode()


def _gz(data: bytes) -> bytes:
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=0) as g:
        g.write(data)
    return out.getvalue()


def _pick(rng: random.Random, weights: dict):
    keys = list(weights)
    return rng.choices(keys, weights=[weights[k] for k in keys])[0]


def _date_between(rng, start: date, end: date) -> str:
    return (start + timedelta(rng.randrange((end - start).days))).isoformat()


# ------------------------------------------------------------ workforce

EMP_COLS = ["employee_id", "entity", "country", "site", "unit",
            "worker_type", "job_family", "grade", "union_or_council",
            "payroll", "hire_date", "fte", "age_band", "gender",
            "manager_id"]

AGE = {"18-24": 11, "25-29": 14, "30-39": 26, "40-49": 23,
       "50-59": 19, "60+": 7}
GENDER = {"F": 34, "M": 62, "X": 1, "undisclosed": 3}


def _people(rng, prefix: str, groups: list[dict]) -> list[dict]:
    """Expand group specs into employee rows with managers."""
    rows: list[dict] = []
    n = 0
    for g in groups:
        sites = g["sites"]
        fams = g["families"]
        gender = g.get("gender", GENDER)
        lead = None
        team = 0
        span = g.get("span", 9)
        for i in range(g["n"]):
            n += 1
            eid = f"{prefix}-{n:06d}"
            if team == 0:
                lead = rows[-1]["employee_id"] if rows and i else ""
            team = (team + 1) % span
            fam = _pick(rng, fams)
            rows.append({
                "employee_id": eid,
                "entity": g["entity"],
                "country": g["country"],
                "site": _pick(rng, sites),
                "unit": g.get("unit", ""),
                "worker_type": g["worker_type"],
                "job_family": fam,
                "grade": rng.choice(g.get("grades", ["G3", "G4", "G5"])),
                "union_or_council": g.get("union", ""),
                "payroll": g["payroll"],
                "hire_date": _date_between(
                    rng, date(g.get("since", 2004), 1, 1),
                    date(2026, 12, 31)),
                "fte": "1.0" if rng.random() > g.get("pt", 0.04)
                else rng.choice(["0.5", "0.6", "0.8"]),
                "age_band": _pick(rng, g.get("age", AGE)),
                "gender": _pick(rng, gender),
                "manager_id": lead or "",
            })
    return rows


FIELD = {"Field Service Technician": 34, "Facilities Operative": 26,
         "Electrician": 9, "HVAC Technician": 11, "Site Supervisor": 6,
         "Security Officer": 8, "Cleaning Operative": 6}
OFFICE = {"Project Management": 18, "Engineering": 22, "Finance": 12,
          "Sales and Bids": 9, "IT": 8, "Procurement": 6,
          "Operations Management": 20, "Legal and Compliance": 2,
          "HR": 3}
ENERGY = {"Energy Technician": 55, "Instrumentation Technician": 15,
          "Lineworker": 18, "Site Supervisor": 7,
          "Health and Safety": 5}
US_STATES = {"CO": 14, "TX": 12, "IL": 9, "NY": 8, "CA": 10, "AZ": 4,
             "GA": 4, "FL": 5, "NC": 4, "OH": 3, "PA": 4, "WA": 3,
             "NJ": 3, "MA": 3, "MI": 2, "MN": 2, "MO": 2, "TN": 2,
             "VA": 2, "UT": 2, "NV": 1, "OR": 1}


def hartwell_groups() -> list[dict]:
    us_field_states = dict(US_STATES)
    for k in ("IL", "NY", "CA"):  # union locals counted separately
        us_field_states.pop(k)
    us_ob = "outsourced (US bureau)"
    return [
        # Hartwell US 24,500 = 6,000 salaried + 18,500 field
        dict(entity="Hartwell US", country="US", n=6000,
             sites={"Denver, CO": 40, "Houston, TX": 12,
                    "Chicago, IL": 12, "New York, NY": 10,
                    "Los Angeles, CA": 10, "Atlanta, GA": 8,
                    "Phoenix, AZ": 8},
             worker_type="salaried", families=OFFICE, payroll=us_ob,
             grades=["G4", "G5", "G6", "G7", "G8"]),
        dict(entity="Hartwell US", country="US", n=1400,
             sites={"Chicago, IL": 60, "Joliet, IL": 40},
             worker_type="field", families=FIELD, payroll=us_ob,
             union="Local (Illinois)", grades=["F1", "F2", "F3"]),
        dict(entity="Hartwell US", country="US", n=1150,
             sites={"New York, NY": 80, "Albany, NY": 20},
             worker_type="field", families=FIELD, payroll=us_ob,
             union="Local (New York)", grades=["F1", "F2", "F3"]),
        dict(entity="Hartwell US", country="US", n=1300,
             sites={"Los Angeles, CA": 60, "Oakland, CA": 40},
             worker_type="field", families=FIELD, payroll=us_ob,
             union="Local (California)", grades=["F1", "F2", "F3"]),
        dict(entity="Hartwell US", country="US", n=2900,
             unit="Hartwell Energy Services",
             sites={"Midland, TX": 40, "Houston, TX": 30,
                    "Pueblo, CO": 30},
             worker_type="field", families=ENERGY, payroll=us_ob,
             grades=["F2", "F3", "F4"]),
        dict(entity="Hartwell US", country="US", n=11750,
             sites={f"field, {s}": w for s, w in
                    us_field_states.items()},
             worker_type="field", families=FIELD, payroll=us_ob,
             grades=["F1", "F2", "F3"], pt=0.08,
             age={"18-24": 16, "25-29": 17, "30-39": 25,
                  "40-49": 20, "50-59": 16, "60+": 6}),
        # Hartwell Canada 4,000
        dict(entity="Hartwell Canada", country="CA", n=1100,
             unit="Hartwell Energy Services Canada",
             sites={"Fort McMurray, AB (rotation)": 70,
                    "Calgary, AB": 30},
             worker_type="field", families=ENERGY,
             payroll="outsourced (Canada bureau)"),
        dict(entity="Hartwell Canada", country="CA", n=2900,
             sites={"Calgary, AB": 40, "Toronto, ON": 35,
                    "Montreal, QC": 25},
             worker_type="field", families=FIELD | OFFICE,
             payroll="outsourced (Canada bureau)"),
        # Hartwell UK 3,200, union recognized for 1,400 site staff
        dict(entity="Hartwell UK", country="GB", n=1400,
             sites={"Manchester": 30, "Leeds": 20, "Birmingham": 20,
                    "Glasgow": 15, "London": 15},
             worker_type="field", families=FIELD,
             union="recognized union (UK site staff)",
             payroll="in-house (UK)"),
        dict(entity="Hartwell UK", country="GB", n=1800,
             sites={"Manchester": 50, "London": 30, "Edinburgh": 20},
             worker_type="salaried", families=OFFICE | FIELD,
             payroll="in-house (UK)"),
        dict(entity="Hartwell Netherlands", country="NL", n=900,
             sites={"Rotterdam": 100}, worker_type="field",
             families=FIELD | OFFICE, union="Ondernemingsraad",
             payroll="in-house (Netherlands)"),
        dict(entity="Hartwell Germany", country="DE", n=1100,
             sites={"Dusseldorf": 70, "Cologne": 30},
             worker_type="field", families=FIELD | OFFICE,
             union="Betriebsrat", payroll="in-house (Germany)"),
        dict(entity="Hartwell Australia", country="AU", n=1600,
             sites={"Brisbane, QLD": 45, "Mackay, QLD": 25,
                    "Sydney, NSW": 30},
             worker_type="field", families=FIELD | OFFICE,
             union="enterprise agreement",
             payroll="in-house (Australia)"),
        # capability center 1,400: 260 HR ops, 90 analytics, 1,050
        dict(entity="Hartwell Global Capability Center", country="IN",
             n=260, unit="HR operations", sites={"Hyderabad": 1},
             worker_type="salaried",
             families={"Payroll Operations (Gulf)": 30,
                       "HR Data Validation": 20,
                       "HR Helpdesk Tier 2": 25,
                       "Recruiting Coordination (US field)": 15,
                       "Background-Check Coordination": 10},
             payroll="in-house (India)", since=2019),
        dict(entity="Hartwell Global Capability Center", country="IN",
             n=90, unit="People analytics and HR tech",
             sites={"Hyderabad": 1}, worker_type="salaried",
             families={"People Analytics": 40,
                       "HR-Tech Engineering": 60},
             payroll="in-house (India)", since=2019),
        dict(entity="Hartwell Global Capability Center", country="IN",
             n=1050, unit="Finance and engineering",
             sites={"Hyderabad": 1}, worker_type="salaried",
             families={"Finance": 45, "Engineering": 55},
             payroll="in-house (India)", since=2019),
        dict(entity="Hartwell Middle East", country="AE", n=500,
             sites={"Dubai": 1}, worker_type="field",
             families=FIELD | {"HR": 2},
             payroll="run from Hyderabad (Gulf)", since=2012),
        dict(entity="Hartwell Middle East", country="SA", n=600,
             sites={"Riyadh": 1}, worker_type="field",
             families=FIELD | {"HR": 2},
             payroll="run from Hyderabad (Gulf)", since=2014),
        dict(entity="Hartwell APAC hub", country="SG", n=200,
             sites={"Singapore": 1}, worker_type="salaried",
             families={"Finance": 50, "Procurement": 25, "HR": 8,
                       "Sales and Bids": 17},
             payroll="in-house (Singapore)", since=2015),
    ]


HARTWELL_ORG = {
    "_synthetic": SYN,
    "name": "Hartwell Group",
    "hq": "Denver, Colorado",
    "as_of": "2027-01-01",
    "employees": 38000,
    "entities": {"Hartwell US": 24500, "Hartwell Canada": 4000,
                 "Hartwell UK": 3200, "Hartwell Netherlands": 900,
                 "Hartwell Germany": 1100, "Hartwell Australia": 1600,
                 "Hartwell Global Capability Center": 1400,
                 "Hartwell Middle East": 1100,
                 "Hartwell APAC hub": 200},
    "hr_function": {"hr_staff_group": 340, "west": 310,
                    "gulf_and_singapore": 30,
                    "capability_center_hr_ops": 260,
                    "meridian_seats": 450},
    "systems": {"HRIS": "HartwellOne (2016)",
                "ATS": "Hartwell Careers on Talentra",
                "employee_service": "AskHartwell",
                "gateway": "Hartwell Gate"},
    "peak_hires_per_month": 1900,
    "cast": ["Claire Whitfield (CPO)", "Daniel Brooks (Head of TA)",
             "Megan Hale (HR Shared Services)",
             "Tom Reilly (People Analytics)", "Mark Ellison (CIO)",
             "Nathan Cole (enterprise architect)",
             "Helen Marsh (HR Director, UK)",
             "Ananya Rao (site head, Hyderabad)"],
}

# ------------------------------------------------ the 412 batch (ch01)

REQS = {
    # ranked at the Friday batch, bottom half moved, later arrivals
    "REQ-FT-2027-0118": dict(ranked=452, later=118,
                             title="Field Service Technician",
                             site="Denver, Colorado", state="CO"),
    "REQ-FT-2027-0131": dict(ranked=372, later=89,
                             title="Field Service Technician",
                             site="Joliet, Illinois", state="IL"),
}
CERTS = ["EPA 608 Universal", "EPA 608 Type I", "EPA 608 Type II",
         "NATE Core", "OSHA 10", "OSHA 30",
         "Journeyman electrician (IL)", "CDL Class B"]
SLICE = HERE / "hartwell" / "smart-shortlist-412-slice.json"
# recruiters later invited 14 from the batch (continuity.md); these
# two are fixed so chapters can name them; the rest are drawn
INVITED_FIXED = ["C-0412-118", "C-0412-201"]
APP_COLS = ["candidate_id", "requisition", "applied_at", "status_fri",
            "talentra_score", "rank_on_req", "batch_rank",
            "years_field_service", "employment_gap_months",
            "certifications", "recruiter_invited"]
SELF_ID_COLS = ["candidate_id", "sex", "age_40_plus",
                "race_ethnicity", "veteran", "disability"]
RACE = {"White": 52, "Hispanic or Latino": 22,
        "Black or African American": 13, "Asian": 4,
        "Two or more races": 3, "declined": 6}


def _cand_attrs(rng, older: bool, female: bool) -> dict:
    gap_p = 0.25 + (0.15 if older else 0) + (0.15 if female else 0)
    gap = rng.choice([3, 6, 9, 12, 14, 18, 24, 26, 30, 36]) \
        if rng.random() < gap_p else rng.choice([0, 0, 0, 1, 2])
    yrs = max(0, int(rng.gauss(9 if older else 4, 3)))
    certs = sorted(rng.sample(CERTS, k=_pick(
        rng, {0: 20, 1: 35, 2: 30, 3: 15})))
    return dict(years_field_service=yrs, employment_gap_months=gap,
                certifications=certs)


def _talentra(a: dict, rng) -> float:
    """The vendor's opaque fit score, as we model it: keyword-heavy,
    with a steep penalty for any employment gap."""
    s = 40 + 3.0 * min(a["years_field_service"], 10)
    s += 6 * len(a["certifications"])
    s -= 0.9 * a["employment_gap_months"]
    return round(s + rng.gauss(0, 6), 1)


def _self_id(rng) -> dict:
    older = rng.random() < 0.34
    female = rng.random() < 0.09
    sex = "F" if female else _pick(rng, {"M": 94, "declined": 6})
    return dict(sex=sex, age_40_plus="Y" if older else "N",
                race_ethnicity=_pick(rng, RACE),
                veteran=_pick(rng, {"Y": 11, "N": 84,
                                    "declined": 5}),
                disability=_pick(rng, {"Y": 5, "N": 87,
                                       "declined": 8}),
                _older=older, _female=female)


def batch_412(rng):
    """Every applicant on the two requisitions, the 412 batch and the
    recruiters' later invitations. The ten slice rows are kept as
    they are in smart-shortlist-412-slice.json."""
    slice_ = json.loads(SLICE.read_text())
    fixed = {c["id"]: c for c in slice_["candidates"]}
    fixed_rank = {c["shortlist_rank"]: c["id"] for c in
                  slice_["candidates"]}
    per_req = {r: v["ranked"] // 2 for r, v in REQS.items()}
    assert sum(per_req.values()) == 412
    need = dict(per_req)
    for c in fixed.values():
        need[c["requisition"]] -= 1
    free_ids = [f"C-0412-{i:03d}" for i in range(1, 413)
                if f"C-0412-{i:03d}" not in fixed]
    rng.shuffle(free_ids)
    selfid, pool = {}, []
    for cid in free_ids:
        req = "REQ-FT-2027-0118" if need["REQ-FT-2027-0118"] and (
            not need["REQ-FT-2027-0131"] or rng.random() < 0.55) \
            else "REQ-FT-2027-0131"
        need[req] -= 1
        sid = _self_id(rng)
        a = _cand_attrs(rng, sid["_older"], sid["_female"])
        a["employment_gap_months"] = max(
            a["employment_gap_months"], 0)
        pool.append(dict(id=cid, requisition=req, **a,
                         _raw=_talentra(a, rng) - 25))
        selfid[cid] = sid
    for cid in fixed:
        selfid[cid] = _self_id(rng)
    pool.sort(key=lambda c: -c["_raw"])
    ranked, it = [], iter(pool)
    for rank in range(1, 413):
        if rank in fixed_rank:
            c = dict(fixed[fixed_rank[rank]])
            c.pop("shortlist_rank")
        else:
            c = next(it)
        c["shortlist_rank"] = rank
        ranked.append(c)
    # score falls with rank; slice rows get the value at their rank
    scores = sorted((c["_raw"] for c in pool), reverse=True)
    top, bottom = scores[0] + 2, scores[-1] - 2
    for c in ranked:
        frac = (c["shortlist_rank"] - 1) / 411
        c["talentra_score"] = round(top - (top - bottom) * frac, 1)
        c.pop("_raw", None)
    # recruiters' later invitations: 14 from the batch
    rest = [c["id"] for c in ranked if c["id"] not in INVITED_FIXED]
    weights = [1 + min(c["years_field_service"], 12) for c in ranked
               if c["id"] not in INVITED_FIXED]
    invited = set(INVITED_FIXED)
    while len(invited) < 14:
        invited.add(rng.choices(rest, weights=weights)[0])
    batch = []
    for c in ranked:
        batch.append({
            "id": c["id"], "requisition": c["requisition"],
            "shortlist_rank": c["shortlist_rank"],
            "talentra_score": c["talentra_score"],
            "years_field_service": c["years_field_service"],
            "employment_gap_months": c["employment_gap_months"],
            "certifications": c["certifications"],
            "set_to": "not_progressed",
            "set_by": "talentra.smart_shortlist",
            "recruiter_id": None, "reason_code": None,
            "recruiter_invited_later": c["id"] in invited})
    return batch, selfid


def applicants(rng, batch, selfid):
    """All 1,031 applicants: the kept top half, the 412, later
    arrivals. Recruiters invited 61 in all, 14 of them from the 412."""
    rows = []
    lo = {r: min(c["talentra_score"] for c in batch
                 if c["requisition"] == r) for r in REQS}
    hi = {r: max(c["talentra_score"] for c in batch
                 if c["requisition"] == r) for r in REQS}
    kept_all = []
    for req, spec in REQS.items():
        code = req[-4:]
        k = spec["ranked"] - spec["ranked"] // 2
        kept = []
        for i in range(k):
            cid = f"C-{code}-K{i + 1:03d}"
            sid = _self_id(rng)
            a = _cand_attrs(rng, sid["_older"], sid["_female"])
            a["employment_gap_months"] = min(
                a["employment_gap_months"], 6)
            sc = round(hi[req] + 0.5 + abs(rng.gauss(0, 9)), 1)
            kept.append(dict(candidate_id=cid, requisition=req,
                             status_fri="applied", talentra_score=sc,
                             **a))
            selfid[cid] = sid
        kept.sort(key=lambda r: -r["talentra_score"])
        for i, r in enumerate(kept, 1):
            r["rank_on_req"] = i
        kept_all += kept
        mine = sorted((c for c in batch if c["requisition"] == req),
                      key=lambda c: c["shortlist_rank"])
        for j, c in enumerate(mine, k + 1):
            rows.append(dict(
                candidate_id=c["id"], requisition=req,
                status_fri="not_progressed",
                talentra_score=c["talentra_score"], rank_on_req=j,
                batch_rank=c["shortlist_rank"],
                years_field_service=c["years_field_service"],
                employment_gap_months=c["employment_gap_months"],
                certifications=c["certifications"],
                recruiter_invited="Y" if c["recruiter_invited_later"]
                else "N"))
        for i in range(spec["later"]):
            cid = f"C-{code}-L{i + 1:03d}"
            sid = _self_id(rng)
            a = _cand_attrs(rng, sid["_older"], sid["_female"])
            rows.append(dict(candidate_id=cid, requisition=req,
                             status_fri="not_yet_applied", **a,
                             recruiter_invited="N"))
            selfid[cid] = sid
        assert lo[req] < hi[req]
    # 47 invitations from the kept top half, weighted to the top
    pick = set()
    while len(pick) < 47:
        r = rng.choices(kept_all, weights=[
            1 / (x["rank_on_req"] ** 0.5) for x in kept_all])[0]
        pick.add(r["candidate_id"])
    for r in kept_all:
        r["recruiter_invited"] = "Y" if r["candidate_id"] in pick \
            else "N"
    rows = kept_all + rows
    day = {"applied": (date(2027, 1, 11), date(2027, 2, 5)),
           "not_progressed": (date(2027, 1, 11), date(2027, 2, 5)),
           "not_yet_applied": (date(2027, 2, 6), date(2027, 2, 26))}
    for r in rows:
        r["applied_at"] = _date_between(rng, *day[r["status_fri"]])
        r["certifications"] = "; ".join(r["certifications"])
    rows.sort(key=lambda r: (r["requisition"], r["candidate_id"]))
    return rows


def requisitions(rng) -> list[dict]:
    """Hartwell Careers requisitions open on February 5, 2027. Only
    the two field-technician roles had more than 200 applicants, so
    only they were touched by the Smart Shortlist default."""
    rows = []
    for req, spec in REQS.items():
        rows.append(dict(requisition=req, title=spec["title"],
                         site=spec["site"], country="US",
                         applicants_feb5=spec["ranked"],
                         applicants_at_close=spec["ranked"]
                         + spec["later"],
                         over_200_on_feb5="Y"))
    titles = list(FIELD) + ["Project Engineer", "Payroll Analyst",
                            "Bid Manager", "HR Business Partner"]
    for i in range(1, 641):
        n = min(int(rng.lognormvariate(3.3, 0.8)), 196)
        st = _pick(rng, US_STATES)
        rows.append(dict(requisition=f"REQ-HW-2027-{i:04d}",
                         title=rng.choice(titles),
                         site=f"field, {st}", country="US",
                         applicants_feb5=n,
                         applicants_at_close=n + rng.randrange(0, 40),
                         over_200_on_feb5="N"))
    return rows


# --------------------------------------- ch01 sector incidents

def ashby_lowe_screening(rng) -> dict:
    """Ashby & Lowe: the HR suite's bundled auto-screen, switched on
    for one warehouse requisition. It declined anyone whose form did
    not contain its keyword list, so 'FLT' did not count."""
    apps = []
    for i in range(1, 65):
        has_cert = rng.random() < 0.55
        wrote = _pick(rng, {"counterbalance forklift": 45,
                            "FLT": 35, "reach truck": 20}) \
            if has_cert else ""
        keyword = wrote in ("counterbalance forklift", "reach truck")
        years = rng.randrange(0, 12)
        declined = not keyword or years < 1
        apps.append(dict(applicant=f"AL-WH-{i:03d}",
                         forklift_certificate=has_cert,
                         certificate_written_as=wrote,
                         years_warehouse=years,
                         auto_declined=declined))
    return {"_synthetic": SYN,
            "org": "Ashby & Lowe Distribution",
            "requisition": "Warehouse Operative, Leicester",
            "feature": "bundled auto-screen (vendor default rules)",
            "switched_on_by": "Rachel Okafor, HR Manager",
            "applicants": apps}


def brightwater_bookings(rng) -> dict:
    """Brightwater: the plant-hiring chatbot books, cancels and
    rebooks shift interviews when a supervisor calendar changes."""
    rows = []
    start = date(2027, 3, 1)
    for i in range(1, 287):
        d = start + timedelta(rng.randrange(7))
        ev = {"booking": f"BW-OH-{i:04d}", "date": d.isoformat(),
              "shift": rng.choice(["first", "second", "third"]),
              "booked_by": "chatbot", "cancelled_by_bot": False,
              "rebooked": "", "candidate_told": ""}
        if rng.random() < 0.26:  # supervisor calendar sync moved
            ev["cancelled_by_bot"] = True
            ev["rebooked"] = _pick(rng, {"same week": 55,
                                         "later week": 15,
                                         "not rebooked": 30})
            ev["candidate_told"] = _pick(rng, {"text": 70,
                                               "none": 30})
        rows.append(ev)
    return {"_synthetic": SYN, "org": "Brightwater Brands",
            "site": "Ohio plant OH-2", "week_of": "2027-03-01",
            "bookings": rows}


SECTORS = {
    "brightwater": ("Brightwater Brands", "Cincinnati, Ohio", [
        dict(entity="Brightwater US", country="US", n=9000,
             sites={"Ohio plant OH-1": 35, "Ohio plant OH-2": 35,
                    "Ohio plant OH-3": 30},
             worker_type="plant shift", families={"Production": 80,
                                                  "Maintenance": 12,
                                                  "Quality": 8},
             payroll="in-house (US)"),
        dict(entity="Brightwater UK", country="GB", n=1600,
             sites={"Leeds plant": 1}, worker_type="plant shift",
             families={"Production": 85, "Maintenance": 15},
             payroll="in-house (UK)"),
        dict(entity="Brightwater NL", country="NL", n=1300,
             sites={"Tilburg plant": 1}, worker_type="plant shift",
             families={"Production": 85, "Maintenance": 15},
             union="Ondernemingsraad", payroll="in-house (NL)"),
        dict(entity="Brightwater PL", country="PL", n=1100,
             sites={"Lodz plant": 1}, worker_type="plant shift",
             families={"Production": 85, "Maintenance": 15},
             payroll="in-house (PL)"),
        dict(entity="Brightwater US", country="US", n=3500,
             sites={"field sales, US": 70, "field sales, UK": 15,
                    "field sales, NL": 8, "field sales, PL": 7},
             worker_type="field sales",
             families={"Key Account Sales": 30,
                       "Territory Sales": 70},
             payroll="in-house (US)"),
        dict(entity="Brightwater US", country="US", n=4500,
             sites={"Cincinnati HQ": 1}, worker_type="salaried",
             families=OFFICE, payroll="in-house (US)"),
    ], "Nadia Ferreira, VP HR Operations"),
    "calder-bank": ("Calder Bank", "Charlotte, North Carolina", [
        dict(entity="Calder Bank US", country="US", n=12400,
             sites={"Charlotte, NC": 55, "branches, NC/SC/VA": 45},
             worker_type="salaried",
             families={"Retail Banking": 40, "Operations": 20,
                       "Risk and Compliance": 12, "Technology": 18,
                       "Finance": 6, "HR": 4},
             payroll="in-house (US)"),
        dict(entity="Calder Bank UK", country="GB", n=3600,
             sites={"Edinburgh": 1}, worker_type="salaried",
             families={"Operations": 40, "Technology": 25,
                       "Risk and Compliance": 20, "HR": 4,
                       "Retail Banking": 11},
             payroll="in-house (UK)"),
    ], "Andrew Kerr, Head of HR Technology and Controls"),
    "hollis": ("Hollis Precision", "Grand Rapids, Michigan", [
        dict(entity="Hollis US", country="US", n=4300,
             sites={"Grand Rapids plant": 1}, worker_type="hourly",
             families={"CNC Machinist": 45, "Assembly": 35,
                       "Maintenance": 20},
             union="union local (Michigan)", payroll="in-house"),
        dict(entity="Hollis Canada", country="CA", n=1100,
             sites={"Ontario plant": 1}, worker_type="hourly",
             families={"CNC Machinist": 50, "Assembly": 50},
             payroll="in-house"),
        dict(entity="Hollis CZ", country="CZ", n=1000,
             sites={"Plzen plant": 1}, worker_type="hourly",
             families={"CNC Machinist": 50, "Assembly": 50},
             union="employee council", payroll="in-house"),
    ], "Teresa Novak, Plant HR Manager"),
    "pennant": ("Pennant Stores", "Toronto, Ontario", [
        dict(entity="Pennant Canada", country="CA", n=30000,
             sites={f"store CA-{i:03d}": 1 for i in range(1, 201)},
             worker_type="hourly", pt=0.55,
             families={"Store Associate": 85, "Shift Lead": 10,
                       "Store Manager": 5}, payroll="in-house"),
        dict(entity="Pennant US", country="US", n=16500,
             sites={f"store US-{i:03d}": 1 for i in range(1, 111)},
             worker_type="hourly", pt=0.55,
             families={"Store Associate": 85, "Shift Lead": 10,
                       "Store Manager": 5}, payroll="in-house"),
        dict(entity="Pennant Canada", country="CA", n=1500,
             sites={"Toronto HQ": 1}, worker_type="salaried",
             families=OFFICE, payroll="in-house"),
    ], "Elena Harlow, Director of Store HR"),
    "restonmere": ("Restonmere Hotels", "London", [
        dict(entity="Restonmere", country=c, n=n,
             sites={f"hotel {c}-{i:02d}": 1 for i in range(1, h + 1)},
             worker_type="hourly", pt=0.3,
             families={"Front Desk": 20, "Housekeeping": 35,
                       "Food and Beverage": 35, "Management": 10},
             payroll="in-house")
        for c, n, h in (("GB", 5200, 19), ("IE", 1300, 5),
                        ("US", 3100, 10), ("AU", 1400, 6))
    ], "Siobhan Doyle, Group People Director"),
    "westbridge": ("Westbridge City Council", "English Midlands", [
        dict(entity="Westbridge City Council", country="GB", n=7500,
             sites={"Civic Centre": 30, "depots": 25,
                    "care services": 30, "libraries": 15},
             worker_type="salaried", pt=0.25,
             families={"Social Care": 30, "Waste and Streets": 20,
                       "Administration": 25, "Housing": 15,
                       "HR": 2, "Planning": 8},
             union="public-sector unions", payroll="shared service"),
    ], "Owen Lewis, Head of HR and OD"),
    "thorne-kessler": ("Thorne Kessler", "New York", [
        dict(entity="Thorne Kessler", country=c, n=n,
             sites={city: 1}, worker_type="salaried",
             families={"Audit": 40, "Advisory": 35, "Tax": 20,
                       "HR": 5}, payroll="in-house")
        for c, n, city in (("US", 3600, "New York"),
                           ("GB", 2200, "London"),
                           ("AU", 1000, "Sydney"))
    ], "Priya Raman, Chief People Officer"),
    "aurelia": ("Aurelia Telecom", "Toronto, Ontario", [
        dict(entity="Aurelia Canada", country="CA", n=14500,
             sites={"Toronto": 40, "field, ON": 35, "field, QC": 25},
             worker_type="salaried",
             families={"Network Engineering": 30,
                       "Field Technician": 35, "Retail": 15,
                       "Technology": 15, "HR": 5},
             payroll="in-house"),
        dict(entity="Aurelia NL", country="NL", n=4500,
             sites={"Utrecht": 1}, worker_type="salaried",
             families={"Network Engineering": 40,
                       "Field Technician": 40, "Technology": 20},
             union="Ondernemingsraad", payroll="in-house"),
    ], "Luc Bernard, VP People Systems"),
    "ashby-lowe": ("Ashby & Lowe Distribution", "Leicester", [
        dict(entity="Ashby & Lowe", country="GB", n=410,
             sites={"Leicester warehouse 1": 45,
                    "Leicester warehouse 2": 40,
                    "Belfast depot": 15},
             worker_type="hourly",
             families={"Warehouse Operative": 60, "Driver": 20,
                       "Office": 19, "HR": 1},
             payroll="payroll bureau"),
    ], "Rachel Okafor, HR Manager"),
}


# HR staff by entity: 310 in the West, 30 in the Gulf and Singapore
# (running-cases.md). Capability-center HR operations (260) are
# counted under their own job families.
HR_QUOTA = {"Hartwell US": 190, "Hartwell Canada": 35,
            "Hartwell UK": 40, "Hartwell Netherlands": 10,
            "Hartwell Germany": 12, "Hartwell Australia": 23,
            "Hartwell Middle East": 22, "Hartwell APAC hub": 8}


def _hr_quota(rng, rows: list[dict]) -> None:
    for r in rows:
        if r["job_family"] == "HR":
            r["job_family"] = "Operations Management"
    for ent, n in HR_QUOTA.items():
        mine = [r for r in rows if r["entity"] == ent]
        pool = [r for r in mine if r["job_family"] in OFFICE]
        if len(pool) < n:
            pool = mine
        for r in rng.sample(pool, n):
            r["job_family"] = "HR"
            r["worker_type"] = "salaried"


# ------------------------------------------------------------- build

def build() -> dict[str, bytes]:
    rng = random.Random(SEED)
    files: dict[str, bytes] = {}
    hw = _people(rng, "HW", hartwell_groups())
    assert len(hw) == 38000, len(hw)
    _hr_quota(rng, hw)
    files["hartwell/org.json"] = _json_bytes(HARTWELL_ORG)
    files["hartwell/employees.csv.gz"] = _gz(
        _csv_bytes(hw, EMP_COLS))
    files["hartwell/requisitions-2027-02-05.csv"] = _csv_bytes(
        requisitions(rng), ["requisition", "title", "site",
                            "country", "applicants_feb5",
                            "applicants_at_close",
                            "over_200_on_feb5"])
    batch, selfid = batch_412(rng)
    files["hartwell/smart-shortlist-412.json"] = _json_bytes({
        "_synthetic": SYN,
        "batch": "Smart Shortlist weekend batch, Friday "
                 "February 5, 2027: 412 applications set to "
                 "not_progressed",
        "rule": "vendor default: on requisitions with more than "
                "200 applicants, move the bottom half",
        "requisitions": {r: f"{v['title']}, {v['site']}"
                         for r, v in REQS.items()},
        "ranked_at_batch": {r: v["ranked"] for r, v in REQS.items()},
        "applicants_on_requisitions": sum(
            v["ranked"] + v["later"] for v in REQS.values()),
        "candidates": batch})
    apps = applicants(rng, batch, selfid)
    assert len(apps) == 1031
    files["hartwell/field-tech-applicants.csv"] = _csv_bytes(
        apps, APP_COLS)
    sid_rows = [dict(candidate_id=k, **{c: v[c] for c in
                                        SELF_ID_COLS[1:]})
                for k, v in sorted(selfid.items())]
    files["hartwell/applicant-self-id.csv"] = _csv_bytes(
        sid_rows, SELF_ID_COLS)
    for slug, (name, hq, groups, contact) in SECTORS.items():
        prefix = "".join(w[0] for w in slug.split("-")).upper()
        rows = _people(rng, prefix[:3] + "X", groups)
        files[f"sectors/{slug}/org.json"] = _json_bytes({
            "_synthetic": SYN, "name": name, "hq": hq,
            "employees": len(rows), "contact": contact})
        files[f"sectors/{slug}/employees.csv.gz"] = _gz(
            _csv_bytes(rows, EMP_COLS))
    files["sectors/ashby-lowe/auto-screen-warehouse.json"] = \
        _json_bytes(ashby_lowe_screening(rng))
    files["sectors/brightwater/ohio-chatbot-bookings.json"] = \
        _json_bytes(brightwater_bookings(rng))
    manifest = {k: hashlib.sha256(_plain(k, v)).hexdigest()
                for k, v in sorted(files.items())}
    files["MANIFEST.json"] = _json_bytes(
        {"_synthetic": SYN, "seed": SEED, "sha256": manifest})
    return files


def _plain(name: str, data: bytes) -> bytes:
    """Content without gzip framing, so zlib versions cannot differ."""
    return gzip.decompress(data) if name.endswith(".gz") else data


def main(argv: list[str]) -> int:
    files = build()
    if "--check" in argv:
        bad = [k for k, v in files.items()
               if not (HERE / k).exists()
               or _plain(k, (HERE / k).read_bytes()) != _plain(k, v)]
        print("fixtures match the generator" if not bad
              else "differ: " + ", ".join(bad))
        return 1 if bad else 0
    for k, v in files.items():
        p = HERE / k
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(v)
        print(f"{len(v):>10,}  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
