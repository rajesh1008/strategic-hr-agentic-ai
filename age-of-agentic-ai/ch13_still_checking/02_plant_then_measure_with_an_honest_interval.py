# Strategic HR in the Age of Agentic AI, Chapter 13: Still Checking
# Listing: Plant, Then Measure With an Honest Interval (Under the Hood)
# Ten plants a month gives a wide interval: seven caught is consistent with anything from about 40% to 89%. Pool three months before calling a trend.

import math, random

def plant(queue, known_wrong, n=10, seed=None):
    """Plants look like live items; the flag that marks them is kept server-side."""
    rng = random.Random(seed)
    items = list(queue)
    for item in rng.sample(known_wrong, n):
        items.insert(rng.randrange(len(items) + 1), item)
    return items

def catch_rate(caught: int, planted: int, z: float = 1.96):
    """Wilson interval: honest when the monthly count of plants is small."""
    if planted == 0:
        return None
    p = caught / planted
    d = 1 + z * z / planted
    centre = (p + z * z / (2 * planted)) / d
    half = z * math.sqrt(p * (1 - p) / planted + z * z / (4 * planted ** 2)) / d
    return p, (centre - half, centre + half)

catch_rate(7, 10)        # (0.7, (0.397..., 0.892...)): one month says little
