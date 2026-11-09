"""Chapter 33: site checks on an agent proposal.

Code runs the checks; the approval card shows the results.
Each check returns (name, passed, detail). A proposal with
any failed check is "flagged". No model.
"""
from __future__ import annotations

from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent / "data"
CREW_MIN = 6
REST_H = 10


def load() -> dict:
    return yaml.safe_load((DATA / "proposals.yaml").read_text())


def checks(p: dict, as_of: str) -> list[tuple[str, bool, str]]:
    k = p["kind"]
    if k == "leave":
        return [
            ("balance", p["days"] <= p["balance_days"],
             f"{p['days']} days asked, {p['balance_days']} left"),
            ("crew minimum", p["on_shift_after"] >= CREW_MIN,
             f"{p['on_shift_after']} of 8 on shift, "
             f"minimum {CREW_MIN}")]
    if k == "timesheet":
        return [("work order", bool(p["work_order"]),
                 f"{p['overtime_h']} h overtime, work order "
                 f"{p['work_order'] or 'none'}")]
    if k == "extension":
        tk = p["ticket_expires"]
        ok = not p["certified_work"] or (tk and tk >= p["date"])
        return [
            ("rest", p["rest_after_h"] >= REST_H,
             f"{p['rest_after_h']} h before next shift"),
            ("ticket", bool(ok),
             f"{p['certified_work'] or 'no certified work'}"
             + (f", ticket expired {tk}" if not ok else ""))]
    if k == "swap":
        return [("rest", p["rest_h"] >= REST_H,
                 f"{p['rest_h']} h between shifts")]
    return [("none", True, "no site check applies")]


def flagged(p: dict, as_of: str) -> list[str]:
    return [n for n, ok, _ in checks(p, as_of) if not ok]
