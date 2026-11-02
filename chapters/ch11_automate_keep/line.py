"""The Automate/Keep Line: five tests, four modes, one rule.

No model is involved here. place() is the rule the owners sign;
the model in second_reader.py only gives a second opinion.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TESTS = ("consequence", "reversibility", "rule",
         "reservation", "sensitivity")
MODES = ("act", "act_with_approval", "recommend", "retrieve")
KINDS = ("read", "draft", "write")


@dataclass(frozen=True)
class Placement:
    side: str   # "automate" or "keep"
    mode: str   # the ceiling: an agent may do this and less

    def __str__(self) -> str:
        return f"{self.side}/{self.mode}"


def place(kind: str, a: dict[str, bool]) -> Placement:
    """Apply the Line test. a holds the five answers."""
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}")
    consequential = a["consequence"] and not (
        a["reversibility"] and a["rule"])
    if a["reservation"] or consequential:
        cap = "retrieve" if a["sensitivity"] else "recommend"
        return Placement("keep", cap)
    if a["consequence"]:
        return Placement("automate", "act_with_approval")
    if kind == "write":
        cheap = a["reversibility"] and a["rule"]
        mode = "act" if cheap else "act_with_approval"
        return Placement("automate", mode)
    if kind == "draft":
        return Placement("automate", "recommend")
    return Placement("automate", "retrieve")


def allowed(ceiling: str, requested: str) -> bool:
    """An owner may set a lower mode than the Line, never higher."""
    return MODES.index(requested) >= MODES.index(ceiling)


def answers(letters: str) -> dict[str, bool]:
    """'YNYNN' -> {'consequence': True, ...} in TESTS order."""
    if len(letters) != 5 or set(letters) - {"Y", "N"}:
        raise ValueError(f"need five Y/N letters, got {letters!r}")
    return {t: c == "Y" for t, c in zip(TESTS, letters)}


def load(path: Path = HERE / "line_v1.yaml") -> dict:
    data = yaml.safe_load(path.read_text())
    for s in data["steps"]:
        s["owner_answers"] = answers(s["answers"])
        s["placement"] = place(s["kind"], s["owner_answers"])
    return data
