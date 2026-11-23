# Strategic HR in the Age of Agentic AI, Chapter 11: Wrong Pay
# Listing: Recompute Every Line, Route Every Unknown (Under the Hood)
# A missing rule is an answer, not an error: the line goes to a person. Decimal, never float, for money.

from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class PayLine:
    line_id: str
    person: str
    country: str
    element: str
    calculated: Decimal

def recompute(lines, events, rules):
    """Expected pay from source events. No model is called."""
    for line in lines:
        rule = rules.get((line.country, line.element))
        if rule is None:
            yield line, None, "no_rule"          # a person must look
            continue
        expected = rule(events.for_person(line.person))
        yield line, expected, line.calculated - expected
