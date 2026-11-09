"""The trail: one entry per step, joined by IDs (synthetic).

Book section: "Designing the trail". The trail points; the
record holds. An entry carries IDs, versions and a short hash
of any value, never the value itself, so the trail can be
kept longer than a transcript and shown to an auditor without
copying an employee's address or bank details into it.
"""
from __future__ import annotations

import hashlib
import itertools

STEPS = ("request", "read", "proposal", "decision",
         "dispatch", "receipt", "readback", "memory",
         "handoff", "reply")


def ref(value: str) -> str:
    """Short fingerprint of a value, for matching only."""
    return "v:" + hashlib.sha256(
        value.encode()).hexdigest()[:10]


class Trail:
    def __init__(self, corr: str):
        self.corr = corr                 # one conversation
        self.entries: list[dict] = []
        self._n = itertools.count(1)

    def add(self, step: str, actor: str, **refs) -> dict:
        assert step in STEPS, step
        e = {"seq": next(self._n), "corr": self.corr,
             "step": step, "actor": actor, **refs}
        self.entries.append(e)
        return e

    def steps(self, action_id: str) -> list[str]:
        return [e["step"] for e in self.entries
                if e.get("action_id") == action_id]
