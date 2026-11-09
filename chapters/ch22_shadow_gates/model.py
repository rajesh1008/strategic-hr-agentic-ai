"""Chapter 22: the attrition model, as people analytics built it.

Book section "The attrition model in shadow". A logistic
regression on eight quarters of history (synthetic), fitted
with plain numpy so every step can be read. Two versions:

  v1  label: "left within the quarter", taken from the HCM
      termination flag, so retirements count as leaving;
      inputs include the retirement-benefit milestone
  v2  label: resignations only (the Intent statement's
      outcome); the milestone input removed

The German lane never reads the pulse survey: the works
agreement for the shadow run excludes it (see shadow.py).
No model API is called; "model" here is the statistics.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .workforce import Person, outcome, people

INPUTS = {
    "v1": ["tenure", "since_promo", "compa", "new_mgr",
           "pulse", "milestone", "short_service"],
    "v2": ["tenure", "since_promo", "compa", "new_mgr",
           "pulse", "short_service"],
}
LABEL = {"v1": ("resigned", "retired"), "v2": ("resigned",)}
HISTORY = 8          # quarters, 2025Q3 to 2027Q2


def row(p: Person, names: list[str]) -> list[float]:
    v = {"tenure": p.tenure, "since_promo": p.since_promo,
         "compa": p.compa, "new_mgr": p.new_mgr,
         "pulse": p.pulse if p.pulse is not None else 0.0,
         "milestone": p.milestone,
         "short_service": float(p.tenure < 2)}
    return [v[n] for n in names]


@dataclass
class Fitted:
    version: str
    lane: str
    names: list[str]
    mean: np.ndarray
    sd: np.ndarray
    w: np.ndarray        # intercept first

    def score(self, ps: list[Person]) -> np.ndarray:
        x = np.array([row(p, self.names) for p in ps])
        z = (x - self.mean) / self.sd
        return 1 / (1 + np.exp(-(self.w[0] + z @ self.w[1:])))

    def drivers(self, p: Person, k: int = 3) -> list[str]:
        """The k inputs pushing this person's score up most."""
        z = (np.array(row(p, self.names)) - self.mean) / self.sd
        c = z * self.w[1:]
        top = np.argsort(-c)[:k]
        return [self.names[i] for i in top if c[i] > 0]


def history(lane: str, seed: int = 2200) -> list[tuple]:
    """(person, outcome) for each past quarter."""
    out = []
    for q in range(HISTORY):
        back = (HISTORY - q) * 0.25
        rng = np.random.default_rng(seed + q)
        for p in people(seed=seed + 100 + q, shift=back):
            if p.lane == lane:
                out.append((p, outcome(p, rng)))
    return out


def fit(version: str, lane: str) -> Fitted:
    names = [n for n in INPUTS[version]
             if not (lane == "DE" and n == "pulse")]
    hist = history(lane)
    x = np.array([row(p, names) for p, _ in hist])
    y = np.array([o in LABEL[version] for _, o in hist], float)
    mean, sd = x.mean(0), x.std(0) + 1e-9
    z = np.column_stack([np.ones(len(x)), (x - mean) / sd])
    w = np.zeros(z.shape[1])
    for _ in range(25):                 # Newton steps (IRLS)
        p = 1 / (1 + np.exp(-(z @ w)))
        g = z.T @ (y - p)
        h = (z * (p * (1 - p))[:, None]).T @ z
        w += np.linalg.solve(h + 1e-6 * np.eye(len(w)), g)
    return Fitted(version, lane, names, mean, sd, w)
