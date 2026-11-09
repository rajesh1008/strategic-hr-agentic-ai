"""A small policy engine: policy as data, decisions as code.

Book section: "Policy as code: the engine in the loop".
A policy file lists rules in order; each rule names an
effect and the conditions that must all be true. The engine
computes every condition from the system of record, takes
the first rule whose conditions hold, falls back to the
default, and logs the decision with the policy version and
the facts it used. No model is involved at any point.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

HERE = Path(__file__).parent


@dataclass
class Decision:
    effect: str
    rule: str
    version: str
    facts: dict = field(default_factory=dict)


class Engine:
    def __init__(self, policy: dict, conditions: dict):
        self.p, self.cond, self.log = policy, conditions, []

    def decide(self, req: dict) -> Decision:
        facts = {c: bool(fn(req))
                 for c, fn in self.cond.items()}
        d = Decision(self.p["default"], "DEFAULT",
                     self.p["version"], facts)
        for r in self.p["rules"]:
            if all(facts[c] for c in r["when"]):
                d = Decision(r["effect"], r["id"],
                             self.p["version"], facts)
                break
        self.log.append({"policy": self.p["policy"],
                         "version": d.version,
                         "rule": d.rule, "effect": d.effect,
                         "request": req, "facts": facts})
        return d


def load_policy(version: str) -> dict:
    f = HERE / "policies" / f"leave-{version}.yaml"
    return yaml.safe_load(f.read_text())
