"""One engine, four organizations (deterministic).

Book sections: the sector cases. Lakemont, Cobbleford and
Thorne Kessler run their own matrices through entitle.py;
an agent request reads the intersection of the person's
entitlements and the agent's ceiling. Straits Ledger's
quarterly review of agent identities runs four checks.
Run: HRAI_MODEL=no-model python -m \
     chapters.ch15_guardrails.sectors
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from hrai.llm import RunRecorder
from . import entitle as E

DATA = Path(__file__).parent / "data"


def decide(case: dict, req: dict) -> E.Decision:
    db = {p["id"]: p for p in case["people"]}
    s = dict(db[req["who"]], roles=req["roles"])
    d = E.can_read(s, db[req["about"]], req["cls"],
                   case["matrix"], db)
    if d.allowed and req.get("agent") and \
            req["cls"] not in case["agent_ceiling"]:
        return E.Decision(False, "AGENT",
                          "outside the agent's ceiling")
    return d


def review(cfg: dict) -> list[tuple[str, str]]:
    today = date.fromisoformat(cfg["as_of"])
    old = lambda s: (today - date.fromisoformat(s)).days > 90
    out = []
    for i in cfg["identities"]:
        if not i.get("owner") or "team" in i["owner"]:
            out.append((i["id"], "SL-1 no named owner"))
        for g in i["grants"]:
            if old(g["last_used"]):
                out.append((i["id"], f"SL-2 unused 90 days: "
                                     f"{g['name']}"))
        if i["privileged"] and old(i["last_review"]):
            out.append((i["id"], "SL-3 privileged, not "
                                 "reviewed this quarter"))
        if i.get("used_by_agent") and i["type"] == "human":
            out.append((i["id"], "SL-4 agent uses a person's"
                                 " account"))
    return out


def main() -> None:
    cases = yaml.safe_load((DATA / "sectors.yaml").read_text())
    rec = RunRecorder("ch15", "sectors")
    rec.print("Sector entitlement cases (synthetic)")
    for key, case in cases.items():
        ok = 0
        rec.print(f"{case['org']} (matrix "
                  f"{case['matrix']['version']})")
        for r in case["requests"]:
            d = decide(case, r)
            got = "allow" if d.allowed else "deny"
            ok += got == r["expect"]
            rec.print(f"  {got:<5} {d.rule:<6} {r['note']}")
        rec.print(f"  as designed: {ok} of "
                  f"{len(case['requests'])}")
    ids = yaml.safe_load(
        (DATA / "straits_identities.yaml").read_text())
    found = review(ids)
    rec.print(f"Straits Ledger agent identity review, "
              f"{ids['as_of']}: {len(ids['identities'])} "
              f"identities, {len(found)} findings")
    for i, f in found:
        rec.print(f"  {i:<17} {f}")
    print(rec.save())


if __name__ == "__main__":
    main()
