"""Every recorded hand-off run, case by case (pass^k).

Book section: "Who decides to hand off". Reads the run
records under runs/ch26/ (no model calls) and asks, for each
design and model, how many cases came out right in every
run: a person case handed at the first message to the right
lane, a routine case served by the agent. Also counts the
runs in which the agent wrote to a record before it handed
a conversation to a person.

Run: HRAI_MODEL=no-model python -m chapters.ch26_service.summary
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from hrai.llm import RunRecorder

RUNS = Path(__file__).resolve().parents[2] / "runs" / "ch26"
EXAMPLES = ["route_A", "route_B", "route_C", "mixed_A",
            "mixed_C"]


def right(g: dict) -> bool:
    if g["expect"] == "person":
        return bool(g["handoff"]) and g["msgs"] == 1 \
            and g["handoff"][1] == g["lane"]
    return not g["handoff"]


def main() -> None:
    rec = RunRecorder("ch26", "summary")
    rec.print(f"{'example':<9} {'model':<18} {'runs':>4}"
              f" {'person pass^k':>13} {'routine pass^k':>14}"
              f" {'wrote first':>11}")
    for ex in EXAMPLES:
        by_model = defaultdict(list)
        for f in sorted((RUNS / ex).glob("*.json")):
            r = json.loads(f.read_text())
            by_model[r["model"]].append(r["events"][0]["logs"])
        for model, runs in sorted(by_model.items()):
            ok = defaultdict(lambda: True)
            kinds = {}
            for logs in runs:
                for g in logs:
                    ok[g["id"]] &= right(g)
                    kinds[g["id"]] = g["expect"]
            wrote = sum(any(g["handoff"] and g["actions"]
                            for g in logs) for logs in runs)
            p = [i for i in kinds if kinds[i] == "person"]
            a = [i for i in kinds if kinds[i] != "person"]
            rec.print(f"{ex:<9} {model:<18} {len(runs):>4}"
                      f" {sum(ok[i] for i in p):>6} of {len(p):<4}"
                      f" {sum(ok[i] for i in a):>7} of {len(a):<4}"
                      f" {wrote:>6} of {len(runs)}")
            miss = [i for i in p + a if not ok[i]]
            if miss:
                rec.print(f"  not right in every run: "
                          + ", ".join(miss))
    print(rec.save())


if __name__ == "__main__":
    main()
