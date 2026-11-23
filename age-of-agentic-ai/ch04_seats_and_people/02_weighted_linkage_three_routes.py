# Strategic HR in the Age of Agentic AI, Chapter 4: Seats and People
# Listing: Weighted Linkage, Three Routes (Under the Hood)
# Field weights are illustrative. Fit m and u on labelled pairs, and set both thresholds on held-out rows so auto-linked precision stays at 100%.

import math

FIELDS = {            # m: agrees on a true link; u: agrees by chance
    "cost_centre": (0.95, 0.05),
    "job_code": (0.90, 0.10),
    "country": (0.99, 0.30),
    "fte": (0.85, 0.40),
}

def match_weight(agree: dict[str, bool]) -> float:
    w = 0.0
    for f, (m, u) in FIELDS.items():
        w += math.log2(m / u) if agree[f] else math.log2((1 - m) / (1 - u))
    return w

def route(w: float, upper: float, lower: float) -> str:
    if w >= upper:
        return "auto_link"
    return "no_link" if w <= lower else "review"
