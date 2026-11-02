"""Deterministic number check for model-written notes.

The model explains; the code computes. Every number in a note
must already appear in the calculator output it was given.
"""
from __future__ import annotations

import re

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers(text: str) -> set[str]:
    """Numbers as bare strings: '$22,939,001' -> '22939001'."""
    out = set()
    for m in NUM.findall(text):
        n = m.replace(",", "").rstrip(".")
        out.add(n)
    return out


def unsourced(note: str, source: str) -> list[str]:
    """Numbers in the note that the source does not contain."""
    have = numbers(source)
    return sorted(numbers(note) - have, key=float)
