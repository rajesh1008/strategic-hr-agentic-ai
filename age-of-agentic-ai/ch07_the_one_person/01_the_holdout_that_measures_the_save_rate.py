# Strategic HR in the Age of Agentic AI, Chapter 7: The One Person
# Listing: The Holdout That Measures the Save Rate (Under the Hood)
# The threshold of five leavers is a design choice; set it with your analyst before the cycle. A quarterly check compares women's predicted and actual leavers.

import random

def split_holdout(listed_ids, n_holdout=40, seed=2026):
    """Held-out people get no conversation and lose nothing they are owed."""
    ids = sorted(listed_ids)
    holdout = set(random.Random(seed).sample(ids, n_holdout))
    return [i for i in ids if i not in holdout], sorted(holdout)

def measured_save_rate(left_t, n_t, left_h, n_h):
    """Relative fall in leaving. None when the holdout has too few leavers."""
    if left_h < 5:
        return None                      # inconclusive, and reported as such
    return 1 - (left_t / n_t) / (left_h / n_h)
