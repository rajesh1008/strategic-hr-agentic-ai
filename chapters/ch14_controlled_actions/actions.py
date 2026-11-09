"""The controlled-action lifecycle, in full (Chapter 14).

Book section: "The lifecycle in code". Every write an agent
asks for becomes an Action that moves through five steps:
proposal, approval, dispatch, receipt and readback. The code
here, never the model, decides each step:

- the approval matrix (matrix.yaml) names the approver: a
  versioned rule or a person in a named role, never the
  requester, the agent or the requester's manager;
- an approval expires, and can be revoked before dispatch;
- dispatch carries an idempotency key, so a repeat is
  harmless where the system honors it;
- an unknown receipt is settled by readback, then at most
  one re-dispatch with the same key, then a person;
- a readback mismatch goes to a person and is never retried;
- a reversal is a new controlled action, not an edit.
"""
from __future__ import annotations

import hashlib
import itertools
import re
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import yaml

from .fakes import ZIP, Timeout

MATRIX = yaml.safe_load(
    (Path(__file__).parent / "matrix.yaml").read_text())
ABBR = {"street": "st", "avenue": "ave", "apartment": "apt",
        "suite": "ste", "road": "rd", "drive": "dr"}
TERMINAL = {"denied", "revoked", "expired", "done",
            "mismatch", "failed", "needs_person"}


def norm(value: str) -> str:
    """Compare meaning, not bytes: case, commas, St/Street."""
    words = re.sub(r"[^\w ]", " ", value.lower()).split()
    return " ".join(ABBR.get(w, w) for w in words)


def idem_key(emp: str, fld: str, value: str) -> str:
    raw = f"{emp}|{fld}|{norm(value)}".encode()
    return "IK-" + hashlib.sha256(raw).hexdigest()[:10]


@dataclass
class Action:
    id: str
    kind: str
    emp: str
    field: str
    value: str
    requester: str
    key: str
    state: str = "proposed"
    reason: str = ""
    before: str | None = None
    approvals: list = field(default_factory=list)
    steps: list = field(default_factory=list)
    reverses: str | None = None
    dispatches: int = 0
    stored: str | None = None


class Lifecycle:
    def __init__(self, hris, clock,
                 agent: str = "svc-askhartwell-agent",
                 managers: dict | None = None):
        self.hris, self.clock, self.agent = hris, clock, agent
        self.managers = managers or {}
        self.actions: dict[str, Action] = {}
        self.by_key: dict[str, Action] = {}
        self._n = itertools.count(1)

    def _log(self, a: Action, step: str, by: str,
             detail: str = "") -> None:
        a.steps.append((self.clock.stamp(), step, by, detail))

    def _end(self, a: Action, state: str, step: str,
             by: str, reason: str) -> Action:
        a.state, a.reason = state, reason
        self._log(a, step, by, f"{state}: {reason}")
        return a

    # 1. Proposal ---------------------------------------------
    def propose(self, emp: str, fld: str, value: str,
                requester: str,
                verified: bool = True) -> Action:
        key = idem_key(emp, fld, value)
        old = self.by_key.get(key)
        if old and old.state not in {"denied", "revoked",
                                     "expired", "failed"}:
            self._log(old, "proposal", self.agent,
                      "repeat: same key, no new action")
            return old
        kind, row = next(((k, r) for k, r in
                          MATRIX["actions"].items()
                          if r["field"] == fld), (fld, None))
        a = Action(f"CA-{next(self._n):03d}", kind, emp, fld,
                   value, requester, key)
        self.actions[a.id], self.by_key[key] = a, a
        self._log(a, "proposal", self.agent,
                  f"{fld} for {emp}, by {requester}")
        v = MATRIX["version"]
        if row is None or row["requester"] == "none":
            return self._end(a, "denied", "approval", "matrix",
                             f"no agent row for {fld} (v{v})")
        if row["requester"] == "self" and requester != emp:
            return self._end(a, "denied", "approval", "matrix",
                             "not the requester's record")
        checks = {"own_record": requester == emp,
                  "session_verified": verified,
                  "address_valid": bool(ZIP.search(value))}
        if row["approver"] == "rule":
            bad = [c for c in row["rule"] if not checks[c]]
            if bad:
                return self._end(a, "denied", "approval",
                                 "rule",
                                 "failed " + ", ".join(bad))
            self._approve(a, f"rule {kind} v{v}", "rule")
            return self.dispatch(a.id)
        a.state = "awaiting_approval"
        a.reason = (" or ".join(row["approver_roles"])
                    + ", needs " + ", ".join(row["requires"]))
        self._log(a, "approval", "matrix", "awaiting "
                  + a.reason)
        return a

    # 2. Approval ---------------------------------------------
    def _approve(self, a: Action, who: str, role: str) -> None:
        row = MATRIX["actions"][a.kind]
        exp = (self.clock.now()
               + timedelta(minutes=row["approval_ttl_min"]))
        a.approvals.append({"by": who, "role": role,
                            "expires": exp})
        a.state = "approved"
        self._log(a, "approval", who,
                  f"approved, expires {exp:%H:%M}")

    def approve(self, aid: str, approver: str, role: str,
                **checks) -> Action:
        a = self.actions[aid]
        row = MATRIX["actions"][a.kind]
        if a.state != "awaiting_approval":
            self._log(a, "approval", approver,
                      f"refused: action is {a.state}")
            return a
        who = {"requester": a.requester, "agent": self.agent,
               "requester_manager":
                   self.managers.get(a.requester)}
        for b in row.get("not_approver", []):
            if approver == who[b]:
                self._log(a, "approval", approver,
                          f"refused: approver is the {b}")
                return a
        if role not in row["approver_roles"]:
            self._log(a, "approval", approver,
                      f"refused: role {role} not in matrix")
            return a
        miss = [r for r in row["requires"] if not checks.get(r)]
        if miss:
            self._log(a, "approval", approver,
                      "refused: missing " + ", ".join(miss))
            return a
        self._approve(a, approver, role)
        return a

    def revoke(self, aid: str, by: str, reason: str) -> Action:
        a = self.actions[aid]
        if a.dispatches:
            self._log(a, "revoke", by, "refused: dispatched;"
                      " reverse instead")
            return a
        if a.state in TERMINAL:
            self._log(a, "revoke", by, f"no effect: {a.state}")
            return a
        return self._end(a, "revoked", "revoke", by, reason)

    # 3. Dispatch and 4. Receipt ------------------------------
    def dispatch(self, aid: str) -> Action:
        a = self.actions[aid]
        if a.state != "approved":
            self._log(a, "dispatch", "lifecycle",
                      f"refused: action is {a.state}")
            return a
        if self.clock.now() > a.approvals[-1]["expires"]:
            return self._end(a, "expired", "dispatch",
                             "lifecycle", "approve again")
        if a.before is None:
            a.before = self.hris.read(a.emp)[a.field]
        return self._send(a)

    def _send(self, a: Action) -> Action:
        a.dispatches += 1
        self._log(a, "dispatch", "lifecycle",
                  f"attempt {a.dispatches}, key {a.key}")
        try:
            r = self.hris.write(a.emp, a.field, a.value,
                                actor=self.agent,
                                action_id=a.id, key=a.key)
        except Timeout as e:
            self._log(a, "receipt", "hartwellone",
                      f"unknown ({e})")
            return self._settle(a)
        if not r.get("ok"):
            return self._end(a, "failed", "receipt",
                             "hartwellone", r["error"])
        rep = " (repeat key, no new write)" \
            if r.get("repeat") else ""
        self._log(a, "receipt", "hartwellone",
                  f"confirmed {r['change_id']}{rep}")
        return self.readback(a)

    def _settle(self, a: Action) -> Action:
        """Unknown receipt: look before you send again."""
        mine = [c for c in self.hris.changes(a.emp, a.field)
                if c["key"] == a.key]
        if mine:
            self._log(a, "receipt", "lifecycle", "settled by"
                      f" lookup: {mine[0]['change_id']} found")
            return self.readback(a)
        if a.dispatches < 2:
            self._log(a, "receipt", "lifecycle", "not written;"
                      " re-dispatch, same key")
            return self._send(a)
        return self._end(a, "needs_person", "receipt",
                         "lifecycle", "two unknown receipts")

    # 5. Readback ---------------------------------------------
    def readback(self, a: Action) -> Action:
        now = self.hris.read(a.emp)[a.field]
        mode = MATRIX["actions"][a.kind]["readback"]
        ok = (norm(now) == norm(a.value)
              if mode == "normalized" else now == a.value)
        if ok:
            a.state = "done"
            self._log(a, "readback", "lifecycle",
                      f"matches ({mode})")
            return a
        a.stored = now
        return self._end(a, "mismatch", "readback",
                         "lifecycle", "a person decides,"
                         " no retry")

    # Reversal: a new controlled action -----------------------
    def reverse(self, aid: str, by: str,
                reason: str) -> Action:
        a = self.actions[aid]
        if a.state not in {"done", "mismatch"}:
            self._log(a, "reverse", by,
                      f"refused: action is {a.state}")
            return a
        row = MATRIX["actions"][a.kind]
        r = Action(f"CA-{next(self._n):03d}", a.kind, a.emp,
                   a.field, a.before, by,
                   idem_key(a.emp, a.field, a.before) + "-R",
                   reverses=a.id)
        self.actions[r.id] = r
        self._log(r, "proposal", by,
                  f"reverse {a.id}: {reason}")
        self._log(a, "reverse", by, f"reversal {r.id} opened")
        if row["reversal"] == "rule":
            self._approve(r, f"rule {a.kind} reversal", "rule")
            return self.dispatch(r.id)
        r.state = "awaiting_approval"
        r.reason = " or ".join(row["approver_roles"])
        self._log(r, "approval", "matrix", "awaiting "
                  + r.reason)
        return r

    def status_text(self, a: Action) -> str:
        """The one line the agent is told, and must repeat.

        A mismatch carries the value HartwellOne now stores, so
        the agent has no gap to fill with a guess about the
        record (the Chapter 14 open item, closed in Chapter 36).
        """
        shows = (f"HartwellOne now shows {a.stored!r}, which is"
                 " not the value asked for" if a.stored else
                 "HartwellOne shows a different value")
        say = {"done": "done, read back from HartwellOne",
               "awaiting_approval": "not changed yet; waiting"
               " for " + a.reason,
               "mismatch": "not confirmed: " + shows
               + "; an HR adviser will check which is right",
               "needs_person": "not confirmed: HartwellOne did"
               " not answer; an HR adviser will check",
               "approved": "approved, not yet sent"}
        return f"{a.id} {a.field}: " + say.get(
            a.state, f"{a.state}, not changed ({a.reason})")
