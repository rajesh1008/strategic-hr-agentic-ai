"""Workforce economics for Chapter 2. Pure functions, no model.

Hours, not heads: the calculator reports time freed as hours
and FTE-equivalents of time, and refuses to report heads cut.
All inputs are synthetic planning values (see data/).
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text())


# --- 1. Critical-role vacancy cost (Talent to Value) ----------

def net_cost_per_day(role: dict) -> float:
    """Value at risk plus cover premium, less pay not spent."""
    pay_per_day = role["loaded_pay_per_year"] / 365
    return (role["value_at_risk_per_day"]
            + role["cover_premium_per_day"]
            - pay_per_day)


def vacancy_days(role: dict, ramp_loss: float) -> float:
    """Expected vacancy-equivalent days a year for one role."""
    exits = role["incumbents"] * role["exit_rate"]
    per_exit = (role["days_to_fill"]
                + role["ramp_days"] * ramp_loss)
    return exits * per_exit


def is_critical(role: dict, rule: dict) -> bool:
    productive = role["days_to_fill"] + role["ramp_days"]
    cost = net_cost_per_day(role)
    return (cost >= rule["min_net_cost_per_day"]
            and productive >= rule["min_days_to_productive"])


def role_map(fx: dict) -> list[dict]:
    rows = []
    for r in fx["roles"]:
        days = vacancy_days(r, fx["ramp_loss"])
        cost = net_cost_per_day(r)
        rule = fx["critical_rule"]
        rows.append({"id": r["id"], "title": r["title"],
                     "incumbents": r["incumbents"],
                     "per_day": round(cost),
                     "days": round(days),
                     "annual": round(days * cost),
                     "critical": is_critical(r, rule)})
    return sorted(rows, key=lambda x: -x["annual"])


def fill_faster(fx: dict, role_id: str, days_cut: int) -> int:
    """Annual value of filling one role days_cut days sooner."""
    r = next(x for x in fx["roles"] if x["id"] == role_id)
    exits = r["incumbents"] * r["exit_rate"]
    return round(exits * days_cut * net_cost_per_day(r))


# --- 2. Cost to serve per resolved contact --------------------

def annual_cost(m: dict) -> float:
    return (m["loaded_cost"] * (1 + m["overhead"])
            + m["attrition"] * m["backfill_cost"])


def effective_contacts(m: dict) -> float:
    """New starters handle about half a load while ramping."""
    ramp_share = m["attrition"] * m["ramp_weeks"] / 52
    return m["contacts_per_fte"] * (1 - ramp_share * 0.5)


def cost_per_resolved(m: dict, escalation: float) -> float:
    handled = annual_cost(m) / effective_contacts(m)
    return handled + (1 - m["fcr"]) * escalation


def naive_cost(m: dict) -> float:
    """The seat-price view: salary over nominal contacts."""
    return m["loaded_cost"] / m["contacts_per_fte"]


def _human_route(om: dict) -> tuple[float, float]:
    """Cost of the fallback human tier, and of lost minutes."""
    a = om["agent_tier0"]
    fb = next(m for m in om["delivery_models"]
              if m["name"] == a["fallback_model"])
    esc = om["escalation_cost_per_contact"]
    lost = (a["minutes_lost_when_not_contained"]
            * a["employee_cost_per_minute"])
    return cost_per_resolved(fb, esc), lost


def agent_blended(om: dict, containment: float) -> float:
    """Cost per query with an agent at tier 0 and a human route.

    Uncontained queries go to the fallback human tier and also
    cost the employee the minutes lost before the hand-off.
    """
    human, lost = _human_route(om)
    run = om["agent_tier0"]["cost_per_conversation"]
    return run + (1 - containment) * (human + lost)


def break_even_containment(om: dict) -> float:
    """Below this containment the agent costs more than none."""
    human, lost = _human_route(om)
    run = om["agent_tier0"]["cost_per_conversation"]
    # solve: run + (1 - c) * (human + lost) = human
    return 1 - (human - run) / (human + lost)


# --- 3. Hours, not heads --------------------------------------

BANNED_OUTPUTS = ("headcount reduction", "heads cut",
                  "fte savings", "roles eliminated")


def hours_ledger(om: dict) -> dict:
    """Freed hours must be fully allocated before they count."""
    freed = sum(s["hours"] for s in om["hours_freed"])
    placed = sum(b["hours"] for b in om["redeployed_to"])
    if placed != freed:
        raise ValueError(
            f"{freed - placed:,} freed hours have no"
            " destination; unplaced hours are not a saving")
    measured = sum(s["hours"] for s in om["hours_freed"]
                   if s["status"] != "Claimed")
    return {"freed": freed, "placed": placed,
            "fte_of_time": freed / om["hours_per_fte_year"],
            "measured": measured}


def refuse_heads(text: str) -> list[str]:
    """Phrases a hours-not-heads report must not contain."""
    low = text.lower()
    return [p for p in BANNED_OUTPUTS if p in low]


# --- 4. Decision rights by layer ------------------------------

HUMAN_CEILING = ("recommend", "retrieve")


def check_rights(rows: list[dict]) -> list[str]:
    """A consequential decision needs a human decider, and the
    agent may at most recommend (the Line, Chapter 11)."""
    problems = []
    for r in rows:
        if not r["consequential"]:
            continue
        if r["decides"] == "agent":
            problems.append(
                f"{r['decision']}: agent decides")
        if r["agent_mode"] not in HUMAN_CEILING:
            problems.append(
                f"{r['decision']}: mode {r['agent_mode']}")
    return problems


# --- 5. Sector case: a vacant ICU shift (Lakemont) ------------

def shift_premium(fx: dict) -> dict:
    """Expected extra cost of a vacant shift, by cover route."""
    base = fx["staff_shift_cost"]
    out = {}
    for r in fx["routes"]:
        extra = r["shift_cost"] - base + r["lost_contribution"]
        out[r["route"]] = r["share"] * extra
    out["expected"] = sum(out.values())
    return out


def agency_only_view(fx: dict) -> float:
    """The first model: agency premium only, per shift."""
    r = fx["routes"][0]
    extra = r["shift_cost"] - fx["staff_shift_cost"]
    return r["share"] * extra
