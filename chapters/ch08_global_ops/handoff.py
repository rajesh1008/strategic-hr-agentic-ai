"""Chapter 8: hand-off checks for an outsourced or offshore HR
service that an agent works in.

Twelve checks in three groups, run over the terms procurement
keyed from each contract (contracts.yaml):

  RACI  who is answerable, who may act, who may change the agent
  DATA  the data-transfer register is complete
  SLA   what the contract pays for, and when it may cut seats

The checks are rules. No model is called. A check says whether
a term is present and consistent; it never decides whether a
transfer mechanism is lawful. That is counsel's call.

Run: HRAI_MODEL=no-model python -m chapters.ch08_global_ops.handoff
(writes runs/ch08/handoff/...)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
AGENT = "agent"
CHECKS = {
    "RACI-1": "A is one named person on the client side",
    "RACI-2": "the agent acts only on Automate rows",
    "RACI-3": "only the client changes or switches the agent",
    "RACI-4": "the approver is not the one who took it",
    "DATA-1": "every cross-border flow has a mechanism",
    "DATA-2": "every processor and sub-processor is listed",
    "DATA-3": "works-council consent is recorded",
    "SLA-1": "containment counts only resolved contacts",
    "SLA-2": "a time-to-human target is set",
    "SLA-3": "seat cuts rest on production numbers",
    "SLA-4": "the current Line is cited, with notice",
    "SLA-5": "wrong actions are reported within a day",
}


@dataclass
class Finding:
    check: str
    ok: bool | None          # None: does not apply
    detail: str = ""


def client_side(c: dict, who: str) -> bool:
    return who in c["client_group"]


def raci(c: dict) -> list[Finding]:
    rows = {r["id"]: r for r in c["raci"]}
    bad = {k: [] for k in ("RACI-1", "RACI-2",
                           "RACI-3", "RACI-4")}
    for r in rows.values():
        a = r["A"]
        if a not in c["people"] or not client_side(
                c, c["people"][a]):
            bad["RACI-1"].append(f"{r['id']} A={a}")
        if AGENT in r["R"] and not r.get("automate"):
            bad["RACI-2"].append(f"{r['id']} {r['kind']}")
        if r["kind"] == "control" and not all(
                client_side(c, x) for x in r["R"]):
            bad["RACI-3"].append(f"{r['id']} R={r['R'][0]}")
        if r["kind"] == "approve":
            took = rows[r["apart_from"]]["R"]
            same = set(r["R"]) & set(took)
            if same:
                bad["RACI-4"].append(
                    f"{r['id']} and {r['apart_from']}: "
                    + ", ".join(sorted(same)))
    return [Finding(k, not v, "; ".join(v))
            for k, v in bad.items()]


def data(c: dict) -> list[Finding]:
    out = []
    gaps = [f"{'/'.join(t['from'])}->{t['to']} "
            f"{t['recipient']}" for t in c["transfers"]
            if t["to"] not in t["from"]
            and not t.get("mechanism")]
    out.append(Finding("DATA-1", not gaps, "; ".join(gaps)))
    listed = {t["recipient"] for t in c["transfers"]}
    need = {x for r in c["raci"] for x in r["R"]
            if x != AGENT and not client_side(c, x)}
    theirs = c["agent_owner"] == "provider" and any(
        AGENT in r["R"] for r in c["raci"])
    subs = {s["name"] for s in c["subprocessors"]}
    missing = sorted(need - listed)
    if theirs and not subs:
        missing.append("no sub-processor for the agent's model")
    missing += sorted(subs - listed)
    out.append(Finding("DATA-2", not missing,
                       "; ".join(missing)))
    wc = [t for t in c["transfers"] if t.get("consent_needed")]
    no = [f"{'/'.join(t['from'])}->{t['to']}" for t in wc
          if not t.get("consent_ref")]
    out.append(Finding("DATA-3", None if not wc else not no,
                       "; ".join(no)))
    return out


def sla(c: dict, rules: dict) -> list[Finding]:
    out = []
    cont = [k for k in c["kpis"] if k["rewards"] == "containment"]
    short = [k["name"] for k in cont
             if k.get("return_window_days", 0)
             < rules["min_return_window_days"]]
    out.append(Finding("SLA-1", None if not cont else not short,
                       "; ".join(short)))
    uses_agent = any(AGENT in r["R"] for r in c["raci"])
    tth = c.get("time_to_human_minutes")
    out.append(Finding("SLA-2",
                       None if not uses_agent else tth is not None,
                       "" if tth else "none in the contract"))
    weak = [f"{s['seats']} seats by {s['by']} ({s['status']})"
            for s in c["seat_cuts"]
            if s["status"] != rules["seat_cut_status"]]
    out.append(Finding("SLA-3",
                       None if not c["seat_cuts"] else not weak,
                       "; ".join(weak)))
    v, cur = c.get("line_version"), c["line_current"]
    days = c.get("line_notice_days", 0)
    ok4 = v == cur and days >= rules["min_line_notice_days"]
    out.append(Finding("SLA-4", ok4, "" if ok4 else
                       f"cites {v or 'no Line'}, current {cur}; "
                       f"notice {days} days"))
    h = c["incident_notify_hours"]
    ok5 = h <= rules["max_incident_hours"]
    out.append(Finding("SLA-5", ok5,
                       "" if ok5 else f"{h} hours"))
    return out


def check(c: dict, rules: dict) -> list[Finding]:
    return raci(c) + data(c) + sla(c, rules)


def load() -> dict:
    return yaml.safe_load((HERE / "contracts.yaml").read_text())


def mark(f: Finding) -> str:
    return {True: "pass", False: "FAIL", None: "n/a"}[f.ok]


def main() -> None:
    from hrai.llm import RunRecorder
    d = load()
    rec = RunRecorder("ch08", "handoff")
    rec.print("Hand-off checks, contracts.yaml (synthetic)")
    for c in d["contracts"]:
        fs = check(c, d["rules"])
        fails = [f for f in fs if f.ok is False]
        rec.print("")
        rec.print(f"{c['id']}  {c['name']}")
        rec.print(f"  {len(fails)} of {len(fs)} checks fail")
        for f in fails:
            rec.print(f"  FAIL {f.check} {CHECKS[f.check]}")
            rec.print(f"       {f.detail}")
        rec.note(contract=c["id"],
                 results={f.check: mark(f) for f in fs})
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
