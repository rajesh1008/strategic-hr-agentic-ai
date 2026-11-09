"""Chapter 10: the ticket taxonomy and the routing rule.

The taxonomy (data/taxonomy.yaml) gives each ticket category one
of four routes: answer, act, person or fix. The rule below turns a
reader's view of a ticket (a category and two flags) into a route.
Whoever reads the ticket, a person or a model, the rule decides.
"""
from __future__ import annotations

from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent / "data"
ROUTES = ("answer", "act", "person", "fix")


def load() -> dict[str, dict]:
    tx = yaml.safe_load((DATA / "taxonomy.yaml").read_text())
    return {c["code"]: c for c in tx["categories"]}


TAX = load()


def route(category: str, sensitive: bool, chasing: bool) -> str:
    """Fail closed on the person: an unknown category or any
    sign of health, conduct, a protected trait, immigration
    status or safety sends the ticket to a named person."""
    if category not in TAX or sensitive:
        return "person"
    r = TAX[category]["route"]
    if r == "person":
        return "person"
    if chasing or r == "fix":
        return "fix"
    return r


def gold(label: str, sensitive: int) -> str:
    """The route the two advisers' label implies."""
    return route(label, bool(sensitive), False)
