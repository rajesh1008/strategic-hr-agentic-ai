# Strategic HR in the Age of Agentic AI, Chapter 15: Month Six
# Listing: A Stop Rule Is Data, Not a Sentence (Under the Hood)
# The benefits rule from Chapter 1: stop if credits received stay under $25,000 after two cycles.

from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class StopRule:
    case: str
    measure: Callable[[dict], float]      # reads the ledger or the evidence record
    fires_when: Callable[[float], bool]
    after_cycles: int
    signed_by: str

def month_six(rule: StopRule, evidence: dict) -> str:
    if evidence["live_cycles"] < rule.after_cycles:
        return "too early: no decision"
    value = rule.measure(evidence)
    return "stop" if rule.fires_when(value) else "continue"

benefits = StopRule("benefits_invoices", lambda e: e["credits_received_usd"],
                    lambda v: v < 25_000, after_cycles=2, signed_by="finance")
