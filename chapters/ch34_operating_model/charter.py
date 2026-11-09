"""Chapter 34: the forum charter as data, checks FC-1 to FC-6.

Book section "A forum that decides nothing". The Hartwell
People Systems Forum charter (synthetic): v0 is Claire
Whitfield's operating-model slide turned into rows by her
team in February 2028; v1 is the charter signed with
DR-34-01 on April 17, 2028. No model is involved.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch34_operating_model.charter
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
NEVER_DECIDE = {"AUDIT", "OPERATOR", "VENDOR"}


def load() -> dict:
    return yaml.safe_load(
        (HERE / "data" / "charter.yaml").read_text())


def check(row: dict, people: list[str]) -> dict:
    d = row["decides"]
    return {
        "FC-1": d in people,             # a person decides
        "FC-2": d != row.get("prepares"),
        "FC-3": d not in NEVER_DECIDE,
        "FC-4": bool(row.get("told")),
        "FC-5": bool(row.get("record")),
        "FC-6": row.get("does") is not None,
    }


def lookup(rows: list[dict], decision: str,
           column: str = "decides") -> str:
    """The deterministic answer: read the row."""
    for r in rows:
        if r["id"] == decision:
            return r[column]
    return "NOT_SET"


def main() -> None:
    rec = RunRecorder("ch34", "charter")
    c = load()
    names = [f"FC-{i}" for i in range(1, 7)]
    ids = {v: {r["id"] for r in c["versions"][v]}
           for v in ("v0", "v1")}
    for v in ("v0", "v1"):
        rows = c["versions"][v]
        res = [(r["id"], check(r, c["people"])) for r in rows]
        ok = sum(all(x.values()) for _, x in res)
        rec.print(f"== charter {v}: {len(rows)} decisions, "
                  f"{ok} pass all six checks")
        for part in (names[:3], names[3:]):
            rec.print("   " + " ".join(
                f"{n} {sum(x[n] for _, x in res)}/"
                f"{len(res)}" for n in part))
        for i, x in res:
            bad = [n for n in names if not x[n]]
            if bad:
                r = next(r for r in rows if r["id"] == i)
                rec.print(f"   {i} {r['decides']:<8} fails "
                          + ", ".join(bad))
        rec.note(version=v, results=res)
    missing = sorted(ids["v1"] - ids["v0"])
    rec.print(f"== in v1, not on the slide: {len(missing)} "
              f"({', '.join(missing)})")
    rec.save()


if __name__ == "__main__":
    main()
