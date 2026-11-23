# Strategic HR in the Age of Agentic AI, Chapter 3: 549 Hours
# Listing: Break-Even, Net Hours and the Doubled-Review Case (Under the Hood)

COST, RATE, WEEKS = 210_000, 50, 46        # tool $ a year, $ an hour, weeks

def break_even_hours() -> float:            # net hours a week the tool must free
    return COST / (RATE * WEEKS)

def net_hours(measured_gross: float, review: float) -> float:
    return measured_gross - review

def capacity_value(net: float) -> float:    # capacity, never cash
    return net * RATE * WEEKS

round(break_even_hours(), 1)                # 91.3
net_hours(244, 81)                          # 163
capacity_value(net_hours(244, 162))         # 188600, below the $210k cost
