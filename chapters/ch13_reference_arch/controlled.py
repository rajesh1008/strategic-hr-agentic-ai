"""Controlled actions in the reference skeleton (synthetic).

Book section: "The skeleton, run". Proposal, approval,
dispatch, receipt and readback, each written to the trail.
The approver is Hartwell Gate's policy (a rule) or a named
person, never the model. An unknown receipt is settled by
readback, never by a second dispatch. Chapter 14 builds the
full lifecycle; this is the minimum the architecture needs.
"""
from __future__ import annotations

import hashlib
import itertools
import re
from pathlib import Path

import yaml

from hrai import gate
from .fakes import Timeout
from .trail import ref

POLICY = yaml.safe_load(
    (Path(__file__).parent / "policy.yaml").read_text())
ZIP = re.compile(r",\s*[A-Z]{2}\s+\d{5}$")


def idem_key(emp: str, field: str, value: str) -> str:
    v = " ".join(re.sub(r"[^\w ]", " ", value.lower()).split())
    raw = f"{emp}|{field}|{v}".encode()
    return "IK-" + hashlib.sha256(raw).hexdigest()[:10]


class Actions:
    def __init__(self, hris, trail, agent_id: str):
        self.hris, self.trail = hris, trail
        self.agent = agent_id
        self.by_key: dict[str, dict] = {}
        self._n = itertools.count(1)

    def propose(self, emp: str, field: str, value: str,
                session_emp: str) -> dict:
        key = idem_key(emp, field, value)
        if key in self.by_key:              # same request again
            a = self.by_key[key]
            self.trail.add("proposal", self.agent,
                           action_id=a["id"], repeat=True)
            return a
        a = {"id": f"CA-{next(self._n):03d}", "emp": emp,
             "field": field, "value": value, "key": key}
        self.by_key[key] = a
        self.trail.add("proposal", self.agent,
                       action_id=a["id"], field=field,
                       value_ref=ref(value), idem_key=key)
        ctx = {"own_record": emp == session_emp,
               "session_verified": True,
               "address_valid": bool(ZIP.search(value))}
        actor = "rule" if field == "home_address" else "human"
        d = gate.evaluate(POLICY, status=field, actor=actor,
                          context=ctx)
        self.trail.add("decision", "hartwell-gate",
                       action_id=a["id"], allowed=d.allowed,
                       reason=d.reason,
                       policy_version=d.policy_version)
        if not d.allowed:
            human = set(d.missing) <= {"approver_id",
                                       "callback_done"}
            a["status"] = ("awaiting_approval"
                           if d.missing and human else "denied")
            a["reason"] = d.reason
            return a
        return self._dispatch(a)

    def _dispatch(self, a: dict) -> dict:
        self.trail.add("dispatch", self.agent,
                       action_id=a["id"], idem_key=a["key"])
        try:
            r = self.hris.write(
                a["emp"], a["field"], a["value"],
                actor=self.agent, action_id=a["id"],
                idem_key=a["key"])
        except Timeout:
            self.trail.add("receipt", "hartwellone",
                           action_id=a["id"], result="unknown")
            a["status"] = "unknown"
            return a
        self.trail.add("receipt", "hartwellone",
                       action_id=a["id"], result="confirmed",
                       change_id=r["change_id"])
        return self._readback(a)

    def _readback(self, a: dict) -> dict:
        now = self.hris.read(a["emp"])[a["field"]]
        ok = now == a["value"]
        self.trail.add("readback", "skeleton",
                       action_id=a["id"], match=ok,
                       value_ref=ref(now))
        a["status"] = "done" if ok else "mismatch"
        return a

    def settle(self) -> list[dict]:
        """After the loop: settle every unknown by readback."""
        return [self._readback(a) for a in self.by_key.values()
                if a.get("status") == "unknown"]
