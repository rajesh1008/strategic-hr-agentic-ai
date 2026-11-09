"""Surface checks (book section "Surface and brain").

A surface is where a person meets the assistant; the brain is
the gateway, retrieval, model and checks behind it. The two are
configured by different teams, so the gateway checks that every
surface matches the status of the use it calls: a surface may
show answers to people only if its use is in production.
"""
from __future__ import annotations

import yaml

from .entitled import DATA


def check(uses: dict, org: str = "hartwell") -> list[str]:
    s = yaml.safe_load((DATA / org / "surfaces.yaml").read_text())
    out = []
    for x in s["surfaces"]:
        st = uses[x["use"]]["status"]
        if x["shows_answer_to_user"] and st != "production":
            out.append(f"{x['id']}: shows answers, but {x['use']} "
                       f"is at {st}")
        if x["identity"] not in ("user sign-in",
                                 "client-issued adviser identity"):
            out.append(f"{x['id']}: no per-person identity")
    return out
