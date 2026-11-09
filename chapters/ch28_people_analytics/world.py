"""Chapter 28: the synthetic workforce the analyses read.

Book sections "Prediction is not cause" and "The retention
test". It reuses Chapter 22's US salaried population and its
resignation rule (chapters/ch22_shadow_gates/workforce.py)
without changing them, and adds one thing HartwellOne never
records: whether a person is already looking for another job
(`searching`). That unrecorded fact is what makes the naive
analysis of raises wrong, which is the chapter's point.

Rules of this synthetic world, stated so a reader can see why
the numbers come out as they do:
  searching     about 12% of people in any quarter; adds 1.4
                to the log-odds of resigning
  a raise       moves pay to 0.95 of the range midpoint, so
                the "pay below 0.92" term of Chapter 22's rule
                no longer applies; nothing else changes
  history       eight quarters, 2025Q3 to 2027Q2, of raises
                for people paid below 0.92 of midpoint:
                  counter-offer  given mostly to people who
                                 are searching (a manager
                                 hears about an offer)
                  market adjustment  given by the range rule
                                 to whole business units
                                 when their budget allowed
  stay talk     a manager's stay conversation lowers the
                log-odds by 0.6, but only for a person who is
                not searching, has two or more years of tenure
                and has something a manager can change (a new
                manager, or 30 or more months since promotion).
                Set here, not measured.

These effects are inputs to the simulation. The chapter says
so: the point is which analysis recovers them, not what they
are at any real employer. Everything is invented. No model is
called.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

import numpy as np

from chapters.ch22_shadow_gates.workforce import (
    Person, hazards, people)

SEARCH_SHARE = 0.12
SEARCH_LOGIT = 1.4
RAISED_COMPA = 0.95
TALK_LOGIT = -0.6
TEST_START = date(2028, 1, 10)   # Monday; wave 1 paid
TEST_END = date(2028, 4, 7)      # Friday, 13 weeks later


def logit(q: float) -> float:
    return float(np.log(q / (1 - q)))


def resign_p(p: Person, searching: bool, raised: bool = False,
             talk: bool = False) -> float:
    """Chance p resigns in the quarter, in this world."""
    if raised and p.compa < 0.92:
        p = replace(p, compa=RAISED_COMPA)
    x = logit(hazards(p)[0]) + SEARCH_LOGIT * searching
    if talk and not searching and actionable(p):
        x += TALK_LOGIT
    return 1 / (1 + np.exp(-x))


def actionable(p: Person) -> bool:
    """Something a manager can change in a conversation."""
    return p.tenure >= 2 and (p.new_mgr > 0
                              or p.since_promo >= 30)


@dataclass
class Row:
    p: Person
    searching: bool
    raise_kind: str | None   # counter-offer, market, None
    resigned: bool


def history(seed: int = 2800) -> list[Row]:
    """Eight past quarters of people paid below 0.92 of
    midpoint, the raises they got and who resigned."""
    out = []
    for q in range(8):
        rng = np.random.default_rng(seed + q)
        back = (8 - q) * 0.25
        ps = [p for p in people(seed=seed + 100 + q, shift=back)
              if p.lane == "US" and p.compa < 0.92]
        # business units whose budget allowed market
        # adjustments this quarter (one in four)
        units = {u: rng.random() < 0.25 for u in range(40)}
        for p in ps:
            s = bool(rng.random() < SEARCH_SHARE)
            unit = int(p.id[-2:]) % 40
            kind = None
            if rng.random() < (0.45 if s else 0.03):
                kind = "counter-offer"
            elif units[unit] and rng.random() < 0.8:
                kind = "market"
            r = rng.random() < resign_p(p, s, raised=kind
                                        is not None)
            out.append(Row(p, s, kind, bool(r)))
    return out


def test_population(seed: int = 2828) -> list[tuple]:
    """US salaried on January 10, 2028, with the unrecorded
    searching flag."""
    rng = np.random.default_rng(seed)
    ps = [p for p in people(as_of=TEST_START) if p.lane == "US"]
    return [(p, bool(rng.random() < SEARCH_SHARE)) for p in ps]
