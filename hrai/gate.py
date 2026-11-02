"""Deterministic policy gate for controlled actions (book Chapters 14 and 15).

The agent proposes; the gate decides. Nothing here calls a model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

POLICY_DIR = Path(__file__).resolve().parent.parent / "hartwell_gate" / "policies"


@dataclass
class Decision:
    allowed: bool
    reason: str
    policy: str
    policy_version: str
    missing: list[str] = field(default_factory=list)


def load_policy(name: str) -> dict:
    return yaml.safe_load((POLICY_DIR / f"{name}.yaml").read_text())


def evaluate(policy: dict, *, status: str, actor: str, context: dict) -> Decision:
    """Allow only listed (status, actor) pairs that carry every required field. Deny by default."""
    pid, ver = policy["tool"], str(policy["version"])
    for rule in policy.get("allow", []):
        if rule["status"] == status and rule["actor"] == actor:
            missing = [f for f in rule.get("requires", []) if not context.get(f)]
            if missing:
                return Decision(False, f"missing required fields: {', '.join(missing)}", pid, ver, missing)
            return Decision(True, "allowed by rule", pid, ver)
    if policy.get("deny_default", True):
        return Decision(False, f"no rule allows actor '{actor}' to set status '{status}'", pid, ver)
    return Decision(True, "allowed (deny_default is false)", pid, ver)
