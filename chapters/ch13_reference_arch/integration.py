"""Integration contract checks (deterministic).

Book section: "Integration patterns". Six checks on every
interface an agent reads or writes through:
INT-1 a named owner on the client side of the data;
INT-2 a write path is idempotent and returns error codes;
INT-3 the agent acts as its own service identity;
INT-4 data is fresh enough for the use;
INT-5 no screen automation for an agent;
INT-6 a timeout is declared for every call.

Run: HRAI_MODEL=no-model python -m \
     chapters.ch13_reference_arch.integration
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).parent / "data" / "integrations.yaml"
SUPPLIER = ("Quayfen",)


def check(i: dict, needs: dict) -> list[str]:
    if i["use"] == "none":
        return []
    bad = []
    if not i["owner"] or i["owner"].startswith(SUPPLIER):
        bad.append("INT-1")
    if i["use"] == "act" and not (i["idempotent"]
                                  and i["errors"]):
        bad.append("INT-2")
    if i["identity"] != "service":
        bad.append("INT-3")
    if i["fresh_min"] > needs[i["use"]]:
        bad.append("INT-4")
    if i["pattern"] == "screen":
        bad.append("INT-5")
    if i["pattern"] not in ("batch file", "vendor batch") \
            and not i["timeout_s"]:
        bad.append("INT-6")
    return bad


def main() -> None:
    rec = RunRecorder("ch13", "integration")
    doc = yaml.safe_load(DATA.read_text())
    for s in doc["sets"]:
        used = [i for i in s["interfaces"] if i["use"] != "none"]
        res = {i["id"]: check(i, doc["needs"]) for i in used}
        ok = sum(1 for v in res.values() if not v)
        pats = Counter(i["pattern"] for i in used)
        rec.print(f"{s['org']} {s['version']}: {len(used)} "
                  f"agent interfaces, {ok} pass")
        rec.print("  patterns: " + ", ".join(
            f"{k} {v}" for k, v in sorted(pats.items())))
        for i in used:
            if res[i["id"]]:
                rec.print(f"  {i['id']} {i['name']:26} "
                          + " ".join(res[i["id"]]))
        fails = Counter(r for v in res.values() for r in v)
        rec.print("  by check: " + (", ".join(
            f"{k} {v}" for k, v in sorted(fails.items()))
            or "none"))
        rec.note(**{f"{s['org']} {s['version']}": res})
    print(rec.save())


if __name__ == "__main__":
    main()
