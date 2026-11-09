"""Chapter 28: the decision-first analytics brief and its check.

Book section "The dashboard that changed nothing". People
analytics at Hartwell (synthetic) writes a brief before it runs
a query: the decision, its owner, the options, the number that
would move the choice from one option to another, the date it
is needed by, the population, the outcome in words with the
field it comes from, the comparison, the kind of question
(descriptive, predictive or causal), the person who owns the
inference, and the Data Readiness Register use (Chapter 12).

The check refuses by default. Rules:
  B1  a decision and a named owner
  B2  at least two options, one of which may be "no change"
  B3  a deciding number: a stated result that picks an option
  B4  a deadline
  B5  an outcome in words, naming its source field
  B6  a comparison; a causal brief needs one that is not
      "none", "target" or before-and-after alone
  B7  the inference is owned by a person, not a tool
  B8  a register use, so the data has been cleared (Ch 12)

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch28_people_analytics.decision_brief
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
TOOLS = re.compile(r"dashboard|model|agent|tool|vendor|ai\b",
                   re.I)
WEAK = re.compile(r"^(none|target|.*target of|before and after"
                  r"|before-and-after)", re.I)


def check(b: dict) -> list[str]:
    fails = []
    if not b.get("decision") or not b.get("owner"):
        fails.append("B1 no decision or no owner")
    if len(b.get("options") or []) < 2:
        fails.append("B2 fewer than two options")
    if not b.get("deciding_number"):
        fails.append("B3 no deciding number")
    if not b.get("deadline"):
        fails.append("B4 no deadline")
    o = b.get("outcome") or ""
    if not o or "(" not in o:
        fails.append("B5 outcome has no source field")
    c = str(b.get("comparison") or "none")
    if WEAK.match(c.strip()):
        fails.append({"causal": "B6 no comparison that could"
                      " show cause",
                      "predictive": "B6 no comparison with what"
                      " people do now"}.get(
                          b.get("method"),
                          "B6 compared only with a target"))
    owner = str(b.get("inference_owner") or "")
    if not owner or TOOLS.search(owner):
        fails.append("B7 inference owned by a tool, not a person")
    if not b.get("register_use"):
        fails.append("B8 no Data Readiness Register use")
    return fails


def main() -> None:
    rec = RunRecorder("ch28", "decision_brief")
    briefs = yaml.safe_load((HERE / "data" / "briefs.yaml")
                            .read_text())
    out = {}
    for b in briefs:
        f = check(b)
        rec.print(f"{b['id']} {b['title']}")
        for x in f:
            rec.print(f"  FAIL {x}")
        rec.print(f"  {'READY' if not f else 'NOT READY'}:"
                  f" {8 - len(f)} of 8")
        out[b["id"]] = f
    rec.note(results=out)
    print(rec.save())


if __name__ == "__main__":
    main()
