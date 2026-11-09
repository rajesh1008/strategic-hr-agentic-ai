"""Entitlements: who may read what about whom (deterministic).

Book section: "The entitlement matrix". The matrix is data
(entitlements.yaml); this module evaluates it. Conditions
are computed from the people records, never taken from the
request or from a model. Deny by default; a "never" class
is refused to everyone except the rules it names; an
aggregate needs at least five people, every one readable.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

HERE = Path(__file__).parent
MATRIX = HERE / "entitlements.yaml"
PEOPLE = HERE / "data" / "people.yaml"
AGENTS = HERE / "agents.yaml"


@dataclass
class Decision:
    allowed: bool
    rule: str
    reason: str


def load(path: Path = MATRIX) -> dict:
    return yaml.safe_load(path.read_text())


def people(path: Path = PEOPLE) -> dict[str, dict]:
    return {p["id"]: p for p in
            yaml.safe_load(path.read_text())["people"]}


def chain(t: dict, db: dict) -> list[str]:
    """Managers above t, nearest first, as of today's record."""
    out, m = [], t.get("reports_to")
    while m and m not in out:
        out.append(m)
        m = db.get(m, {}).get("reports_to")
    return out


def facts(s: dict, t: dict, db: dict) -> dict[str, bool]:
    unit = s.get("unit")
    return {
        "self": s["id"] == t["id"],
        "in_line": s["id"] in chain(t, db),
        "same_entity": s["entity"] == t["entity"],
        "not_unit_peer": not (unit and unit == t.get("unit")),
        "entity_in_scope": t["entity"] in s.get("scope", []),
        "member_authorized": s["id"] in t.get("authorized", []),
        "barrier_clear": not t.get("private_side")
        or s.get("side") == "private",
        "target_partner": bool(t.get("partner")),
        "same_site": s.get("site") == t.get("site"),
    }


def can_read(s: dict, t: dict, cls: str, m: dict,
             db: dict) -> Decision:
    f = facts(s, t, db)
    roles = set(s.get("roles", [])) | {"any"}
    never = {n["class"]: n for n in m.get("never", [])}
    near = []
    for r in m["rules"]:
        if r["role"] not in roles or cls not in r["read"]:
            continue
        failed = [c for c in r["when"] if not f[c]]
        if failed:
            near.append((r["role"] == "any", len(failed),
                         r["id"], failed))
            continue
        n = never.get(cls)
        if n and r["id"] not in n["except"]:
            return Decision(False, "NEVER", n["why"])
        return Decision(True, r["id"], "allowed")
    if cls in never:
        return Decision(False, "NEVER", never[cls]["why"])
    if near:                    # explain the closest rule
        _, _, rid, failed = min(near)
        return Decision(False, rid,
                        "failed: " + ", ".join(failed))
    return Decision(False, "DEFAULT", "no rule allows it")


def view(s: dict, tid: str, m: dict, db: dict,
         ceiling: list[str] | None = None) -> dict:
    """The record as this person (or their agent) may see it."""
    t, out, withheld = db[tid], {"id": tid}, {}
    for cls, fields in m["classes"].items():
        d = can_read(s, t, cls, m, db)
        if not d.allowed:
            withheld[cls] = f"{d.rule}: {d.reason}"
            continue
        if ceiling is not None and cls not in ceiling:
            withheld[cls] = "AGENT: outside the agent's ceiling"
            continue
        for f in fields:
            out[f] = value(t, f)
    out["withheld"] = withheld
    return out


def value(t: dict, f: str):
    if f == "absence_dates":
        return [{"from": a["from"], "to": a["to"]}
                for a in t.get("absence", [])]
    if f == "absence_reason":
        return [a["reason"] for a in t.get("absence", [])]
    return t.get(f)


def aggregate(s: dict, ids: list[str], cls: str, m: dict,
              db: dict) -> Decision | float:
    """Mean over people: five or more, every one readable."""
    n = m["aggregates"]["min_cell"]
    if len(ids) < n:
        return Decision(False, "AGG", f"fewer than {n} people")
    no = [i for i in ids
          if not can_read(s, db[i], cls, m, db).allowed]
    if no:
        return Decision(False, "AGG",
                        f"{len(no)} of {len(ids)} not readable")
    return round(sum(db[i][cls] for i in ids) / len(ids), 2)
