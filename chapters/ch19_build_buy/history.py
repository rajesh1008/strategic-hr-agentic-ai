"""Chapter 19: a small model trained on Hartwell's history.

Book section "Fine-tune or retrieve: the removed rule comes
back". Northgate's optional Fit Match add-on (synthetic)
offered to "learn Hartwell's hiring standard" from past
phone-first decisions. Before buying it, Hartwell built the
same thing in miniature: a logistic regression trained on
the 4,800 Q4 2026 applications outside the agent sample,
labeled with what the old configuration did to them, and
scored it on the 1,200-applicant agent sample from
Chapter 7 against the posted requirements.

Three versions of the small model:
  H1  trained on the old outcomes, all features
  H2  trained on the old outcomes, the gap column dropped
  H3  trained on outcomes relabeled by the posted rule
No model API is involved; pure Python, fixed seed.
"""
from __future__ import annotations

import math
import random

from chapters.ch07_adverse_impact.make_data import load

SEED = 19
EPOCHS = 400
RATE = 0.5


def certs(a: dict) -> list[str]:
    return [c for c in a["certifications"].split("; ") if c]


def epa608(a: dict) -> bool:
    return any(c.startswith("EPA 608") for c in certs(a))


def posted(a: dict) -> bool:
    """Posted requirements: an EPA 608 certification of any
    type and at least 2 years of field service."""
    return epa608(a) and int(a["years_field_service"]) >= 2


def old_outcome(a: dict) -> bool:
    """What the old configuration did in Q4 2026: the posted
    requirements plus "no gap over six months", the
    criterion DR-07-01 removed on April 1, 2027."""
    return posted(a) and int(a["longest_gap_months"]) <= 6


FEATURES = {
    "years": lambda a: min(int(a["years_field_service"]),
                           20) / 20,
    "gap": lambda a: min(int(a["longest_gap_months"]),
                         48) / 48,
    "epa608": lambda a: float(epa608(a)),
    "any_cert": lambda a: float(bool(certs(a))),
    "n_certs": lambda a: len(certs(a)) / 3,
}


def vec(a: dict, cols: list[str]) -> list[float]:
    return [1.0] + [FEATURES[c](a) for c in cols]


def train(rows: list[dict], label, cols: list[str]):
    """Plain logistic regression by batch gradient descent."""
    xs = [vec(a, cols) for a in rows]
    ys = [1.0 if label(a) else 0.0 for a in rows]
    w = [0.0] * len(xs[0])
    for _ in range(EPOCHS):
        g = [0.0] * len(w)
        for x, y in zip(xs, ys):
            z = sum(wi * xi for wi, xi in zip(w, x))
            p = 1 / (1 + math.exp(-z))
            for j, xj in enumerate(x):
                g[j] += (p - y) * xj
        w = [wi - RATE * gi / len(xs) * 10
             for wi, gi in zip(w, g)]
    return w


def score(w: list[float], a: dict, cols: list[str]) -> float:
    z = sum(wi * xi for wi, xi in zip(w, vec(a, cols)))
    return 1 / (1 + math.exp(-z))


VERSIONS = {
    "H1": ("old outcomes, all features", old_outcome,
           ["years", "gap", "epa608", "any_cert", "n_certs"]),
    "H2": ("old outcomes, gap column dropped", old_outcome,
           ["years", "epa608", "any_cert", "n_certs"]),
    "H3": ("relabeled by the posted rule", posted,
           ["years", "gap", "epa608", "any_cert", "n_certs"]),
}


def split() -> tuple[list[dict], list[dict]]:
    apps = load("hartwell-q4-2026.csv")
    hist = [a for a in apps if a["agent_sample"] == "N"]
    new = [a for a in apps if a["agent_sample"] == "Y"]
    return hist, new


def fit_all() -> dict:
    """{version: (weights, cols, recommendations on new)}"""
    random.seed(SEED)
    hist, new = split()
    out = {}
    for v, (_, label, cols) in VERSIONS.items():
        w = train(hist, label, cols)
        recs = {a["candidate_id"]: score(w, a, cols) >= 0.5
                for a in new}
        out[v] = (w, cols, recs)
    return out
