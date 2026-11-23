# Strategic HR in the Age of Agentic AI, Chapter 11: Wrong Pay
# Listing: The Note Guard: No Digit Without a Slot (Under the Hood)
# Strict on purpose: a draft that types even a date as digits is rejected and rewritten with a slot.

import re

SLOT = re.compile(r"\{\{(\w+)\}\}")
DIGIT = re.compile(r"\d")

def render_note(draft: str, facts: dict[str, str]) -> str:
    """The model writes words and {{slots}}; code supplies every number."""
    if DIGIT.search(SLOT.sub("", draft)):
        raise ValueError("draft carries a figure the code did not produce")
    unknown = set(SLOT.findall(draft)) - facts.keys()
    if unknown:
        raise ValueError(f"unknown slots: {sorted(unknown)}")
    return SLOT.sub(lambda m: facts[m.group(1)], draft)
