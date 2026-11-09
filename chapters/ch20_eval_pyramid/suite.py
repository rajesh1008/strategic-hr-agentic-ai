"""The golden set, run k times against the service agent.

Book section: "Level 2: the golden set". The agent under test
is the Chapter 14 AskHartwell agent, unchanged: same
instructions, same three tools, same lifecycle and fake
HartwellOne. Each case starts from a fresh fixture with its
faults queued. Graders (graders.py) score the end state.

pass@1 is the share of case runs that pass. pass^k counts a
case only if it passes in all k runs: an employee meets one
run, but the employer meets all of them.

A variant swaps one part of the agent so the suite can be
tested against a known fault (failure injection):
  P1  instructions without "Never say a change is made unless
      the status says done."

Run: python -m chapters.ch20_eval_pyramid.suite [K] [P1]
     (needs ANTHROPIC_API_KEY; writes runs/ch20/suite/)
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from chapters.ch03_agentic_systems.loop import Budget, run
from chapters.ch14_controlled_actions import agent as ch14
from chapters.ch14_controlled_actions.actions import Lifecycle
from chapters.ch14_controlled_actions.fakes import (Clock,
                                                    HartwellOne)
from hrai.llm import RunRecorder
from .graders import grade

GOLDEN = yaml.safe_load(
    (Path(__file__).parent / "data/golden.yaml").read_text())
NEVER = (" Never say a change is made unless the status says"
         " done.")
VARIANTS = {"base": ch14.SYSTEM,
            "P1": ch14.SYSTEM.replace(NEVER, "")}


def play(rec, cid: str, case: dict, system: str) -> dict:
    emp = case["emp"]
    lc = Lifecycle(HartwellOne(), Clock(),
                   managers={ch14.LENA: "HW-012927"})
    if case.get("faults"):
        lc.hris.inject(*case["faults"], emp=emp)
    calls: list = []
    out = run(rec, system.format(emp=emp),
              ch14.kit(lc, emp, calls), case["ask"], Budget())
    seen = {"emp": emp, "reply": out.final_text,
            "handoff": "handoff" in calls,
            "writes": len(lc.hris.audit),
            "actions": [(a.kind, a.state, a.emp, a.dispatches)
                        for a in lc.actions.values()]}
    return {"seen": seen, "grade": grade(case, seen),
            "stop": out.stop_reason, "turns": out.turns}


def main() -> None:
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    var = sys.argv[2] if len(sys.argv) > 2 else "base"
    rec = RunRecorder("ch20", "suite" if var == "base"
                      else f"suite_{var}")
    cases = GOLDEN["cases"]
    rec.print(f"Golden set v{GOLDEN['version']}, {len(cases)}"
              f" cases x {k} runs, agent {var}")
    results: dict[str, list] = {c: [] for c in cases}
    for i in range(1, k + 1):
        for cid, case in cases.items():
            r = play(rec, cid, case, VARIANTS[var])
            results[cid].append(r)
            g, s = r["grade"], r["seen"]
            acts = ", ".join(f"{a[0]} {a[1]}"
                             for a in s["actions"]) or "none"
            mark = "pass" if g["pass"] else \
                "FAIL " + ",".join(g["fails"])
            extra = " (judge)" if g["notes"] else ""
            rec.print(f"run{i} {cid} {mark}{extra}")
            rec.print(f"   {acts} | writes {s['writes']}"
                      f"{' | hand_off' if s['handoff'] else ''}")
            rec.note(run=i, case=cid, reply=s["reply"],
                     seen=s, grade=g)
    rec.print("=== by case")
    once = allk = 0
    for cid, rs in results.items():
        p = sum(r["grade"]["pass"] for r in rs)
        once += p
        allk += p == k
        fails = sorted({f for r in rs for f in
                        r["grade"]["fails"]})
        rec.print(f"{cid} {p}/{k}"
                  + (f"  {','.join(fails)}" if fails else ""))
    n = len(cases)
    rec.print(f"pass@1 {once}/{n * k} ({once / (n * k):.0%});"
              f" pass^{k} {allk}/{n} ({allk / n:.0%})")
    print(rec.save())


if __name__ == "__main__":
    main()
