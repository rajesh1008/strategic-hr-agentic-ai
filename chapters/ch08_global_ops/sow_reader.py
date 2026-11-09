"""Chapter 8: a model reads the vendor's draft statement of work;
the checks decide.

Procurement keys the terms of every outsourcing contract by hand
(contracts.yaml). Here a model reads the same draft and answers
the same fields. The code compares the two readings field by
field. Wherever they differ, the field goes to Megan Hale and
counsel with the clause the model quoted. The model's reading is
then run through the SLA checks, to see whether a reader who
relied on it would have caught the same problems. The model
signs nothing, keys nothing and changes nothing.

Run: python -m chapters.ch08_global_ops.sow_reader
(needs ANTHROPIC_API_KEY; writes runs/ch08/sow_reader/...)
"""
from __future__ import annotations

import json
import re
import textwrap

from hrai.llm import RunRecorder

from . import handoff

SOW = handoff.HERE / "data" / "quayfen_sow_draft.md"
FIELDS = {
    "line_version": "Version of the client's Automate/Keep"
    " Line the SOW cites, as a string, or null",
    "line_notice_days": "Days of notice before a new Line"
    " version binds the supplier; 0 if none stated",
    "incident_notify_hours": "Hours the supplier has to tell"
    " the client about an incident",
    "time_to_human_minutes": "Target minutes from hand-off to"
    " a human adviser, or null if the SOW sets none",
    "return_window_days": "Days a containment or deflection"
    " KPI waits for a repeat contact before counting a"
    " contact as resolved; 0 if it does not wait",
    "seat_cut": "Seats the supplier commits to cut, as an"
    " integer, or 0",
    "seat_cut_measured": "true only if the seat cut rests on"
    " a rate measured on this client's own contacts",
    "changes_agent": "Who may change the agent's tools or"
    " permissions: client, supplier or both",
    "tells_employee": "Who tells an employee about an"
    " incident that affected them: client or supplier",
    "remote_view_is_transfer": "true if the SOW treats remote"
    " viewing of UK records from abroad as a transfer",
}
SYSTEM = (
    "You read a draft outsourcing statement of work for an HR"
    " team. Answer each field from the text alone. Do not judge"
    " whether a term is good or lawful.\nFields:\n"
    + "\n".join(f"{k}: {v}" for k, v in FIELDS.items())
    + '\nReply with JSON only: {"<field>": {"value": ...,'
    ' "clause": "the clause number you relied on"}}')


def keyed(c: dict) -> dict:
    """The same fields, from procurement's keyed terms."""
    cont = [k for k in c["kpis"]
            if k["rewards"] == "containment"]
    rows = {r["id"]: r for r in c["raci"]}
    cut = c["seat_cuts"][0] if c["seat_cuts"] else None

    def side(rid: str) -> str:
        r = rows[rid]["R"]
        return ("client" if all(handoff.client_side(c, x)
                                for x in r) else "supplier")
    uk = [t for t in c["transfers"] if "UK" in t["from"]]
    return {
        "line_version": c["line_version"],
        "line_notice_days": c["line_notice_days"],
        "incident_notify_hours": c["incident_notify_hours"],
        "time_to_human_minutes": c["time_to_human_minutes"],
        "return_window_days":
            cont[0].get("return_window_days", 0) if cont else 0,
        "seat_cut": cut["seats"] if cut else 0,
        "seat_cut_measured": bool(cut) and cut["status"]
        == "Measured in production",
        "changes_agent": side("R03"),
        "tells_employee": side("R11"),
        "remote_view_is_transfer":
            bool(uk) and bool(uk[0].get("mechanism")),
    }


def same(a, b) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    if a in (None, "null") and b in (None, "null"):
        return True
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return a == b


def ask(rec: RunRecorder, text: str) -> dict:
    resp = rec.create(max_tokens=2000, system=SYSTEM, messages=[
        {"role": "user", "content": text}],
        # the box's Brotli is too old for the SDK's decoder
        extra_headers={"Accept-Encoding": "gzip, deflate"})
    out = "".join(b.text for b in resp.content
                  if b.type == "text")
    m = re.search(r"\{.*\}", out, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def overlay(c: dict, got: dict) -> dict:
    """The contract as the model read it, for the SLA checks."""
    v = {k: (got.get(k) or {}).get("value") for k in FIELDS}
    m = json.loads(json.dumps(c, default=str))
    m["line_version"] = v["line_version"]
    m["line_notice_days"] = v["line_notice_days"] or 0
    m["incident_notify_hours"] = v["incident_notify_hours"] or 0
    m["time_to_human_minutes"] = v["time_to_human_minutes"]
    for k in m["kpis"]:
        if k["rewards"] == "containment":
            k["return_window_days"] = v["return_window_days"] or 0
    for s in m["seat_cuts"]:
        s["status"] = ("Measured in production"
                       if v["seat_cut_measured"] else "Claimed")
    return m


def main() -> None:
    d = handoff.load()
    c = {x["id"]: x for x in d["contracts"]}["QUA-D"]
    want = keyed(c)
    rec = RunRecorder("ch08", "sow_reader")
    got = ask(rec, SOW.read_text())
    diff = []
    for k in FIELDS:
        g = (got.get(k) or {})
        if not same(g.get("value"), want[k]):
            diff.append((k, want[k], g.get("value"),
                         g.get("clause", "")))
    rec.print(f"SOW reader, {rec.calls[-1]['response']['model']}"
              f": {len(FIELDS) - len(diff)} of {len(FIELDS)}"
              " fields match procurement")
    for k, w, g, cl in diff:
        rec.print(f"  {k}: keyed {w} | model {g}"
                  f" (clause {cl})")
    rec.print(f"Routed to Megan Hale and counsel: {len(diff)}")
    sla = handoff.sla(overlay(c, got), d["rules"])
    base = handoff.sla(c, d["rules"])
    found = [f.check for f in sla if f.ok is False]
    need = [f.check for f in base if f.ok is False]
    rec.print(f"SLA checks on the model's reading: "
              f"{len(found)} of {len(need)} failures found")
    missed = sorted(set(need) - set(found))
    for ln in textwrap.wrap("missed: " + (", ".join(missed)
                            or "none"), 60):
        rec.print(f"  {ln}")
    rec.note(diff=[list(x[:3]) for x in diff], found=found,
             missed=missed)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
