# Strategic HR in the Age of Agentic AI, Chapter 9: The Pay Gap
# Listing: Read the Form of the Pay Statement (Under the Hood)
# The classifier says what the posting shows. Whether a single figure is lawful depends on the jurisdiction; the strictest state a remote candidate could work from applies.

import re

MONEY = r"\$\s?(\d[\d,]*(?:\.\d+)?)\s?(k|K)?"
RANGE = re.compile(MONEY + r"\s*(?:-|–|to)\s*" + MONEY)
SINGLE = re.compile(MONEY)

def to_number(digits: str, k: str | None) -> float:
    return float(digits.replace(",", "")) * (1000 if k else 1)

def pay_form(text: str) -> str:
    """Classify the visual form of the pay statement. Legality is decided
    afterwards by the jurisdiction rule table that counsel maintains."""
    m = RANGE.search(text)
    if m:
        lo, hi = to_number(m[1], m[2]), to_number(m[3], m[4])
        if lo == hi:
            return "degenerate_range"
        return "range" if lo < hi else "reversed_range"
    if SINGLE.search(text):
        return "single_figure"
    return "no_pay"
