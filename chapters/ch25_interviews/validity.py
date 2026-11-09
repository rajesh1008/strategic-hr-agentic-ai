"""Chapter 25: the assessment validity table.

Book section "The assessment validity table". Six checks per
method, VAL-1 to VAL-6, and a verdict:
  STOP  no job-analysis link (VAL-1) or a prohibited
        inference (VAL-5): no paperwork fixes it
  FIX   any other check fails
  KEEP  all six pass
A published estimate for a method's class is context, never
evidence on its own: it says how well the class predicts on
average elsewhere, not how this method does here.

Run:  python -m chapters.ch25_interviews.validity
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"
NEVER = yaml.safe_load(
    (HERE / "inferences.yaml").read_text())["never"]


def checks(m: dict) -> dict[str, bool]:
    return {
        "VAL-1": bool(m["tasks"]),
        "VAL-2": m["evidence"] == "local",
        "VAL-3": m["impact"] in ("current", "due"),
        "VAL-4": bool(m["adjustments"]),
        "VAL-5": not any(p in NEVER for p in m["infers"]),
        "VAL-6": bool(m["owner"]) and bool(m["review"]),
    }


def verdict(c: dict[str, bool]) -> str:
    if not c["VAL-1"] or not c["VAL-5"]:
        return "STOP"
    return "KEEP" if all(c.values()) else "FIX"


def main() -> None:
    rec = RunRecorder("ch25", "validity")
    inv = yaml.safe_load((HERE / "inventory.yaml").read_text())
    rec.print("== Hartwell assessment inventory, September 2027")
    tally: dict[str, int] = {}
    for m in inv["methods"]:
        c = checks(m)
        v = verdict(c)
        tally[v] = tally.get(v, 0) + 1
        est = "-" if m["estimate"] is None \
            else f"{m['estimate']:.2f}"
        fails = [k for k, ok in c.items() if not ok]
        rec.print(f"{m['id']} {v:4s} {m['name']}")
        rec.print(f"     class {m['meta']} ({est});"
                  f" evidence {m['evidence']}")
        rec.print(f"     fails: {', '.join(fails) or 'none'}")
        rec.note(method=m["id"], checks=c, verdict=v)
    rec.print("verdicts: " + ", ".join(
        f"{k} {n}" for k, n in sorted(tally.items())))
    rec.save()


if __name__ == "__main__":
    main()
