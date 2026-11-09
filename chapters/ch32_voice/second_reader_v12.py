"""Chapter 32: Chapter 11's second reader on Line v1.2.

Book section "Line v1.2". The representatives changed three
steps' answers and rewrote eight steps' facts. This reruns
Chapter 11's blind second reader, unchanged, on v1.2 three
times and compares what it routes to the Line review panel
with Chapter 11's three runs on v1.0 (read from their run
records, not retyped).

Run:  HRAI_MODEL=claude-haiku-5-5 \\
        python -m chapters.ch32_voice.second_reader_v12
"""
from __future__ import annotations

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from chapters.ch11_automate_keep import line
from chapters.ch11_automate_keep.second_reader import (
    BATCH, ask)
from hrai.llm import REPO, RunRecorder, model

HERE = Path(__file__).resolve().parent / "data"
RUNS = 3


def routed_v10() -> list[set[str]]:
    out = []
    for f in sorted((REPO / "runs/ch11/second_reader")
                    .glob("*.json")):
        ev = json.loads(f.read_text())["events"]
        out.append({e["routed"] for e in ev if "routed" in e})
    return out


def one_run(rec: RunRecorder, steps: list[dict]) -> set[str]:
    says: dict[str, dict] = {}
    for i in range(0, len(steps), BATCH):
        says.update(ask(rec, steps[i:i + BATCH]))
    routed = set()
    for s in steps:
        m = says.get(s["id"])
        if m is None or line.place(
                s["kind"], m["answers"]) != s["placement"]:
            routed.add(s["id"])
    return routed


def main() -> None:
    data = line.load(HERE / "line_v1_2.yaml")
    steps = data["steps"]
    rec = RunRecorder("ch32", "second_reader_v12")
    with ThreadPoolExecutor(RUNS) as ex:
        got = list(ex.map(lambda _: one_run(rec, steps),
                          range(RUNS)))
    old = routed_v10()
    rec.print(f"== {model()}: second reader, {RUNS} runs each")
    for name, runs in (("v1.0", old), ("v1.2", got)):
        sizes = ", ".join(str(len(r)) for r in runs)
        every = sorted(set.intersection(*runs))
        rec.print(f"Line {name}: routed per run {sizes}; "
                  f"in all {len(runs)}: {len(every)}")
        rec.print("  " + " ".join(every))
    count = Counter(i for r in got for i in r)
    for sid in ("B01", "E03", "F02", "F08", "G08",
                "H04", "H06", "H08"):
        was = sum(sid in r for r in old)
        rec.print(f"{sid}: routed v1.0 {was} of {len(old)}, "
                  f"v1.2 {count[sid]} of {RUNS}")
    rec.note(v12_routed=[sorted(r) for r in got])
    rec.save()


if __name__ == "__main__":
    main()
