"""Chapter 7: the adverse-impact table.

Book sections "Building the table", "Four-fifths and
significance" and "Slices, intersections and small numbers".

One row per group at one selection step: applicants,
selected, selection rate, impact ratio against the
highest-rate group, the difference in standard deviations,
an exact p-value, a 95% interval for the ratio, the
shortfall to four-fifths and the flags a reader needs
before trusting the ratio.

No model is involved. The four-fifths line (0.80) is a rule
of thumb from the US Uniform Guidelines, not a safe harbor,
and no court or regulator outside the US uses it as a test.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Iterable

FOUR_FIFTHS = 0.80
ALPHA = 0.05
SMALL_N = 30
NOT_REPORTED = {"declined", "unknown", "", None}
SHORT = {"Black or African American": "Black",
         "Hispanic or Latino": "Hispanic/Latino",
         "Two or more races": "Two or more",
         "Native Hawaiian or Pacific Islander": "NHPI",
         "Native American or Alaska Native": "Native American"}

# flag codes printed in the table, with the legend line
FLAGS = {
    "AI": "below 0.80 and significant",
    "<.8": "below 0.80, not significant",
    "SIG": "significant, above 0.80",
    "1P": "one person moves it across 0.80",
    "SM": "fewer than 30 in the group",
    "REF": "reference group (highest rate)",
    "XS": "under the minimum share, not compared",
}


@dataclass
class Row:
    group: str
    n: int
    selected: int
    rate: float
    ratio: float | None = None
    sd: float | None = None
    p: float | None = None
    low: float | None = None
    high: float | None = None
    shortfall: int = 0
    parity: int = 0
    flags: list[str] = field(default_factory=list)


def sd_diff(x1: int, n1: int, x2: int, n2: int) -> float:
    """Pooled two-proportion z: how many standard deviations
    group 1's rate sits from group 2's."""
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return 0.0 if se == 0 else (x1 / n1 - x2 / n2) / se


def _log_pmf(a: int, n1: int, n2: int, k: int) -> float:
    lc = lambda n, r: (math.lgamma(n + 1) - math.lgamma(r + 1)
                       - math.lgamma(n - r + 1))
    return lc(n1, a) + lc(n2, k - a) - lc(n1 + n2, k)


def fisher_p(x1: int, n1: int, x2: int, n2: int) -> float:
    """Two-sided Fisher exact p-value for a 2x2 table."""
    k = x1 + x2
    lo, hi = max(0, k - n2), min(k, n1)
    obs = _log_pmf(x1, n1, n2, k)
    tot = sum(math.exp(lp) for a in range(lo, hi + 1)
              if (lp := _log_pmf(a, n1, n2, k)) <= obs + 1e-7)
    return min(1.0, tot)


def ratio_interval(x1, n1, x2, n2, z=1.96):
    """95% interval for a ratio of two rates (log method)."""
    if x1 == 0 or x2 == 0:
        return None, None
    r = (x1 / n1) / (x2 / n2)
    se = math.sqrt(1 / x1 - 1 / n1 + 1 / x2 - 1 / n2)
    return r * math.exp(-z * se), r * math.exp(z * se)


def table(records: Iterable[dict], group: Callable[[dict], str],
          selected: Callable[[dict], bool],
          min_share: float = 0.0) -> tuple[list[Row], int]:
    """Build the adverse-impact table for one step.

    Returns the rows (highest rate first) and the count of
    records whose group was not reported. Groups under
    min_share of the reported records are listed, never
    compared (New York City audits allow 2%)."""
    counts: dict[str, list[int]] = {}
    missing = 0
    for r in records:
        g = group(r)
        if g in NOT_REPORTED:
            missing += 1
            continue
        c = counts.setdefault(g, [0, 0])
        c[0] += 1
        c[1] += bool(selected(r))
    total = sum(n for n, _ in counts.values())
    rows = [Row(g, n, s, s / n) for g, (n, s) in counts.items()]
    big = [r for r in rows if r.n >= min_share * total]
    for r in rows:
        if r.n < min_share * total:
            r.flags.append("XS")
    if not big:
        return rows, missing
    ref = max(big, key=lambda r: (r.rate, r.n))
    ref.ratio, ref.flags = 1.0, ref.flags + ["REF"]
    for r in big:
        if r is not ref:
            _compare(r, ref)
        if r.n < SMALL_N:
            r.flags.append("SM")
    rows.sort(key=lambda r: ("XS" in r.flags, -r.rate))
    return rows, missing


def _compare(r: Row, ref: Row) -> None:
    r.ratio = r.rate / ref.rate if ref.rate else None
    r.sd = sd_diff(r.selected, r.n, ref.selected, ref.n)
    r.p = fisher_p(r.selected, r.n, ref.selected, ref.n)
    r.low, r.high = ratio_interval(
        r.selected, r.n, ref.selected, ref.n)
    need = FOUR_FIFTHS * ref.rate * r.n
    r.shortfall = max(0, math.ceil(need - r.selected - 1e-9))
    r.parity = max(0, round(ref.rate * r.n - r.selected))
    below, sig = r.ratio < FOUR_FIFTHS, r.p < ALPHA
    if below and sig:
        r.flags.append("AI")
    elif below:
        r.flags.append("<.8")
    elif sig and r.rate < ref.rate:
        r.flags.append("SIG")
    up = (r.selected + 1) / r.n / ref.rate
    down = (r.selected - 1) / r.n / ref.rate
    if below and up >= FOUR_FIFTHS or (
            not below and down < FOUR_FIFTHS):
        r.flags.append("1P")


def intersect(*keys: str) -> Callable[[dict], str]:
    """Group by two or more fields; unreported if any is."""
    def g(r: dict) -> str:
        parts = [r.get(k) for k in keys]
        if any(p in NOT_REPORTED for p in parts):
            return "unknown"
        return " & ".join(str(p) for p in parts)
    return g


def render(rows: list[Row], title: str,
           missing: int = 0) -> list[str]:
    """The table as printed in the book (64 columns)."""
    out = [title,
           f"{'group':<18}{'n':>6}{'sel':>6}{'rate':>6}"
           f"{'ratio':>6}{'SD':>6}{'p':>7}  flags"]
    for r in rows:
        ratio = "" if r.ratio is None else f"{r.ratio:.2f}"
        sd = "" if r.sd is None else f"{r.sd:.1f}"
        p = "" if r.p is None else (
            "<0.001" if r.p < 0.001 else f"{r.p:.3f}")
        name = " & ".join(SHORT.get(p, p)
                          for p in r.group.split(" & "))
        out.append(f"{name[:18]:<18}{r.n:>6}{r.selected:>6}"
                   f"{r.rate:>6.2f}{ratio:>6}{sd:>6}{p:>7}"
                   f"  {' '.join(r.flags)}".rstrip())
    if missing:
        out.append(f"not reported: {missing}")
    return out


def legend(rows: list[Row]) -> list[str]:
    used = [f for f in FLAGS if any(f in r.flags for r in rows)]
    return [f"{f:<4} {FLAGS[f]}" for f in used]


def as_dict(r: Row) -> dict:
    return {k: getattr(r, k) for k in Row.__dataclass_fields__}
