"""Chapter 29: the pay desk's tools (deterministic).

Book section "An agent that only explains". Every tool here
is code. The agent that calls them (explain.py) has no tool
that changes pay, bank details or a benefit election, and no
tool that returns other people's pay. All data synthetic.
"""
from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal as D

from . import gratuity, rules
from .sheets import OPENING_WEEK

PROVIDER_GROSS = rules.legacy(OPENING_WEEK)   # what was paid
QUERY = "PQ-28-0117"

PLANS = {  # 2028 medical, employee + spouse, 26 paychecks
    "HDHP-HSA": dict(prem=D("88.40"), ded=D(3400),
                     coins=D("0.20"), oop=D(9000),
                     hsa=D(1000)),
    "PPO-Core": dict(prem=D("164.75"), ded=D(1500),
                     coins=D("0.20"), oop=D(6000), hsa=D(0)),
    "PPO-Plus": dict(prem=D("241.10"), ded=D(500),
                     coins=D("0.10"), oop=D(4000), hsa=D(0)),
}
USE = {"low": D(1000), "medium": D(6000), "high": D(25000)}


def payslip(emp: str) -> str:
    if emp != OPENING_WEEK.emp:
        return "no payslip access for this employee"
    r = rules.compute(OPENING_WEEK)
    gap = PROVIDER_GROSS - r.gross
    return "\n".join(
        ["payslip week Jan 10 to 16, 2028, paid Jan 21",
         f"provider gross paid ${PROVIDER_GROSS}",
         "provider overtime: 14 h x 1.5 x base $31.40"]
        + ["Hartwell rule recalculation:"]
        + rules.trace(OPENING_WEEK, r)
        + [f"paid ${-gap} less than the rule",
           f"payroll query {QUERY} opened Jan 21 by the"
           " recalculation check; owner US payroll manager;"
           " any correction is paid by off-cycle payment"])


def what_if(emp: str, day: str, hours: float,
            night: float) -> str:
    if emp != OPENING_WEEK.emp:
        return "no access"
    idx = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat",
           "Sun"].index(day[:3].title())
    days = list(OPENING_WEEK.days)
    days[idx] += D(str(hours))
    alt = rules.Sheet(OPENING_WEEK.emp, "TX", OPENING_WEEK.base, days,
                      OPENING_WEEK.night + D(str(night)),
                      OPENING_WEEK.premium, OPENING_WEEK.bonus)
    now, new = rules.compute(OPENING_WEEK), rules.compute(alt)
    return "\n".join(
        ["estimate only; this week as booked so far:"]
        + rules.trace(OPENING_WEEK, now)
        + [f"with {hours} more hours on {day}:"]
        + rules.trace(alt, new)
        + [f"difference ${new.gross - now.gross} gross,"
           " before tax and deductions"])


def plan_cost(p: dict, claims: D) -> D:
    ded = min(claims, p["ded"])
    rest = (claims - ded) * p["coins"]
    oop = min(ded + rest, p["oop"])
    return p["prem"] * 26 + oop - p["hsa"]


def compare_plans(emp: str, tier: str) -> str:
    out = [f"2028 medical, tier {tier}, annual cost ="
           " premiums + out of pocket - HSA employer seed"]
    for name, p in PLANS.items():
        cells = ", ".join(
            f"{k} ${plan_cost(p, v):,.2f}"
            for k, v in USE.items())
        out.append(f"{name}: premium ${p['prem']} per"
                   f" paycheck; {cells}")
    out.append("use levels: claims of $1,000 (low), $6,000"
               " (medium), $25,000 (high) a year")
    if emp == "HW-012771":
        out.append("note: spouse HW-019044 is a Hartwell"
                   " employee; dual-coverage rule applies;"
                   " benefits team confirms eligibility")
    out.append("elections are made only by the employee in"
               " HartwellOne > Benefits; window closes Fri"
               " Nov 19, 2027 at 23:59 MT")
    return "\n".join(out)


def add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day,
                          calendar.monthrange(y, m)[1]))


def pay_info_request(emp: str, today: date) -> str:
    due = add_months(today, 2)
    return (f"request PIR-NL-28-014 logged for {emp};"
            f" received {today:%B %-d, %Y}; written answer due"
            f" by {due:%B %-d, %Y}; answered by Hartwell"
            " Netherlands HR (reward) in writing; the agent"
            " holds no other person's pay")


def gratuity_estimate(emp: str) -> str:
    if emp != "HME-DXB-0311":
        return "no access"
    start, end = date(2022, 2, 1), date(2028, 3, 31)
    basic = D(3800)
    yrs = gratuity.service_years(start, end, 0)
    amt = gratuity.uae(basic, yrs)
    return "\n".join([
        f"estimate for {emp}, UAE, rule UAE-EOS v1.0",
        f"service {start:%B %-d, %Y} to {end:%B %-d, %Y},"
        f" unpaid leave 0 days: {yrs} years",
        f"basic wage AED {basic:,} a month; day = basic / 30",
        "first 5 years x 21 days; after 5 years x 30 days",
        f"estimated gratuity AED {amt:,}",
        "final statement by Gulf payroll (Hyderabad) on the"
        " last working day; paid with final wages"])


def route(queue: str, summary: str, n: list[int]) -> str:
    n[0] += 1
    return (f"ticket HR-28-{4400 + n[0]} to {queue} queue;"
            " a named person replies within 2 working days")
