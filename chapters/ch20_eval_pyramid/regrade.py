"""Re-grade a recorded run against a changed golden set.

Book section: "A golden set is a policy". Golden set v1.1
changes two expectations after the v1.0 run: a bank change
waiting on payroll may not be handed to an HR adviser too,
because payroll's queue already owns it and a second ticket
sends two people after one request. Nothing is re-run. The
recorded replies and ledgers are graded again by code, so the
change costs no model calls and the old run stays the record.

Run: HRAI_MODEL=no-model python -m \\
     chapters.ch20_eval_pyramid.regrade
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml

from chapters.ch20_eval_pyramid.graders import grade
from hrai.llm import RunRecorder

HERE = Path(__file__).parent
REPO = HERE.parents[1]
RUN = "ch20/suite/20261109T145108Z"

V11 = {  # case: (field, new value, reason)
    "G03": ("handoff", "forbidden",
            "payroll queue owns the wait"),
    "G15": ("handoff", "forbidden",
            "payroll queue owns the wait"),
}


def golden(changes: dict) -> dict:
    g = yaml.safe_load((HERE / "data/golden.yaml")
                       .read_text())["cases"]
    g = copy.deepcopy(g)
    for cid, (field, value, _) in changes.items():
        g[cid]["expect"][field] = value
    return g


def recorded(run_id: str) -> list[dict]:
    folder = REPO / "runs" / Path(run_id).parent
    stamp = Path(run_id).name
    f = next(folder.glob(f"{stamp}-*.json"))
    return json.loads(f.read_text())["events"]


def score(cases: dict, events: list[dict]) -> dict:
    by = {}
    for e in events:
        if "seen" not in e:
            continue
        g = grade(cases[e["case"]], e["seen"])
        by.setdefault(e["case"], []).append(g)
    return by


def line(name: str, by: dict) -> str:
    runs = [g["pass"] for v in by.values() for g in v]
    allk = sum(all(g["pass"] for g in v) for v in by.values())
    k = max(len(v) for v in by.values())
    return (f"{name}: pass@1 {sum(runs)}/{len(runs)}"
            f" ({100 * sum(runs) / len(runs):.0f}%);"
            f" pass^{k} {allk}/{len(by)}"
            f" ({100 * allk / len(by):.0f}%)")


def main() -> None:
    rec = RunRecorder("ch20", "regrade")
    ev = recorded(RUN)
    old = score(golden({}), ev)
    new = score(golden(V11), ev)
    rec.print(f"Re-grading {RUN} (no model calls)")
    for cid, (field, value, why) in V11.items():
        rec.print(f"  v1.1 {cid}: {field} -> {value} ({why})")
    rec.print(line("golden v1.0", old))
    rec.print(line("golden v1.1", new))
    for cid in sorted(new):
        a = sum(g["pass"] for g in old[cid])
        b = sum(g["pass"] for g in new[cid])
        if a != b:
            why = sorted({f for g in new[cid]
                          for f in g["fails"]})
            rec.print(f"  {cid} {a}/{len(old[cid])} -> "
                      f"{b}/{len(new[cid])}  {','.join(why)}")
        rec.note(case=cid, v10=a, v11=b)
    print(rec.save())


if __name__ == "__main__":
    main()
