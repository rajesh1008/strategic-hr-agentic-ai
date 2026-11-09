"""Jurisdiction rules as data (Chapter 5; owned by the ch05 writer).

The law lives in YAML under hrai/law/rules/, one file per lane
group, one record per rule. Each record cites the evidence-register
IDs (R-NNN in the book's 01-research/) that support it and stays
marked VERIFY until a reviewer has matched it to the checked text.

lookup.py answers one question deterministically: given the facts
of one workflow step at one place on one date, which recorded rules
reach it, which are unclear, and where the register has no record.
No model decides law here. A model may draft a proposed rule change
(chapters/ch05_jurisdiction_map/horizon_drafter.py); a person
approves it before anything in rules/ changes.
"""
from .lookup import (DUTIES, Facts, Finding, coverage, horizon,
                     load_rules, obligations, place_chain)

__all__ = ["DUTIES", "Facts", "Finding", "coverage", "horizon",
           "load_rules", "obligations", "place_chain"]
