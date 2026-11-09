"""Chapter 12: the quality scorecard for the job-architecture data.

Five measures, each a share of records that pass, computed for each
of HartwellOne's three job architectures. Accuracy needs an answer
key, so it is measured only on the forty codes the reward team
reviewed by hand. No model is involved.

Run: HRAI_MODEL=no-model python -m chapters.ch12_data_readiness.quality
(writes runs/ch12/quality/...)
"""
from __future__ import annotations

import csv
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
AS_OF = (2027, 3)          # the register's first full run


def rows(name: str) -> list[dict]:
    with (HERE / "data" / name).open() as f:
        return list(csv.DictReader(l for l in f if not l.startswith("#")))


def grades() -> set[str]:
    g = yaml.safe_load((HERE / "grades.yaml").read_text())
    return set(g["field"]) | set(g["salaried"])


def months_old(ym: str) -> int:
    y, m = (int(x) for x in ym.split("-"))
    return (AS_OF[0] - y) * 12 + AS_OF[1] - m


def scorecard(arch: str) -> dict[str, tuple[int, int]]:
    """(passed, total) per measure for one architecture."""
    cat = [r for r in rows("job_catalog.csv")
           if r["architecture"] == arch and r["status"] == "active"]
    codes = {r["code"]: r for r in rows("job_catalog.csv")}
    titles: dict[str, set[str]] = {}
    for r in cat:
        titles.setdefault(r["title"], set()).add(r["mapped_grade"])
    key = {p["code"]: p for p in yaml.safe_load(
        (HERE / "profiles.yaml").read_text())["profiles"]}
    keyed = [r for r in cat if r["code"] in key]
    ent = {"UKB": "Hartwell UK", "EUCA": None, "HG": "Group"}[arch]
    people = [p for p in rows("local_codes.csv")
              if (ent is None and p["entity"] != "Hartwell UK")
              or p["entity"] == ent]
    live = [p for p in people
            if codes.get(p["local_code"], {}).get("status") == "active"]
    return {
        "complete": (sum(bool(r["desc"]) and r["mapped_grade"]
                         in grades() for r in cat), len(cat)),
        "valid": (len(live), len(people)),
        "unique": (sum(len(titles[r["title"]]) == 1 for r in cat),
                   len(cat)),
        "accurate": (sum(key[r["code"]]["reviewed"] == r["mapped_grade"]
                         for r in keyed), len(keyed)),
        "current": (sum(months_old(r["last_reviewed"]) <= 24
                        for r in cat), len(cat)),
    }


def people_on_rejected() -> tuple[int, int]:
    """People whose code's 2016 mapping the reward team rejects."""
    key = {p["code"]: p for p in yaml.safe_load(
        (HERE / "profiles.yaml").read_text())["profiles"]}
    bad = {c for c, p in key.items() if p["mapped"] != p["reviewed"]}
    ppl = rows("local_codes.csv")
    return sum(p["local_code"] in bad for p in ppl), len(ppl)


def pct(p: tuple[int, int]) -> str:
    return f"{100 * p[0] / p[1]:5.1f}%" if p[1] else "    -"


def main() -> None:
    rec = RunRecorder("ch12", "quality")
    archs = {"HG": "Hartwell Grades", "UKB": "UK legacy bands",
             "EUCA": "EU pay groups"}
    cards = {a: scorecard(a) for a in archs}
    rec.print("Job-architecture scorecard, HartwellOne, March 2027")
    rec.print(f"{'measure':<10}" + "".join(f"{a:>9}" for a in archs))
    for m in ("complete", "valid", "unique", "accurate", "current"):
        rec.print(f"{m:<10}" + "".join(
            f"{pct(cards[a][m]):>9}" for a in archs))
        rec.note(measure=m, **{a: cards[a][m] for a in archs})
    n, tot = people_on_rejected()
    rec.print(f"People on a code whose mapping was rejected: "
              f"{n} of {tot}")
    for a in archs:
        acc = cards[a]["accurate"]
        if acc[1]:
            rec.print(f"{archs[a]}: {acc[0]} of {acc[1]} reviewed "
                      "codes keep their 2016 grade")
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
