# Strategic HR in the Age of Agentic AI, Chapter 4: Seats and People
# Listing: Widening Raw Intervals to Their Stated Coverage (Under the Hood)

import numpy as np

def conformal_margin(lo, hi, y, alpha=0.20):
    """Split conformal on held-out forecast origins: how far must the raw
    intervals stretch so that (1 - alpha) of outcomes fall inside?"""
    scores = np.maximum(lo - y, y - hi)          # positive when y falls outside
    n = len(scores)
    k = int(np.ceil((n + 1) * (1 - alpha)))       # finite-sample rank
    return np.sort(scores)[min(k, n) - 1]         # widen to [lo - q, hi + q]
