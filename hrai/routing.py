"""Calibration and the routing line (Chapter 16).

A model's confidence is a claim until it is measured. This
module turns labeled cases into a reliability table, fits a
calibration map on one half of the cases and checks it on
the other, and routes each new case to one of four places:

  complete     the agent completes (or, for a Keep step, the
               recommendation goes to the confirm lane)
  review       a named person reviews the case in full
  escalate     a senior reviewer reads it; the case is unclear
  fail_closed  a named person decides, whatever the score

Fail-closed rules run first and no score can override them.
No model is called here; everything is deterministic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

Pair = tuple[float, bool]   # (stated confidence, was right)


def wilson(k: int, n: int, z: float = 1.96
           ) -> tuple[float, float]:
    """95% Wilson interval for k successes in n."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n
                      + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def reliability(pairs: list[Pair], edges: list[float]
                ) -> list[dict]:
    """One row per confidence bin: how sure, how right."""
    rows = []
    for lo, hi in zip(edges, edges[1:]):
        last = hi == edges[-1]
        inb = [(c, r) for c, r in pairs
               if lo <= c < hi or (last and c == hi)]
        n = len(inb)
        if n == 0:
            rows.append({"lo": lo, "hi": hi, "n": 0})
            continue
        right = sum(r for _, r in inb)
        rows.append({
            "lo": lo, "hi": hi, "n": n,
            "said": sum(c for c, _ in inb) / n,
            "right": right / n,
            "ci": wilson(right, n)})
    return rows


def ece(pairs: list[Pair], edges: list[float]) -> float:
    """Expected calibration error: the weighted gap between
    what the model said and how often it was right."""
    n = len(pairs)
    return sum(r["n"] / n * abs(r["said"] - r["right"])
               for r in reliability(pairs, edges) if r["n"])


def brier(pairs: list[Pair]) -> float:
    return sum((c - r) ** 2 for c, r in pairs) / len(pairs)


def isotonic(pairs: list[Pair]) -> list[tuple[float, float]]:
    """Pool-adjacent-violators fit: a step map from stated
    confidence to measured accuracy that never goes down as
    confidence goes up. Blocks with equal values merge.
    Returns (upper confidence, value)."""
    pts = sorted(pairs)
    blocks: list[list[float]] = []   # [hi, sum, n]
    for c, r in pts:
        blocks.append([c, float(r), 1.0])
        while len(blocks) > 1 and (blocks[-2][1] / blocks[-2][2]
                                   >= blocks[-1][1] / blocks[-1][2]):
            hi, s, n = blocks.pop()
            blocks[-1][0] = hi
            blocks[-1][1] += s
            blocks[-1][2] += n
    return [(hi, s / n) for hi, s, n in blocks]


def calibrate(fit: list[tuple[float, float]], c: float
              ) -> float:
    """Measured accuracy for a stated confidence c."""
    for hi, v in fit:
        if c <= hi:
            return v
    return fit[-1][1]


@dataclass
class RoutingLine:
    """One signed routing line for one step and one model."""
    step: str
    version: str
    model: str
    complete_at: float      # calibrated score to complete
    review_at: float        # below this, escalate
    fail_closed: list[str] = field(default_factory=list)
    review_if: list[str] = field(default_factory=list)
    owner: str = ""
    review_by: str = ""


@dataclass
class Case:
    case_id: str
    proposal: str           # what the agent proposes
    score: float | None     # calibrated; None if missing
    flags: list[str] = field(default_factory=list)


def route(case: Case, line: RoutingLine) -> tuple[str, str]:
    """Fail closed first; then hard-case flags; then the
    score decides the lane."""
    if case.proposal in line.fail_closed:
        return "fail_closed", f"proposal {case.proposal}"
    for f in case.flags:
        if f in line.fail_closed:
            return "fail_closed", f"flag {f}"
    s = case.score
    if s is None or not 0.0 <= s <= 1.0:
        return "fail_closed", "no usable score"
    hard = [f for f in case.flags if f in line.review_if]
    if hard:
        return "review", "flag " + ",".join(hard)
    if s >= line.complete_at:
        return "complete", f"score {s:.2f}"
    if s >= line.review_at:
        return "review", f"score {s:.2f}"
    return "escalate", f"score {s:.2f}"


def lowest_safe(pairs: list[tuple[float, bool]],
                target: float, min_n: int = 30
                ) -> tuple[float | None, int, float]:
    """Lowest threshold t such that the cases scored at or
    above t were right often enough: the Wilson lower bound
    of their accuracy is at least the target. Returns
    (t, n above t, lower bound); t is None if none is safe."""
    for t in sorted({c for c, _ in pairs}):
        above = [r for c, r in pairs if c >= t]
        if len(above) < min_n:
            break
        lo, _ = wilson(sum(above), len(above))
        if lo >= target:
            return t, len(above), lo
    return None, 0, 0.0
