"""Retrieval for the knowledge assistant: BM25 over title and
text, with three designs (book section "Entitled retrieval").

pilot:      one index built under the service identity; every
            document can be ranked and shown (what Hartwell ran
            in June 2027).
instructed: the same index; each passage carries its labels and
            the model is told who the user is and asked to use
            only what they may read (a behavioral control).
entitled:   the entitlement rule removes documents first; only
            readable documents are ranked (the fix).
whole:      entitled, but every readable document is attached
            unranked (the "just send it all" design, for cost).
"""
from __future__ import annotations

import math
import re
from collections import Counter

from . import entitled

WORD = re.compile(r"[a-z0-9]+")
STOP = set("""a an and are as at be by can do does for from get
have how i in is it my of on or our the to we what when where
which who will with you your""".split())


def tokens(text: str) -> list[str]:
    return [w for w in WORD.findall(text.lower()) if w not in STOP]


def bm25(query: str, docs: dict, ids: list[str],
         k1: float = 1.2, b: float = 0.75) -> list[tuple[str, float]]:
    bags = {i: tokens(docs[i]["title"] + " " + docs[i]["text"])
            for i in ids}
    n = len(ids) or 1
    avg = sum(len(t) for t in bags.values()) / n
    df = Counter(w for t in bags.values() for w in set(t))
    out = []
    for i, t in bags.items():
        tf, score = Counter(t), 0.0
        for w in set(tokens(query)):
            if w not in tf:
                continue
            idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
            score += idf * tf[w] * (k1 + 1) / (
                tf[w] + k1 * (1 - b + b * len(t) / avg))
        if score > 0:
            out.append((i, round(score, 2)))
    return sorted(out, key=lambda x: (-x[1], x[0]))


def search(query: str, user: dict, docs: dict, design: str,
           k: int = 4) -> list[str]:
    if design == "whole":
        return entitled.readable(user, docs)
    if design == "entitled":
        pool = entitled.readable(user, docs)
    else:
        pool = list(docs)
    return [i for i, _ in bm25(query, docs, pool)[:k]]
