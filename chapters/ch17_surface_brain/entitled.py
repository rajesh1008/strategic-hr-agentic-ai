"""Document entitlements for retrieval (deterministic).

Book section: "Entitled retrieval". A document carries labels
set by its owner: entity, audience, class and, where it applies,
a union scope. A user's entities and roles come from the
system of record. The rule is evaluated in code before any
ranking, so a document the user may not read never reaches the
model. Deny by default.
"""
from __future__ import annotations

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def load(org: str) -> tuple[dict, dict]:
    d = DATA / org
    docs = yaml.safe_load((d / "corpus.yaml").read_text())["docs"]
    users = yaml.safe_load((d / "users.yaml").read_text())["users"]
    return ({x["id"]: x for x in docs}, {u["id"]: u for u in users})


def can_read(user: dict, doc: dict) -> tuple[bool, str]:
    roles = set(user.get("roles", []))
    ents = set(user.get("entities", []))
    if doc.get("status") == "superseded":
        return False, "superseded"
    if doc["entity"] != "GROUP" and not (
            doc["entity"] in ents or "ALL" in ents):
        return False, f"entity {doc['entity']}"
    aud = set(doc.get("audience", []))
    if "all" not in aud and not aud & roles:
        return False, "audience"
    scope = doc.get("union_scope")
    if scope and scope not in user.get("union_scopes", []) \
            and not roles & {"hr", "reward"}:
        return False, f"union scope {scope}"
    if doc["class"] == "PERSONAL" and not (
            set(doc.get("personal_roles", [])) & roles):
        return False, "personal"
    return True, "ok"


def readable(user: dict, docs: dict) -> list[str]:
    return [i for i, d in docs.items() if can_read(user, d)[0]]
