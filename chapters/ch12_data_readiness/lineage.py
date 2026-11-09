"""Chapter 12: walk the lineage of one field, hop by hop.

A hop passes when it names an owner, a control and a record. A hop
whose site differs from the employee's lane is a cross-border read
and must appear in the data-transfer register (Chapter 8). The last
hop leaves Hartwell, so it may have no owner, but it needs a record.

Run: HRAI_MODEL=no-model python -m chapters.ch12_data_readiness.lineage
(writes runs/ch12/lineage/...)
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
HOME = {"UK": {"UK"}}


def check(lin: dict) -> list[tuple[int, str]]:
    home = HOME[lin["subject_lane"]]
    out = []
    last = lin["hops"][-1]["n"]
    for h in lin["hops"]:
        if not h["record"]:
            out.append((h["n"], "no record"))
        if h["n"] != last:
            if not h["owner"]:
                out.append((h["n"], "no owner"))
            if not h["control"]:
                out.append((h["n"], "no control"))
        if h["site"] not in home and h["site"] != "outside Hartwell":
            out.append((h["n"], f"cross-border read ({h['site']}): "
                                "transfer register"))
    return out


def main() -> None:
    lin = yaml.safe_load((HERE / "lineage.yaml").read_text())
    rec = RunRecorder("ch12", "lineage")
    rec.print(f"Lineage of {lin['field']} ({lin['subject_lane']} "
              f"employee): {len(lin['hops'])} hops")
    for h in lin["hops"]:
        rec.print(f"{h['n']} {h['step']} | {h['system']}, {h['site']}")
    found = check(lin)
    rec.print(f"Findings: {len(found)}")
    for n, text in found:
        rec.print(f"  hop {n}: {text}")
        rec.note(hop=n, finding=text)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
