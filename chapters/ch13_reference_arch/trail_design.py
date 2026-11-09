"""Trail design checks (deterministic).

Book section: "Designing the trail". Five checks:
TRL-1 the whole chain, request to readback, joined by IDs;
TRL-2 entries hold references and hashes, not copies;
TRL-3 kept long enough for the law, and no copy of content
      kept longer than the record it copies;
TRL-4 the trail sits in a store the employer controls;
TRL-5 the agent's identity cannot change or delete it.

Run: HRAI_MODEL=no-model python -m \
     chapters.ch13_reference_arch.trail_design
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).parent / "data" / "trail_designs.yaml"
CHAIN = ["request", "proposal", "decision", "dispatch",
         "receipt", "readback"]
MIN_MONTHS = 6     # AI Act Art 26(6) floor, high-risk systems


def check(d: dict) -> list[str]:
    bad, keep = [], d["keep_months"]
    if any(s not in d["joined_by_id"] for s in CHAIN):
        bad.append("TRL-1")
    if d["holds"] != "refs":
        bad.append("TRL-2")
    short = d["high_risk"] and keep["actions"] < MIN_MONTHS
    long_copy = keep["content"] > d["record_months"]
    if short or long_copy:
        bad.append("TRL-3")
    if not d["store"].startswith("employer"):
        bad.append("TRL-4")
    if d["agent_can_modify"]:
        bad.append("TRL-5")
    return bad


def main() -> None:
    rec = RunRecorder("ch13", "trail_design")
    for d in yaml.safe_load(DATA.read_text())["designs"]:
        bad = check(d)
        rec.print(f"{d['org']}: {d['name']}")
        rec.print("   " + (" ".join(bad) if bad
                           else "passes all five"))
        rec.note(**{f"{d['org']}: {d['name']}": bad})
    print(rec.save())


if __name__ == "__main__":
    main()
