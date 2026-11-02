"""Test a ticket-deflection claim on our own queue (Hartwell capability center, Hyderabad).

The claim (vendor proposal, synthetic): the HR helpdesk agent "deflects 45% of tier-1
tickets". The capability center routes alternate tier-1 tickets to the agent for eight
weeks (synthetic). A ticket the agent closes counts as deflected only if the same person
does not come back on the same category within seven days.

Run:  HRAI_MODEL=no-model python -m chapters.ch04_claim_ledger.deflection
"""
from __future__ import annotations

import json
from pathlib import Path

from hrai.ledger import Claim, Measurement
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "data/askhr-queue.json").read_text())
METRIC = "tier1_tickets_resolved_without_person"
MIN_PER_TICKET = 9.0      # tier-1 handling minutes per ticket (synthetic time study)
MIN_PER_RECONTACT = 14.0  # a returning ticket takes longer: history, apology, fix


def rates(tickets):
    ag = [t for t in tickets if t["arm"] == "agent"]
    closed = sum(t["bot_closed"] for t in ag)
    kept = sum(t["bot_closed"] and not t["recontact_7d"] for t in ag)
    back = sum(t["recontact_7d"] for t in ag)
    return {"agent_tickets": len(ag), "closed": closed / len(ag), "deflected": kept / len(ag),
            "recontacts": back}


def by_category(tickets):
    cats = sorted({t["category"] for t in tickets})
    return {c: rates([t for t in tickets if t["category"] == c]) for c in cats}


def hours_per_week(tickets, weeks=8):
    r = rates(tickets)
    saved = r["closed"] * r["agent_tickets"] * MIN_PER_TICKET / 60
    added = r["recontacts"] * MIN_PER_RECONTACT / 60
    return saved / weeks, added / weeks


def build_claim(tickets=None) -> Claim:
    tickets = tickets or DATA["tickets"]
    r = rates(tickets)
    c = Claim(claim_id="D-01", claimant="Helpdesk vendor",
              statement="Our HR agent deflects 45% of tier-1 tickets",
              metric_id=METRIC, metric_definition="share of tier-1 tickets closed by the agent "
              "with no return on the same category within 7 days",
              value=45.0, unit="percent of tier-1 tickets", source="vendor proposal, slide 9 (synthetic)",
              owner="Vikram Desai", version="agent 2026.3")
    c.add(Measurement(status="Measured in production", metric_id=METRIC,
                      value=round(100 * r["deflected"], 1), version="agent 2026.3",
                      measured_by="Hartwell capability center payroll ops (Vikram Desai)",
                      records="tier-1 HR queue, alternate tickets", n=r["agent_tickets"],
                      period="eight weeks, Aug-Sep 2026", method="alternate routing, 7-day return check",
                      baseline="control arm handled by people", owner="Ananya Rao"),
          on="2026-10-02")
    return c


def main() -> None:
    t = DATA["tickets"]
    rec = RunRecorder("ch04", "deflection")
    r = rates(t)
    rec.print(f"tickets: {len(t)} over 8 weeks; {r['agent_tickets']} routed to the agent (synthetic)")
    rec.print("claimed deflection                         45%")
    rec.print(f"closed by the agent (vendor's count)       {100 * r['closed']:.0f}%")
    rec.print(f"closed and no return within 7 days         {100 * r['deflected']:.0f}%")
    rec.print("")
    rec.print(f"{'category':<22}{'closed':>8}{'kept':>8}")
    for cat, x in by_category(t).items():
        rec.print(f"{cat:<22}{100 * x['closed']:>7.0f}%{100 * x['deflected']:>7.0f}%")
    s, a = hours_per_week(t)
    rec.print("")
    rec.print(f"tier-1 hours saved per week   {s:.0f}")
    rec.print(f"hours added by returns        {a:.0f}")
    rec.print(f"net hours per week            {s - a:.0f}")
    c = build_claim(t)
    rec.print(f"ledger: {c.claim_id} {c.effective_status().label}, board number {c.board_number()}%")
    rec.save()


if __name__ == "__main__":
    main()
