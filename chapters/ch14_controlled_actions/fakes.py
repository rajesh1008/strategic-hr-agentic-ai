"""In-memory HartwellOne with injectable faults (synthetic).

Book section: "Five ways a write goes wrong". The fake system
of record keeps employee records, its own audit log and the
idempotency keys it has seen. A fault can be queued for the
next write:

  lose_reply  the write lands, the caller sees a timeout
  drop        the call times out and nothing is written
  reject      HartwellOne refuses the value (E_VALIDATION)
  overwrite   the write lands, then another actor changes
              the same field before anyone reads it back
  normalize   HartwellOne stores its own postal form of the
              address (upper case, "St" for "Street")

`honor_keys=False` models a downstream system that ignores
idempotency keys, so a repeat writes twice. No model, no real
system and no real person is involved.
"""
from __future__ import annotations

import copy
import itertools
import re
from datetime import datetime, timedelta

SEED = {
    "HW-012771": {"name": "Lena Ruiz",
                  "home_address": "1450 Ogden St, Apt 3,"
                  " Denver, CO 80218",
                  "bank_account": "Front Range CU ****4417",
                  "phone_on_file": "***-***-0193"},
    "HW-019044": {"name": "Diego Ruiz",
                  "home_address": "1450 Ogden St, Apt 3,"
                  " Denver, CO 80218",
                  "bank_account": "Front Range CU ****2280",
                  "phone_on_file": "***-***-7751"},
    "HW-015118": {"name": "Tomas Reyes",
                  "home_address": "88 Rampart Way,"
                  " Aurora, CO 80011",
                  "bank_account": "Mile High Bank ****0921",
                  "phone_on_file": "***-***-4410"},
}


class Timeout(Exception):
    """HartwellOne did not answer; the outcome is unknown."""


class Clock:
    """A test clock, so expiry can be shown without waiting."""

    def __init__(self, start: str = "2027-05-18T09:00"):
        self.t = datetime.fromisoformat(start)

    def now(self) -> datetime:
        return self.t

    def advance(self, minutes: int) -> None:
        self.t += timedelta(minutes=minutes)

    def stamp(self) -> str:
        return self.t.strftime("%H:%M")


ZIP = re.compile(r",\s*[A-Z]{2}\s+\d{5}$")


def postal(value: str) -> str:
    v = re.sub(r"\bStreet\b", "St", value)
    return re.sub(r",", "", v).upper()


class HartwellOne:
    FIELDS = ("home_address", "bank_account")

    def __init__(self, seed: dict | None = None,
                 honor_keys: bool = True):
        self.rec = copy.deepcopy(seed or SEED)
        self.audit: list[dict] = []
        self.seen: dict[str, dict] = {}
        self.honor_keys = honor_keys
        self.faults: list[str] = []
        self.emp_faults: dict[str, list[str]] = {}
        self.notices: list[dict] = []   # sent by HartwellOne
        self._ids = itertools.count(7001)

    def inject(self, *faults: str, emp: str | None = None
               ) -> None:
        """Queue faults for the next writes, or one person's."""
        if emp:
            self.emp_faults.setdefault(emp, []).extend(faults)
        else:
            self.faults.extend(faults)

    def _fault(self, emp: str) -> str | None:
        mine = self.emp_faults.get(emp)
        if mine:
            return mine.pop(0)
        return self.faults.pop(0) if self.faults else None

    def read(self, emp: str) -> dict:
        return dict(self.rec[emp])

    def changes(self, emp: str, field: str) -> list[dict]:
        return [a for a in self.audit
                if a["employee"] == emp and a["field"] == field]

    def write(self, emp: str, field: str, value: str, *,
              actor: str, action_id: str, key: str) -> dict:
        fault = self._fault(emp)
        if fault == "drop":
            raise Timeout("no reply after 30 s")
        if self.honor_keys and key in self.seen:
            return dict(self.seen[key], repeat=True)
        if field not in self.FIELDS:
            return {"ok": False, "error": "E_FIELD"}
        if fault == "reject" or (field == "home_address"
                                 and not ZIP.search(value)):
            return {"ok": False, "error": "E_VALIDATION"}
        change = f"CH-{next(self._ids)}"
        self.rec[emp][field] = (postal(value)
                                if fault == "normalize"
                                else value)
        self.audit.append({"change_id": change, "employee": emp,
                           "field": field, "actor": actor,
                           "action_id": action_id, "key": key})
        if field == "bank_account":
            self.notices.append({"employee": emp,
                                 "to": "old and new contact",
                                 "change_id": change})
        result = {"ok": True, "change_id": change}
        self.seen[key] = result
        if fault == "overwrite":
            other = f"CH-{next(self._ids)}"
            self.rec[emp][field] = value.replace(
                "Apt 5", "Apt 15")
            self.audit.append({"change_id": other,
                               "employee": emp, "field": field,
                               "actor": "adviser MNL-T1-0442",
                               "action_id": None, "key": None})
        if fault == "lose_reply":
            raise Timeout("reply lost after the write")
        return result
