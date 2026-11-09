"""Chapter 29: the deterministic pay rule.

Book section "The deterministic pay rule". Gross pay for one
weekly timesheet of an hourly US employee, computed by rules
in code and never by a model. Every line of the result
carries the ID of the rule that produced it, so an agent can
explain a payslip by quoting lines, and a reviewer can trace
each number to a rule with an owner, a version and a source.

The rules are a synthetic reading of US overtime law for the
book (29 USC 207; state daily overtime) and carry [VERIFY]
in the chapter until counsel signs them. Money is Decimal,
rounded half up to the cent once per line.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal as D

CENT = D("0.01")
RULESET = "US-PAY v1.3"
RULES = {
    "R-BASE": "every hour worked at the base rate",
    "R-NIGHT": "night premium per night hour",
    "R-BONUS": "nondiscretionary bonus for the week",
    "R-RATE": "regular rate = straight-time pay / hours",
    "R-OT": "overtime hours x 0.5 x regular rate",
    "R-DT": "double-time hours x 1.0 x regular rate",
}


def money(x: D) -> D:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class Sheet:
    emp: str
    state: str            # TX, CO or CA
    base: D               # dollars per hour
    days: list[D]         # hours worked, Monday to Sunday
    night: D = D(0)       # hours on the night shift
    premium: D = D(0)     # night premium per hour
    bonus: D = D(0)       # nondiscretionary, this week
    # Periods of consecutive work, in hours, each counted once,
    # even when it runs from one workday into the next. None
    # means each day's hours were one period inside that day.
    spans: list[D] | None = None


@dataclass
class Result:
    lines: list[tuple[str, str, D]] = field(default_factory=list)
    gross: D = D(0)
    rate: D = D(0)
    ot: D = D(0)
    dt: D = D(0)


def premium_hours(s: Sheet) -> tuple[D, D]:
    """Overtime and double-time hours under the state's rule."""
    total = sum(s.days, D(0))
    weekly = max(total - 40, D(0))
    if s.state == "CA":
        dot = sum((min(max(h - 8, D(0)), D(4))
                   for h in s.days), D(0))
        ddt = sum((max(h - 12, D(0)) for h in s.days), D(0))
        rest = total - dot - ddt
        return dot + max(rest - 40, D(0)), ddt
    if s.state == "CO":
        # COMPS Order #40, Rule 4.1: over 40 in the workweek,
        # over 12 in a workday, or over 12 consecutive hours
        # whatever the workday; the greatest applies (v1.3).
        d12 = sum((max(h - 12, D(0)) for h in s.days), D(0))
        spans = s.spans if s.spans is not None else s.days
        c12 = sum((max(h - 12, D(0)) for h in spans), D(0))
        return max(weekly, d12, c12), D(0)
    return weekly, D(0)


def compute(s: Sheet) -> Result:
    r = Result()
    hours = sum(s.days, D(0))
    base = money(hours * s.base)
    night = money(s.night * s.premium)
    bonus = money(s.bonus)
    straight = base + night + bonus
    r.lines.append(("R-BASE", f"{hours} h x ${s.base}", base))
    if night:
        r.lines.append(("R-NIGHT",
                        f"{s.night} h x ${s.premium}", night))
    if bonus:
        r.lines.append(("R-BONUS", "weekly bonus", bonus))
    r.rate = (straight / hours).quantize(D("0.0001"),
                                         ROUND_HALF_UP)
    r.ot, r.dt = premium_hours(s)
    if r.ot:
        p = money(r.ot * D("0.5") * r.rate)
        r.lines.append(("R-OT",
                        f"{r.ot} h x 0.5 x ${r.rate}", p))
    if r.dt:
        p = money(r.dt * r.rate)
        r.lines.append(("R-DT", f"{r.dt} h x ${r.rate}", p))
    r.gross = sum((amt for _, _, amt in r.lines), D(0))
    return r


def legacy(s: Sheet) -> D:
    """The 2019 spreadsheet: weekly overtime at 1.5 x base.

    It ignores the night premium and the bonus in the rate
    and ignores daily overtime. Kept to show the difference.
    """
    hours = sum(s.days, D(0))
    ot = max(hours - 40, D(0))
    straight = money((hours - ot) * s.base)
    return (straight + money(s.night * s.premium) + s.bonus
            + money(ot * s.base * D("1.5")))


def trace(s: Sheet, r: Result | None = None) -> list[str]:
    """The lines an agent may quote, one per rule applied."""
    r = r or compute(s)
    out = [f"{s.emp} week, {s.state}, ruleset {RULESET}"]
    for rid, what, amt in r.lines:
        out.append(f"{rid:<8}{what:<28}${amt:>9}")
    out.append(f"{'gross':<36}${r.gross:>9}")
    return out
