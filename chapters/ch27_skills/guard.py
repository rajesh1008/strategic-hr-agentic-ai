"""Chapter 27: what a skills suggestion may not carry.

Book sections "Declared, evidenced, suggested" and the Agent
Design Note. NEVER holds the personal classes the inventory
must not record about anyone, as patterns code can check.
A suggestion passes only if its skill is in the catalog, its
quote is copied word for word from a document the design is
allowed to read, and the quote carries no NEVER class.
"""
from __future__ import annotations

import re

NEVER = {
    "HEALTH": r"\b(sick|illness|operation|surgery|hospital"
              r"|health|medical|knee)\b",
    "CARE": r"(kita|child ?care|pick-up|caring for|carer"
            r"|caregiv|family commitment|dialysis|father)",
    "REP": r"(betriebsrat|works council"
           r"|employee representative|union)",
    "HOURS": r"(23:4\d|22:5\d|late[- ]night|late evening"
             r"|midnight|after[- ]hours|outside (normal |"
             r"working |business )?hours|worked through the"
             r" weekend|long hours|work[- ]life|burnout"
             r"|out of hours)",
    "CONFLICT": r"(disagree|conflict|tension|friction"
                r"|interpersonal|ignored my handover)",
    "RELIGION": r"(ramadan|religio|fasting|faith)",
    "PARENTAL": r"(parental leave|maternity|paternity"
                r"|pregnan|elternzeit|family leave)",
}
_RX = {k: re.compile(v, re.I) for k, v in NEVER.items()}


def classes(text: str) -> set[str]:
    """The NEVER classes a piece of text touches."""
    return {k for k, rx in _RX.items() if rx.search(text or "")}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def check(sug: dict, catalog: dict, allowed: list[str]) -> str:
    """'ok' or the first reason the suggestion is refused."""
    if sug.get("skill_id") not in catalog:
        return "not_in_catalog"
    q = _norm(sug.get("quote", ""))
    if len(q) < 12:
        return "no_quote"
    if not any(q in _norm(t) for t in allowed):
        return "quote_not_in_source"
    if classes(q):
        return "never_class"
    return "ok"
