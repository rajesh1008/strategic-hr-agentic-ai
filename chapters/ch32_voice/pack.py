"""Chapter 32: the information pack, deny by default (no model).

Book section "The information pack". A union, a works
council and a consultation committee all need the same ten
answers before they can agree to anything. This builds the
pack from the system register and refuses to issue it while
any answer is missing. It does not judge the answers; the
representatives do that.

Run:  HRAI_MODEL=no-model python -m chapters.ch32_voice.pack
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"
FIELDS = [
    ("PK-1", "purpose", "What it does"),
    ("PK-2", "affected", "Who it touches"),
    ("PK-3", "sources", "What it reads"),
    ("PK-4", "never_read", "What it never reads"),
    ("PK-5", "readers", "Who uses the output"),
    ("PK-6", "line", "Where it sits on the Line"),
    ("PK-7", "review", "Human review and appeal"),
    ("PK-8", "tests", "Test results by group"),
    ("PK-9", "monitoring", "What is logged, kept, read"),
    ("PK-10", "switch_off", "How to switch it off"),
]


def build(facts: dict) -> tuple[list[str], list[str]]:
    lines, missing = [], []
    for pid, key, label in FIELDS:
        val = (facts.get(key) or "").strip()
        if not val:
            missing.append(pid)
            val = "MISSING"
        lines.append(f"{pid} {label}: {val}")
    return lines, missing


def main() -> None:
    packs = yaml.safe_load((HERE / "packs.yaml").read_text())
    rec = RunRecorder("ch32", "pack")
    for use, facts in packs.items():
        _, missing = build(facts)
        state = "issue" if not missing else "HOLD"
        rec.print(f"{use}: {10 - len(missing)} of 10 "
                  f"answered -> {state}")
        for pid in missing:
            label = dict((p, l) for p, _, l in FIELDS)[pid]
            rec.print(f"  {pid} missing: {label}")
        rec.note(use=use, missing=missing)
    rec.save()


if __name__ == "__main__":
    main()
