"""Chapter 32: the register checked for represented employees.

Book section "What Ray asked for". Chapter 11's register gives
every Keep step a decider, a reviewer and an appeal. For a
union member that appeal is the wrong door: the agreement has
a grievance procedure with its own clock and a representative
in the room. These four checks run beside Chapter 11's six.

  U-1  a Keep step in a represented area has a block
  U-2  the block names a grievance route whose stages all
       have a role and at least 5 days, or a reason it has
       none
  U-3  the representative sees the case record only on the
       member's written authorization
  U-4  the member is told about the representative
"""
from __future__ import annotations

U_TEXT = {
    "U-1": "represented block on the Keep step",
    "U-2": "grievance route with stages, roles and days",
    "U-3": "record shown only on written authorization",
    "U-4": "member told about the representative",
}


def check(line_data: dict, reg: dict) -> list[tuple[str, str]]:
    """(step id, check id) for every failure."""
    areas = set(reg.get("represented_areas", "CDEGH"))
    routes = reg.get("routes", {})
    keep = [s["id"] for s in line_data["steps"]
            if s["placement"].side == "keep"
            and s["id"][0] in areas]
    entries = {e["id"]: e for e in reg["entries"]}
    gaps = []
    for sid in keep:
        b = entries.get(sid, {}).get("represented")
        if not b:
            gaps.append((sid, "U-1"))
            continue
        names = b.get("route", [])
        stages = [st for n in names
                  for st in routes.get(n, [])]
        ok = bool(names) and len(stages) > 0 and all(
            st.get("who") and st.get("file_days", 0) >= 5
            and st.get("answer_days", 0) >= 5 for st in stages)
        excused = not names and b.get("no_route_reason")
        if not ok and not excused:
            gaps.append((sid, "U-2"))
        access = b.get("rep_access")
        if access != "member_written_authorization":
            gaps.append((sid, "U-3"))
        if "representative" not in b.get("told_adds", ""):
            gaps.append((sid, "U-4"))
    return gaps
