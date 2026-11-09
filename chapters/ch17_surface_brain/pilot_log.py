"""A synthetic log of the manager pilot's questions, May 27 to
June 9, 2027 (book section "What went wrong on June 9").

The pilot's gateway log kept which documents each question
retrieved, not the answer text. Replaying retrieval over the
logged questions answers one question exactly: how often did
the context a manager's answer was drafted from hold an internal
or personal document that manager may not read? (Another
country's open policy is a wrong-country answer, counted in the
evaluation, not here.) The questions are generated from a
fixed seed and templates; the counts are computed.
"""
from __future__ import annotations

import random

import yaml

from . import entitled, retrieve
from .entitled import DATA

ROLES = ["maintenance technician", "senior maintenance technician",
         "facilities supervisor", "field service technician",
         "apprentice"]
ASK = [
    "What is the pay band for a {r}?",
    "Can I offer a {r} above the band midpoint?",
    "How much annual leave does a {r} get?",
    "What overtime rate applies to a {r} at the weekend?",
    "What is the process if a {r} leaves a plant room unlocked?",
    "How do I set the starting salary for a new {r}?",
    "Can a {r} carry over leave into next year?",
    "What does a {r} earn in our other countries?",
]


def managers(cfg: dict) -> list[dict]:
    out = []
    for ent, n in cfg["managers"].items():
        for k in range(n):
            u = {"id": f"m-{ent.lower()}-{k + 1:02d}",
                 "entities": [ent], "roles": ["manager"]}
            if ent == "US" and k < 3:
                u["union_scopes"] = ["IL-local"]
            out.append(u)
    return out


def questions(cfg: dict) -> list[tuple[dict, str]]:
    rnd = random.Random(cfg["seed"])
    ms = managers(cfg)
    out = []
    for _ in range(cfg["days"]):
        for m in rnd.sample(ms, rnd.randint(14, 22)):
            out.append((m, rnd.choice(ASK).format(r=rnd.choice(ROLES))))
    return out


def replay(design: str = "pilot") -> dict:
    cfg = yaml.safe_load((DATA / "hartwell" / "incident.yaml")
                         .read_text())["pilot"]
    docs, _ = entitled.load("hartwell")
    qs = questions(cfg)
    exposed = personal = 0
    by_doc: dict[str, int] = {}
    for m, q in qs:
        bad = [i for i in retrieve.search(q, m, docs, design)
               if not entitled.can_read(m, docs[i])[0]
               and docs[i]["class"] != "OPEN"]
        exposed += bool(bad)
        personal += any(docs[i]["class"] == "PERSONAL" for i in bad)
        for i in bad:
            by_doc[i] = by_doc.get(i, 0) + 1
    return {"questions": len(qs), "managers": len(managers(cfg)),
            "exposed": exposed, "personal": personal,
            "by_doc": by_doc}
