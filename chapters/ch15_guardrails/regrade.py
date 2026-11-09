"""Re-grade recorded test-pack runs with the current grader.

Book section: "A prompt is not a guardrail". Reads replies
and pay_summary results from run records; makes no model
calls. Exposure comes from the record and does not change.
Run: HRAI_MODEL=no-model python -m \
     chapters.ch15_guardrails.regrade RUN.json ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from hrai.llm import RunRecorder
from . import entitle as E
from . import oracle as O
from .testpack import PACK


def run_means(record: dict) -> list:
    """(employee_ids, mean) for every pay_summary answered."""
    asked, out = {}, []
    for call in record["calls"]:
        for msg in call["request"]["messages"]:
            if not isinstance(msg["content"], list):
                continue
            for b in msg["content"]:
                if b.get("name") == "pay_summary":
                    asked[b["id"]] = b["input"].get(
                        "employee_ids", [])
                if (b.get("type") == "tool_result"
                        and b["tool_use_id"] in asked
                        and '"mean"' in b["content"]):
                    m = json.loads(b["content"])["mean"]
                    out.append((asked[b["tool_use_id"]], m))
    return out


def main(paths: list[str]) -> None:
    db = E.people()
    cases = {c["id"]: c for c in
             yaml.safe_load(PACK.read_text())["cases"]}
    rec = RunRecorder("ch15", "regrade")
    rec.print("Test pack re-graded, grader v1.1 (synthetic)")
    for p in paths:
        r = json.loads(Path(p).read_text())
        means = run_means(r)
        rec.print(f"Run {r['run_id']}")
        tally: dict = {}
        for ev in r["events"]:
            (key, v), = ev.items()
            build, cid = key.split(":")
            c = cases[cid]
            t = tally.setdefault(build, [0, 0, 0, 0, 0])
            if c["kind"] == "control":
                t[3] += 1
                t[4] += v["answered"]
                continue
            new = O.disclosed(c, v["reply"], db, means)
            t[0] += v["disclosed"]
            t[1] += new
            t[2] += v["exposed"]
            if new != v["disclosed"]:
                was = "flagged" if v["disclosed"] else "passed"
                now = "flagged" if new else "passed"
                rec.print(f"  {build}:{cid} {was} by v1.0,"
                          f" {now} by v1.1")
        for b, t in tally.items():
            rec.print(f"  {b:<7} disclosed v1.0 {t[0]}, v1.1"
                      f" {t[1]}; reached model {t[2]};"
                      f" controls {t[4]} of {t[3]}")
    print(rec.save())


if __name__ == "__main__":
    main(sys.argv[1:])
