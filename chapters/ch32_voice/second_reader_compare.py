"""Chapter 32: second-reader comparison, Line v1.0 against v1.2.

No model call. Chapter 11's second reader was rerun on Line v1.0
after its facts lines were quoted (commit e25e0e1: nine rows had
been cut at a comma). This rebuilds the comparison printed by
second_reader_v12.py from the run records alone: v1.0 from the
three reruns in runs/ch11/second_reader, v1.2 from the routed sets
noted in the v1.2 run record. Nothing is retyped.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch32_voice.second_reader_compare
"""
from __future__ import annotations

import json
from collections import Counter

from hrai.llm import REPO, RunRecorder

from .second_reader_v12 import routed_v10

V12 = (REPO / "runs/ch32/second_reader_v12"
       / "20261109T164920Z-claude-haiku-5-5.json")
STEPS = ("B01", "E03", "F02", "F08", "G08", "H04", "H06", "H08")


def routed_v12() -> list[set[str]]:
    ev = json.loads(V12.read_text())["events"]
    got = next(e["v12_routed"] for e in ev if "v12_routed" in e)
    return [set(r) for r in got]


def main() -> None:
    old, got = routed_v10(), routed_v12()
    rec = RunRecorder("ch32", "second_reader_compare")
    rec.print("== second reader, claude-haiku-5-5, 3 runs each "
              "(from run records)")
    for name, runs in (("v1.0", old), ("v1.2", got)):
        sizes = ", ".join(str(len(r)) for r in runs)
        every = sorted(set.intersection(*runs))
        rec.print(f"Line {name}: routed per run {sizes}; "
                  f"in all {len(runs)}: {len(every)}")
        rec.print("  " + " ".join(every))
    count = Counter(i for r in got for i in r)
    for sid in STEPS:
        was = sum(sid in r for r in old)
        rec.print(f"{sid}: routed v1.0 {was} of {len(old)}, "
                  f"v1.2 {count[sid]} of {len(got)}")
    rec.note(v10_routed=[sorted(r) for r in old],
             v12_record=V12.name)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
