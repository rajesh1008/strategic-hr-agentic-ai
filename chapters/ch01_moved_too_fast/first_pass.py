"""Chapter 1: a first pass of the Automate/Keep Line.

Book section: "A first pass at the Line". Ten steps from the
chapter's three incidents (Hartwell's Smart Shortlist release,
Brightwater's plant chatbot, Ashby & Lowe's bundled screen and
Calder Bank's letter copilot), placed with the Chapter 11 rule.
No model is involved: the rule places, and the script compares
each placement with the mode the software actually ran in.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch01_moved_too_fast.first_pass
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from chapters.ch11_automate_keep.line import (MODES, allowed,
                                              answers, place)
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent


def run(p) -> list[dict]:
    steps = yaml.safe_load(
        (HERE / "first_pass.yaml").read_text())["steps"]
    p(f"{'id':<3} {'answers':<7} {'placed':<26} "
      f"{'shipped':<9} ok")
    out = []
    for s in steps:
        pl = place(s["kind"], answers(s["answers"]))
        shipped = s["as_shipped"]
        ok = shipped == "new" or (
            shipped in MODES and allowed(pl.mode, shipped))
        p(f"{s['id']:<3} {s['answers']:<7} {str(pl):<26} "
          f"{shipped:<9} {'yes' if ok else 'NO'}")
        out.append({**s, "placed": str(pl), "within": ok})
    over = [s["id"] for s in out if not s["within"]]
    p(f"steps run above their ceiling: {len(over)} "
      f"({', '.join(over)})")
    return out


def main(argv: list[str]) -> None:
    rec = RunRecorder("ch01", "first_pass")
    rec.note(steps=run(rec.print))
    print("run record:", rec.save().name)


if __name__ == "__main__":
    main(sys.argv[1:])
