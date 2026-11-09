"""The controlled-action ledger, first view (Chapter 3).

Book section: "The controlled-action ledger". One entry per
write an agent proposes, with five steps in order: proposal,
approval, dispatch, receipt, readback. Chapter 14 builds the
full lifecycle (hrai/actions.py); this is the minimum that
makes a write accountable. No model is involved here.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field


def key_for(payload: dict) -> str:
    """Same request, same key: a repeat cannot double-book."""
    raw = json.dumps(payload, sort_keys=True).encode()
    return "IK-" + hashlib.sha256(raw).hexdigest()[:10]


@dataclass
class Entry:
    action_id: str
    tool: str
    proposal: dict              # who asked, what, for whom
    key: str
    approval: dict = field(default_factory=dict)
    dispatch: dict = field(default_factory=dict)
    receipt: dict = field(default_factory=dict)
    readback: dict = field(default_factory=dict)

    def state(self) -> str:
        if not self.approval:
            return "proposed"
        if not self.approval.get("approved"):
            return "awaiting " + self.approval["approver"]
        if self.readback.get("matches"):
            return "done (read back)"
        if self.receipt.get("status") == "unknown":
            return "unknown: read back before retry"
        return self.receipt.get("status", "approved")


class Ledger:
    def __init__(self):
        self.entries: list[Entry] = []

    def propose(self, tool: str, proposal: dict) -> Entry:
        e = Entry(f"A-{len(self.entries) + 1:03d}", tool,
                  proposal, key_for(proposal))
        self.entries.append(e)
        return e

    def rows(self) -> list[dict]:
        return [dict(asdict(e), state=e.state())
                for e in self.entries]
