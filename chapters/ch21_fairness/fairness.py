"""Chapter 21: the fairness suite's tests beyond the table.

Book sections "Errors, not only selections", "Small cells
and many comparisons" and "When protected data is missing".
Chapter 7's adverse-impact table (impact.py) compares
selection rates. These functions add what a challenge asks
next:
  errors()   among people who met the bar, how often each
             group was wrongly screened out
  bounds()   how far an impact ratio could move if every
             applicant who declined self-ID belonged to one
             side or the other
  holm()     which of many comparisons survive when you
             test them all at once
  cell()     whether a group is big enough to read at all

No model is involved, and nothing here sees a resume.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from chapters.ch07_adverse_impact.impact import (
    NOT_REPORTED, SHORT, fisher_p)

MIN_N = 30          # read a ratio only at 30 or more
MIN_EXPECTED = 5    # and at 5 or more expected selections


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


@dataclass
class Err:
    group: str
    n: int          # met the bar
    wrong: int      # screened out anyway
    rate: float
    low: float
    high: float
    p: float | None = None
    flags: list[str] = field(default_factory=list)


def errors(records, group, meets, said) -> tuple[list[Err], int]:
    """Wrong rejections among applicants who met the bar, by
    group, each group tested against all other reported
    applicants (two-sided Fisher). Flag ERR: higher and
    p < 0.05; SM: fewer than 30 qualified in the group."""
    q = [r for r in records if meets(r)]
    counts: dict[str, list[int]] = {}
    missing = 0
    for r in q:
        g = group(r)
        if g in NOT_REPORTED:
            missing += 1
            continue
        c = counts.setdefault(g, [0, 0])
        c[0] += 1
        c[1] += not said(r)
    tn = sum(n for n, _ in counts.values())
    tw = sum(w for _, w in counts.values())
    rows = []
    for g, (n, w) in counts.items():
        lo, hi = wilson(w, n)
        e = Err(g, n, w, w / n, lo, hi)
        if tw:
            e.p = fisher_p(w, n, tw - w, tn - n)
            others = (tw - w) / (tn - n) if tn > n else 0
            if e.p < 0.05 and e.rate > others:
                e.flags.append("ERR")
        if n < MIN_N:
            e.flags.append("SM")
        rows.append(e)
    rows.sort(key=lambda e: (-e.rate, -e.n))
    return rows, missing


def render_errors(rows: list[Err], title: str,
                  missing: int = 0) -> list[str]:
    out = [title, f"{'group':<18}{'met':>5}{'out':>5}"
                  f"{'rate':>6}{'95% interval':>14}{'p':>7}  flags"]
    for e in rows:
        p = "" if e.p is None else (
            "<0.001" if e.p < 0.001 else f"{e.p:.3f}")
        name = SHORT.get(e.group, e.group)
        out.append(f"{name[:18]:<18}{e.n:>5}{e.wrong:>5}"
                   f"{e.rate:>6.2f}{e.low:>7.2f} to{e.high:>5.2f}"
                   f"{p:>7}  {' '.join(e.flags)}".rstrip())
    if missing:
        out.append(f"not reported: {missing} met the bar")
    return out


def declined(records, group, meets, said) -> tuple[int, int]:
    """Applicants who met the bar but gave no answer for this
    axis: (how many, how many screened out). They are a group
    the audit can see, even when it cannot name them."""
    q = [r for r in records if meets(r) and group(r)
         in NOT_REPORTED]
    return len(q), sum(not said(r) for r in q)


def readable(records, group, selected):
    """Chapter 7's table on groups of 30 or more only, so the
    reference group is one you can read. Returns the rows,
    the not-reported count and the small groups as
    (name, n), which are listed and never compared."""
    from chapters.ch07_adverse_impact.impact import table
    n: dict[str, int] = {}
    for r in records:
        g = group(r)
        if g not in NOT_REPORTED:
            n[g] = n.get(g, 0) + 1
    big = {g for g, k in n.items() if k >= MIN_N}
    rows, missing = table(
        [r for r in records if group(r) in big
         or group(r) in NOT_REPORTED], group, selected)
    small = sorted(((g, k) for g, k in n.items()
                    if g not in big), key=lambda x: -x[1])
    return rows, missing, small


def bounds(records, group, selected, focus: str, ref: str):
    """Impact ratio of `focus` against `ref` as reported, and
    at the two extremes: every not-reported applicant in
    `focus`, or every one in `ref`. Returns (as reported,
    lowest, highest)."""
    def rate(rs):
        return sum(map(selected, rs)) / len(rs) if rs else 0.0
    f = [r for r in records if group(r) == focus]
    g = [r for r in records if group(r) == ref]
    u = [r for r in records if group(r) in NOT_REPORTED]
    seen = rate(f) / rate(g)
    a = rate(f + u) / rate(g)
    b = rate(f) / rate(g + u)
    return seen, min(a, b, seen), max(a, b, seen)


def holm(pvals: dict[str, float], alpha: float = 0.05
         ) -> dict[str, bool]:
    """Holm's step-down correction: True where a comparison
    still counts as significant after testing all of them."""
    order = sorted(pvals, key=pvals.get)
    m, keep, going = len(order), {}, True
    for i, k in enumerate(order):
        going = going and pvals[k] <= alpha / (m - i)
        keep[k] = going
    return keep


def cell(n: int, ref_rate: float) -> str:
    """READ, or why a cell cannot be read on its own."""
    if n < MIN_N:
        return "too few"
    if n * ref_rate < MIN_EXPECTED:
        return "too few expected"
    return "READ"
