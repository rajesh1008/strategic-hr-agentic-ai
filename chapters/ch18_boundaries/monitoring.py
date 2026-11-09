"""The monitoring test: eleven checks, three verdicts.

Book section: "The monitoring test". Each proposal in
data/proposals.yaml is checked against M1 to M11. A STOP
cannot be fixed by paperwork; NOT YET lists what is
missing; PROCEED means every check passed. The checks
encode the rules the chapter cites per lane; they are a
screening aid, not legal advice. All data synthetic.

Run: HRAI_MODEL=no-model python -m \\
         chapters.ch18_boundaries.monitoring
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"
EUROPE = {"NL", "DE", "UK"}
COUNCIL = {"NL", "DE"}
NOTICE_DAYS = {"AU-NSW": 14}
NEVER = {"ehr"}  # a patient record is never an HR source


def check(p: dict) -> dict[str, str]:
    """Return {check: 'ok' | 'gap' | 'stop'} for one design."""
    lane, r = p["lane"], {}
    words = len(str(p["purpose"]).split())
    r["M1 purpose"] = "ok" if words >= 6 else "gap"
    r["M2 necessity"] = "ok" if p["alternatives"] else "gap"
    r["M3 basis"] = ("gap" if p["basis"] == "consent"
                     else "ok")
    r["M4 assessment"] = ("ok" if p["dpia"] or lane not in
                          EUROPE else "gap")
    need = NOTICE_DAYS.get(lane, 0)
    r["M5 notice"] = ("ok" if p["notice"] and
                      p.get("notice_days", need) >= need
                      else "gap")
    r["M6 representatives"] = (
        "gap" if lane in COUNCIL
        and p["council"] != "consented" else "ok")
    r["M7 emotion"] = "stop" if p["staff_emotion"] else "ok"
    r["M8 named person"] = (
        "gap" if p["decision_use"] == "individual"
        and not p["reviewer"] else "ok")
    long = (p["retention_days"] > 365
            and p["basis"] != "legal_obligation")
    r["M9 time limits"] = (
        "gap" if p["outside_hours"] or p["covert"] or long
        else "ok")
    r["M10 aggregation"] = (
        "gap" if p["min_group"] < 5 and not p["reviewer"]
        else "ok")
    r["M11 source"] = ("stop" if set(p["sources"]) & NEVER
                       else "ok")
    return r


def verdict(r: dict[str, str]) -> str:
    if "stop" in r.values():
        return "STOP"
    return "NOT YET" if "gap" in r.values() else "PROCEED"


def load() -> list[dict]:
    return yaml.safe_load((DATA / "proposals.yaml").read_text())


def main() -> None:
    rec = RunRecorder("ch18", "monitoring")
    for p in load():
        r = check(p)
        bad = [k.split()[0] for k, v in r.items() if v != "ok"]
        rec.note(id=p["id"], version=p["version"], checks=r)
        rec.print(f"{p['id']} {p['version']}  {p['lane']:<6}"
                  f" {verdict(r):<8} "
                  + (" ".join(bad) if bad else "-"))
    print(rec.save())


if __name__ == "__main__":
    main()
