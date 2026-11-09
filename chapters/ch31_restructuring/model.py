"""Chapter 31: shared loaders and the task arithmetic.

Book sections "Task exposure is not absorption" and "The
scenario fan". Roles and counts only; no person-level data
enters this module.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

DATA = Path(__file__).parent / "data"
PERSON = re.compile(r"\bHW-\d{6}\b")


def load(name: str = "scope.yaml") -> dict:
    return yaml.safe_load((DATA / name).read_text())


def half_up(x: float) -> int:
    """Round half up, so 10.5 roles reads as 11."""
    return int(x + 0.5)


def exposed(tasks: list[dict]) -> float:
    """Share of hours in tasks an occupation-level exposure
    score marks as exposed. Says nothing about absorption."""
    return sum(t["share"] for t in tasks if t["exposed"])


def absorbed(tasks: list[dict], weights: dict) -> float:
    """Share of hours the agents measurably absorb, each
    rate weighted by its claim status."""
    return sum(t["share"] * t["rate"] * weights[t["status"]]
               for t in tasks if t["side"] == "automate")


def assert_no_people(lines: list[str]) -> None:
    """Scenario outputs carry roles, never people."""
    for line in lines:
        if PERSON.search(line):
            raise ValueError(f"person ID in output: {line}")
