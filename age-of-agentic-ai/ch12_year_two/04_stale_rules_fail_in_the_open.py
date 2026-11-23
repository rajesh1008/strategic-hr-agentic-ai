# Strategic HR in the Age of Agentic AI, Chapter 12: Year Two
# Listing: Stale Rules Fail in the Open (Under the Hood)

from datetime import date

def apply_rule(rule, case, today: date):
    """A rule past its review date fails in the open, not in silence."""
    if rule.owner is None:
        return route_to_person(case, reason=f"{rule.id}: no owner")
    if today > rule.review_by and not rule.signed_off_since(rule.review_by):
        return route_to_person(case, reason=f"{rule.id}: review date passed")
    return rule.evaluate(case)
