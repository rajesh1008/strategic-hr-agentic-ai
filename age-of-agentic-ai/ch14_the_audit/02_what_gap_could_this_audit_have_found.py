# Strategic HR in the Age of Agentic AI, Chapter 14: The Audit
# Listing: What Gap Could This Audit Have Found? (Under the Hood)

from statistics import NormalDist
from math import sqrt

def detectable_gap(n_a, n_b, base,
                   alpha=0.05, power=0.80):
    """Smallest gap in selection rates
    this audit could reliably see."""
    z = NormalDist().inv_cdf
    se = sqrt(base * (1 - base)
              * (1 / n_a + 1 / n_b))
    return (z(1 - alpha / 2) + z(power)) * se

round(detectable_gap(60, 70, 0.20), 3)
# 0.197: a 20-point gap could hide
