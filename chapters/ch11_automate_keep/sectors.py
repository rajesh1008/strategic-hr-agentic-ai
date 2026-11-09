"""Chapter 11: the same Line rule at five second organizations.

Each organization's process owners answered the five tests for a few
steps (sector_lines.yaml). line.place() is the same rule Hartwell signs.
No model is involved.

Run: HRAI_MODEL=no-model python -m chapters.ch11_automate_keep.sectors
(writes runs/ch11/sectors/...)
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

from . import line

HERE = Path(__file__).resolve().parent


def main() -> None:
    data = yaml.safe_load((HERE / "sector_lines.yaml").read_text())
    rec = RunRecorder("ch11", "sectors")
    for org, steps in data["orgs"].items():
        placed = [(s, line.place(s["kind"], line.answers(s["answers"])))
                  for s in steps]
        sides = Counter(p.side for _, p in placed)
        rec.print(f"{org}: {len(steps)} steps, automate "
                  f"{sides['automate']}, keep {sides['keep']}")
        for s, p in placed:
            rec.print(f"  {s['id']:<5}{s['answers']}  {str(p):<27}"
                      f"{s['step'][:44]}")
            rec.note(org=org, step=s["id"], placement=str(p))
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
