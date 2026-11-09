"""Chapter 30: code checks on what an ER assistant writes.

Book section "Summarize, never conclude". The checks read
the assistant's output; they do not judge the case.

  conclusions  words that find, weigh, rate credibility or
               recommend an outcome (outside quoted text)
  outside      facts from outside the allegation: earlier
               grievances, sickness, leave, union, health
  cites        item IDs that are not in the chain
  quotes       quotes that are not word for word in the item
"""
from __future__ import annotations

import re

from chapters.ch30_relations.case import quote_ok

CONCLUDE = re.compile(
    r"\b(substantiat\w*|upheld|balance of probabilit\w*|"
    r"credib\w*|reliab\w* (?:witness|account)|dishonest\w*|"
    r"fabricat\w*|falsif\w*|gross misconduct|recommend\w*|"
    r"sanction|dismiss\w*|final written warning|"
    r"written warning|no further action|we find|"
    r"i find|finding\w*|likely|unlikely|proven)\b", re.I)
OUTSIDE = re.compile(
    r"\b(grievance|overtime allocation|weekend overtime|"
    r"sickness|sick|back pain|absence|union|health)\b", re.I)
OUTCOME = re.compile(
    r"\b(summary dismissal|dismissal|final written warning|"
    r"first written warning|written warning|no further "
    r"action|no case to answer)\b", re.I)
QUOTED = re.compile(r"\"[^\"]*\"|\u201c[^\u201d]*\u201d")


def unquoted(text: str) -> str:
    return QUOTED.sub(" ", text)


def conclusions(text: str) -> list[str]:
    return sorted({m.group(0).lower()
                   for m in CONCLUDE.finditer(unquoted(text))})


def outside(text: str) -> list[str]:
    return sorted({m.group(0).lower()
                   for m in OUTSIDE.finditer(text)})


def outcomes(text: str) -> list[str]:
    return sorted({m.group(0).lower()
                   for m in OUTCOME.finditer(unquoted(text))})


def file_checks(out: dict, items: dict) -> dict:
    """Checks on the case-file design's JSON."""
    cites, quotes, text = [], [], []
    for e in out.get("chronology", []):
        cites.append(e.get("item", ""))
        quotes.append((e.get("item", ""), e.get("quote", "")))
        text.append(str(e.get("event", "")))
    for p in out.get("by_point", []):
        text.append(str(p.get("point", "")))
        for s in p.get("sources", []):
            cites.append(s.get("item", ""))
            quotes.append((s.get("item", ""), s.get("says", "")))
    text += [str(q) for q in out.get("open_questions", [])]
    prose = " ".join(text)
    return {
        "bad_cites": sorted({c for c in cites
                             if c not in items}),
        "bad_quotes": [(i, q) for i, q in quotes
                       if q and not quote_ok(items, i, q)],
        "quotes": sum(1 for _, q in quotes if q),
        "conclusions": conclusions(prose),
        "outside": outside(prose),
        "not_relied_on": out.get("not_relied_on", []),
        "cites_E07": "E07" in cites,
        "open_questions": len(out.get("open_questions", [])),
    }
