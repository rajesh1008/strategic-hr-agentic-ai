"""In-memory HartwellOne, the system of record (synthetic).

Book section: "The system-of-record rule". HartwellOne holds
the employee record and its own audit log. Every write names
the identity that made it, the action it serves and an
idempotency key; a repeated key returns the first result and
writes nothing. `lose_reply_once` applies the first write and
then raises Timeout, the partial failure the chapter uses.
Nothing here calls a model or a real system.
"""
from __future__ import annotations

import copy
import itertools

SEED = {
    "HW-012771": {
        "name": "Lena Ruiz",
        "entity": "Hartwell US",
        "home_address": "1450 Ogden St, Apt 3, Denver, CO 80218",
        "bank_account": "Front Range CU ****4417",
        "manager_id": "HW-012927",
    },
}


class Timeout(Exception):
    """HartwellOne did not answer; the outcome is unknown."""


class HartwellOne:
    FIELDS = ("home_address", "bank_account", "manager_id")

    def __init__(self, lose_reply_once: bool = False):
        self.rec = copy.deepcopy(SEED)
        self.version = {k: 1 for k in self.rec}
        self.audit: list[dict] = []
        self._seen: dict[str, dict] = {}
        self._ids = itertools.count(5001)
        self._lose = lose_reply_once

    def read(self, emp: str) -> dict:
        r = dict(self.rec[emp])
        r["version"] = self.version[emp]
        return r

    def write(self, emp: str, field: str, value: str, *,
              actor: str, action_id: str, idem_key: str) -> dict:
        if idem_key in self._seen:          # repeat: no write
            return dict(self._seen[idem_key], repeat=True)
        if field not in self.FIELDS:
            return {"ok": False, "error": "E_FIELD"}
        old = self.rec[emp][field]
        self.rec[emp][field] = value
        self.version[emp] += 1
        change = f"CH-{next(self._ids)}"
        self.audit.append({
            "change_id": change, "employee": emp,
            "field": field, "actor": actor,
            "action_id": action_id, "idem_key": idem_key,
            "version": self.version[emp],
            "changed": old != value})
        reply = {"ok": True, "change_id": change,
                 "version": self.version[emp]}
        self._seen[idem_key] = reply
        if self._lose:
            self._lose = False
            raise Timeout("no reply within 10 s")
        return reply
