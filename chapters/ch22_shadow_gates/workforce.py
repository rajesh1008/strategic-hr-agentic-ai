"""Chapter 22: the population the attrition model scores.

Book sections "The attrition model in shadow" and "Hartwell
Germany: a shadow run designed with the Betriebsrat". Two
populations from the Hartwell fixture (synthetic):
  US   the 6,000 salaried employees of Hartwell US
  DE   the 1,100 employees of Hartwell Germany

The fixture gives age band, hire date and job family. This
module adds, with a fixed seed, the fields the model reads
and the quarter each person actually lives through. The
rules are stated so a reader can see why numbers look as
they do:
  resignation  more likely with pay below 0.92 of midpoint,
               a long wait since promotion, a new manager, a
               low pulse score, under two years' service;
               less likely from 50 and again from 60
  retirement   possible only from 55; likelier from 60 and
               at the retirement-benefit milestone
  milestone    "reached, or within 24 months of, the
               retirement-benefit milestone" (age 55 with 10
               years' service in the US retiree-medical plan,
               age 60 in the German company pension plan): a
               benefits field, not an age field, on paper
Age is never a model input. It is used only to test.

Everything is invented. No model is called.
"""
from __future__ import annotations

import csv
import gzip
from dataclasses import dataclass
from datetime import date

import numpy as np

from hrai.llm import REPO

SEED = 22
START = date(2027, 7, 12)      # shadow starts (Monday)
END = date(2027, 10, 8)        # 13 weeks later (Friday)
BANDS = ["18-24", "25-29", "30-39", "40-49", "50-59", "60+"]
SPAN = {"18-24": (18, 25), "25-29": (25, 30),
        "30-39": (30, 40), "40-49": (40, 50),
        "50-59": (50, 60), "60+": (60, 67)}
MILESTONE = {"US": (55, 10), "DE": (60, 0)}


@dataclass
class Person:
    id: str
    lane: str            # US or DE
    band: str
    age: float
    sex: str
    tenure: float        # years of service
    since_promo: float   # months since last promotion
    compa: float         # pay / range midpoint
    new_mgr: int         # manager changes, last 12 months
    pulse: float | None  # pulse survey (US only)
    milestone: int       # 0 or 1, see module docstring


def _fixture() -> list[dict]:
    path = REPO / "fixtures" / "hartwell" / "employees.csv.gz"
    with gzip.open(path, "rt") as f:
        rows = csv.DictReader(l for l in f if not l.startswith("#"))
        return [r for r in rows if
                (r["entity"] == "Hartwell US"
                 and r["worker_type"] == "salaried")
                or r["entity"] == "Hartwell Germany"]


def _milestone(lane: str, age: float, tenure: float) -> int:
    at_age, service = MILESTONE[lane]
    # years until both conditions hold
    wait = max(at_age - age, service - tenure, 0.0)
    return int(age >= at_age - 2 and wait <= 2.0)


def people(seed: int = SEED, as_of: date = START,
           shift: float = 0.0) -> list[Person]:
    """The population on `as_of`. `shift` (years) ages the
    draw backward, so history can be built from it."""
    rng = np.random.default_rng(seed)
    out = []
    for r in _fixture():
        lane = "US" if r["entity"] == "Hartwell US" else "DE"
        lo, hi = SPAN[r["age_band"]]
        age = rng.uniform(lo, hi) - shift
        hired = date.fromisoformat(r["hire_date"])
        tenure = max(0.1, (as_of - hired).days / 365.25 - shift)
        tenure = min(tenure, max(0.1, age - 18))
        since = min(tenure * 12, rng.gamma(2.0, 14.0))
        out.append(Person(
            id=r["employee_id"], lane=lane, band=_band(age),
            age=age, sex=r["gender"], tenure=tenure,
            since_promo=since,
            compa=float(np.clip(rng.normal(1.0, 0.09),
                                0.7, 1.3)),
            new_mgr=int(rng.poisson(0.35)),
            pulse=(float(np.clip(rng.normal(3.7, 0.6), 1, 5))
                   if lane == "US" else None),
            milestone=_milestone(lane, age, tenure)))
    return out


def _band(age: float) -> str:
    for b, (lo, hi) in SPAN.items():
        if lo <= age < hi:
            return b
    return "18-24" if age < 18 else "60+"


def hazards(p: Person) -> tuple[float, float]:
    """True quarterly chance of (resigning, retiring)."""
    x = (-4.6 + 1.2 * (p.compa < 0.92)
         + 0.25 * min(p.since_promo, 48) / 12
         + 0.5 * p.new_mgr + 0.9 * (p.tenure < 2)
         - 0.6 * ((p.pulse or 3.7) - 3.7)
         + 0.4 * (p.age < 30) - 0.5 * (p.age >= 50)
         - 0.6 * (p.age >= 60))
    resign = 1 / (1 + np.exp(-x))
    if p.age < 55:
        retire = 0.0
    else:
        y = (-4.6 if p.age < 60 else -3.0) + 0.9 * p.milestone
        retire = 1 / (1 + np.exp(-y))
    return float(resign), float(retire)


def outcome(p: Person, rng: np.random.Generator) -> str:
    """What happens to p in one quarter."""
    resign, retire = hazards(p)
    u = rng.random()
    if u < retire:
        return "retired"
    if u < retire + resign:
        return "resigned"
    return "stayed"
