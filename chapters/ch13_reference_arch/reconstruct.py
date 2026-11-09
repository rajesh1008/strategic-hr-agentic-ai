"""The reconstruct test (synthetic).

Book section: "Designing the trail". Start from the system of
record, never from the agent's log: for every change an agent
identity made, follow IDs (not timestamps) back through the
trail to the request. A change is reconstructed only if the
whole chain is there.

Run: HRAI_MODEL=no-model python -m \
     chapters.ch13_reference_arch.reconstruct
"""
from __future__ import annotations

import json
from pathlib import Path

from hrai.llm import RunRecorder

CHAIN = ("proposal", "decision", "dispatch", "receipt",
         "readback")
DATA = Path(__file__).parent / "data"


def reconstruct(audit: list[dict], trail: list[dict],
                agents: set[str]) -> list[dict]:
    out = []
    for c in audit:
        if c["actor"] not in agents:
            continue
        aid = c.get("action_id")
        got = {e["step"] for e in trail
               if aid and e.get("action_id") == aid}
        corr = {e["corr"] for e in trail
                if aid and e.get("action_id") == aid}
        asked = any(e["step"] == "request" and e["corr"] in corr
                    for e in trail)
        miss = [s for s in CHAIN if s not in got]
        if not asked:
            miss.append("request")
        out.append({"change": c["change_id"],
                    "actor": c["actor"], "missing": miss})
    return out


def main() -> None:
    rec = RunRecorder("ch13", "reconstruct")
    pilot = json.loads((DATA / "pilot_feb2027.json").read_text())
    res = reconstruct(pilot["audit"], pilot["trail"],
                      set(pilot["agent_identities"]))
    full = [r for r in res if not r["missing"]]
    rec.print("Reconstruct test: AskHartwell pilot, "
              "February 2027 (synthetic)")
    rec.print(f"Changes in HartwellOne by agent identities: "
              f"{len(res)}")
    rec.print(f"Reconstructed to a full chain: {len(full)}")
    by = {}
    for r in res:
        k = (r["actor"], tuple(r["missing"]))
        by[k] = by.get(k, 0) + 1
    for (actor, miss), n in sorted(by.items()):
        rec.print(f"  {n:>3} by {actor}, missing:")
        rec.print("      " + (", ".join(miss) or "nothing"))
    said = [e for e in pilot["trail"]
            if e["step"] == "reply" and e.get("said_done")]
    backed = [e for e in said if any(
        x["step"] == "readback" and x["corr"] == e["corr"]
        for x in pilot["trail"])]
    rec.print(f"Replies telling an employee it was done: "
              f"{len(said)}")
    rec.print(f"  with a readback behind them: {len(backed)}")
    rec.note(results=res)
    print(rec.save())


if __name__ == "__main__":
    main()
