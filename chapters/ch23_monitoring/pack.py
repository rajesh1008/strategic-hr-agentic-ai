"""The regulator pack: nine sections, built from the record.

Book section: "What the regulator asks for". A pack section is
complete only when the incident record holds every field it
needs; the code lists what is missing rather than letting a
narrative cover the gap. It also computes each notification
clock from the time the organization became aware. Whether a
rule applies is counsel's decision, recorded in the input; the
code never decides it. No model is called.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"


def load(name: str) -> dict:
    return yaml.safe_load((DATA / name).read_text())


def gaps(inc: dict, sections: dict) -> dict[str, list]:
    have = set(inc["have"])
    return {sid: [f for f in s["needs"] if f not in have]
            for sid, s in sections.items()}


def clocks(inc: dict, rules: dict) -> list[str]:
    aware = datetime.strptime(inc["aware"], "%Y-%m-%d %H:%M")
    out = []
    for lane, verdict in inc["lanes"].items():
        r = rules[lane]
        if verdict != "applies":
            out.append(f"{lane:<9}{verdict} (decision recorded)")
            continue
        if r.get("clock_h"):
            due = aware + timedelta(hours=r["clock_h"])
            out.append(f"{lane:<9}{r['clock_h']} h: due "
                       f"{due:%a %b %d %H:%M} UTC (rule to verify)")
        else:
            out.append(f"{lane:<9}{r['note']} (rule to verify)")
    return out


def main() -> None:
    rec = RunRecorder("ch23", "pack")
    inputs, rules = load("pack_inputs.yaml"), load(
        "notify_rules.yaml")["rules"]
    secs = inputs["sections"]
    for iid, inc in inputs["incidents"].items():
        g = gaps(inc, secs)
        done = sum(not v for v in g.values())
        rec.print(f"== {iid} ({inc['org']}): sections complete "
                  f"{done} of {len(secs)}")
        for sid, miss in g.items():
            if miss:
                rec.print(f"  {sid} {secs[sid]['name']}: missing "
                          + ", ".join(miss))
        rec.print("  clocks from awareness "
                  f"({inc['aware']} UTC):")
        for line in clocks(inc, rules):
            rec.print(f"    {line}")
    print(rec.save())


if __name__ == "__main__":
    main()
