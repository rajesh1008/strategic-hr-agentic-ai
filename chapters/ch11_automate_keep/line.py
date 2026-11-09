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
        low = a["sensitivity"] or kind == "read"
        return Placement("keep", "retrieve" if low else "recommend")
    if kind == "read":
        return Placement("automate", "retrieve")
    if kind == "draft":
        return Placement("automate", "recommend")
    if a["consequence"]:
        return Placement("automate", "act_with_approval")
    cheap = a["reversibility"] and a["rule"]
    return Placement("automate", "act" if cheap else "act_with_approval")


def allowed(ceiling: str, requested: str) -> bool:
    """An owner may set a lower mode than the Line, never higher."""
    return MODES.index(requested) >= MODES.index(ceiling)


def answers(letters: str) -> dict[str, bool]:
    """'YNYNN' -> {'consequence': True, ...} in TESTS order."""
    if len(letters) != 5 or set(letters) - {"Y", "N"}:
        raise ValueError(f"need five Y/N letters, got {letters!r}")
    return {t: c == "Y" for t, c in zip(TESTS, letters)}


FIELDS = {"id", "owner", "kind", "answers", "step", "facts"}


def load(path: Path = HERE / "line_v1.yaml") -> dict:
    data = yaml.safe_load(path.read_text())
    for s in data["steps"]:
        # A comma in an unquoted flow-mapping value ends the value and
        # turns the rest into a stray key: refuse such a row outright.
        if set(s) != FIELDS or not all(
                isinstance(s[k], str) and s[k] for k in FIELDS):
            raise ValueError(f"{path.name}: row {s.get('id')!r} does "
                             f"not parse to exactly {sorted(FIELDS)}")
        s["owner_answers"] = answers(s["answers"])
        s["placement"] = place(s["kind"], s["owner_answers"])
    return data
