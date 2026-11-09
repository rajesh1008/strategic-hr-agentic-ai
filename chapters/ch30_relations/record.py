"""Chapter 30: the case decision record and its checks.

Book section "The decision record". A case decision record
is written by the person who decides, after the hearing,
and checked by code before any letter is drafted:

  DEC-1  a named decider who is not the investigator, an
         agent or a system
  DEC-2  the allegation as put, with the date it was put
         and the evidence shared before the meeting
  DEC-3  the employee's own account cited and answered
  DEC-4  every item relied on is in the evidence chain,
         and none is an agent output or an HR-record item
         outside the allegation
  DEC-5  the reasons are the decider's words: under 20% of
         their eight-word runs appear in any agent output
         for the case
  DEC-6  the outcome is within policy for the finding, with
         mitigation and comparable cases recorded
  DEC-7  every step the lane requires is recorded as done
  DEC-8  an appeal to a different named person, with a
         window of at least 5 business days

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch30_relations.record
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from chapters.ch30_relations.case import DATA
from hrai.llm import REPO, RunRecorder

AGENT = {"agent", "assistant", "system", "copilot", "model"}
OUTSIDE = {"hr_record", "agent_output"}


def lanes() -> dict:
    return yaml.safe_load((DATA / "lanes.yaml").read_text())


def steps_for(lane: str, ads: bool) -> list[str]:
    ls = lanes()
    out, cur = [], ls[lane]
    while cur:
        out = cur.get("steps", []) + out
        if ads:
            out += cur.get("if_ads", [])
        cur = ls.get(cur.get("inherits", ""))
    return list(dict.fromkeys(out))


def agent_text(run_ids: list[str]) -> str:
    out = []
    for rid in run_ids:
        folder = REPO / "runs" / Path(rid).parent
        stamp = Path(rid).name.split("#")[0]
        rec = json.loads(next(folder.glob(
            f"{stamp}-*.json")).read_text())
        for c in rec["calls"]:
            for b in c["response"]["content"]:
                if b.get("type") == "text":
                    out.append(b["text"])
    return " ".join(out)


def shingles(text: str, n: int = 8) -> set:
    w = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def copied(reasons: str, agent: str) -> float:
    mine = shingles(reasons)
    return len(mine & shingles(agent)) / len(mine) if mine else 0


def checks(r: dict, chain: dict) -> list[str]:
    bad = []
    d, inv = r.get("decider") or {}, r.get("investigator") or {}
    if (not d.get("name") or d["name"] == inv.get("name")
            or str(d.get("role", "")).lower() in AGENT):
        bad.append("DEC-1")
    if not (r.get("allegation") and r.get("put_on")
            and r.get("evidence_shared")):
        bad.append("DEC-2")
    own = [i for i in r.get("relied_on", [])
           if chain.get(i, {}).get("by_employee")]
    if not own or not r.get("response_considered"):
        bad.append("DEC-3")
    if any(i not in chain or chain[i]["kind"] in OUTSIDE
           for i in r.get("relied_on", [])):
        bad.append("DEC-4")
    agent = agent_text(r.get("agent_outputs", []))
    if agent and copied(r.get("reasons", ""), agent) >= 0.20:
        bad.append("DEC-5")
    if not (r.get("outcome") in r.get("policy_range", [])
            and r.get("mitigation") and "comparables" in r):
        bad.append("DEC-6")
    need = steps_for(r["lane"], bool(r.get("ads_used")))
    if any(s not in r.get("steps_done", []) for s in need):
        bad.append("DEC-7")
    a = r.get("appeal") or {}
    if (not a.get("name") or a["name"] in (d.get("name"),
                                           inv.get("name"))
            or a.get("window_days", 0) < 5):
        bad.append("DEC-8")
    return bad


def missing_steps(r: dict) -> list[str]:
    need = steps_for(r["lane"], bool(r.get("ads_used")))
    return [s for s in need if s not in r.get("steps_done", [])]


def main() -> None:
    rec = RunRecorder("ch30", "record")
    doc = yaml.safe_load((DATA / "records.yaml").read_text())
    rec.print("== case decision records, DEC-1 to DEC-8")
    for r in doc["records"]:
        chain = doc["chains"][r["chain"]]
        bad = checks(r, chain)
        extra = ""
        if "DEC-5" in bad:
            pct = copied(r["reasons"],
                         agent_text(r["agent_outputs"]))
            extra = f" (copied {pct:.0%})"
        if "DEC-7" in bad:
            extra += f" (missing {', '.join(missing_steps(r))})"
        rec.print(f"  {r['id']:<18} {r['lane']:<8}"
                  f" {' '.join(bad) or 'pass'}{extra}")
        rec.note(record=r["id"], fails=bad)
    rec.save()


if __name__ == "__main__":
    main()
