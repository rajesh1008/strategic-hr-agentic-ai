"""Chapter 6: the works-council consultation plan.

For each system and country, list the representative body,
the legal hook each of the system's features triggers, what
the body can do (consent, opinion, inform), and the date by
which Hartwell must start so the longest track ends before
go-live. The EU
baseline (AI Act Art 26(7)) is added wherever the checker says
high-risk. Lead times are Hartwell's planning assumptions.

Run: HRAI_MODEL=no-model \
     python -m chapters.ch06_high_risk.councils
(writes runs/ch06/councils/...)
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import yaml

from . import checker

HERE = Path(__file__).resolve().parent


def plan(s: dict, go_live: date, cfg: dict) -> dict:
    """Rows of (country, body, power, hook, rid) and a start
    date: go-live minus the longest lead time that applies."""
    high = checker.classify(s["facts"]).high_risk
    rows, lead = [], 0
    for cc in s["where"]:
        c = cfg["countries"][cc]
        hit = [h for h in c["hooks"]
               if h["when"] in s["council_triggers"]]
        for h in hit:
            rows.append((cc, c["body"],
                         h.get("power", c["power"]),
                         h["ref"], h["rid"]))
        if hit:
            lead = max(lead, c["lead_weeks"])
        if high:
            b = cfg["eu_baseline"]
            early = go_live < b["from"]
            power = "inform early" if early else b["power"]
            rows.append((cc, "reps and workers", power,
                         b["ref"], b["rid"]))
            lead = max(lead, b["lead_weeks"])
    start = go_live - timedelta(weeks=lead)
    return {"rows": rows, "lead_weeks": lead, "start": start}


def main() -> None:
    from hrai.llm import RunRecorder
    cfg = yaml.safe_load((HERE / "councils.yaml").read_text())
    systems = {s["id"]: s for s in checker.load()["systems"]}
    rec = RunRecorder("ch06", "councils")
    for p in cfg["plans"]:
        s, go = systems[p["system"]], p["date"]
        out = plan(s, go, cfg)
        rec.print(f"{s['id']} {s['name'][:38]}, "
                  f"{p['kind']} {go}")
        for cc, body, power, ref, rid in out["rows"]:
            rec.print(f"  {cc} {body[:16]:<16} {power[:14]:<14}"
                      f" {ref[:40]:<40} {rid or 'VERIFY'}")
        if not out["rows"]:
            rec.print("  no body to inform or consult")
        rec.print(f"  start by {out['start']} "
                  f"({out['lead_weeks']} weeks)")
        rec.note(system=s["id"], start=str(out["start"]),
                 rows=len(out["rows"]))
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
