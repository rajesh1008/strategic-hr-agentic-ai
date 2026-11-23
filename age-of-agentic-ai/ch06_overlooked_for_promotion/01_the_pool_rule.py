# Strategic HR in the Age of Agentic AI, Chapter 6: Overlooked for Promotion
# Listing: The Pool Rule (Under the Hood)
# Fixed slots left critical roles vacant 21% of the time; the pool, 2%.

def pool_with_bar(candidates, bar: float, budget: int):
    """Promote everyone who clears the bar, up to the budget.
    No fixed slots, so a ready person is never refused to fill a quota."""
    cleared = [c for c in candidates if c.panel_score >= bar]
    if len(cleared) <= budget:
        return cleared, []
    cleared.sort(key=lambda c: c.panel_score, reverse=True)
    return cleared[:budget], cleared[budget:]     # waitlist is told, and why
