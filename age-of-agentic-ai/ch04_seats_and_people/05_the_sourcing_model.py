# Strategic HR in the Age of Agentic AI, Chapter 4: Seats and People
# Listing: The Sourcing Model (Under the Hood)
# Yields, costs and the release cap come from the plan file; the penalty prices a quarter of unmet demand. The constraint on borrowing is the line the chapter warns about.

import pulp

def plan(options, demand, quarters, penalty):
    """Least cash plus a penalty on unmet demand."""
    caps = {o.capability for o in options}
    keys = [(o.id, q) for o in options for q in quarters]
    gaps = [(c, q) for c in caps for q in quarters]
    m = pulp.LpProblem("sourcing", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("fte", keys, lowBound=0)
    short = pulp.LpVariable.dicts("short", gaps, lowBound=0)
    m += (pulp.lpSum(o.cost * x[o.id, q] for o, q in
                     ((o, q) for o in options for q in quarters))
          + penalty * pulp.lpSum(short.values()))
    for c, q in gaps:
        # build options carry the reskilling success probability
        supply = pulp.lpSum(o.yield_at(q) * x[o.id, q]
                            for o in options if o.capability == c)
        m += supply + short[c, q] >= demand[c, q]
    for o in options:
        if o.lever == "borrow":            # only if managers release people
            for q in quarters:
                m += x[o.id, q] <= o.released_by_managers(q)
    m.solve(pulp.PULP_CBC_CMD(msg=False))
    return x, short
