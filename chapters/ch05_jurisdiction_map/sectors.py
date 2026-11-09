"""Chapter 5: the same lookup at three sector organizations.

Fieldnote (software; 31 US states, Dublin, Sydney and staff in
Spain, Poland and Portugal through an employer of record),
Pennant Stores (retail scheduling in Canada and US cities) and
Larkspur Hotels (one-way video for front-desk hiring). All
synthetic. No model is involved.

Run: HRAI_MODEL=no-model python -m chapters.ch05_jurisdiction_map.sectors
(writes runs/ch05/sectors/...)
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

import yaml

from hrai import law
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
ORDER = ["APPLIES", "PAUSED", "UNCLEAR", "GAP"]


def lanes(org: dict) -> list[dict]:
    return [x if isinstance(x, dict) else {"code": x}
            for x in org["lanes"]]


def run_org(org, design, rules, as_of):
    """Yield (lane, step id, Finding) for one org and design."""
    over = (org.get("designs") or {}).get(design, {})
    for ln in lanes(org):
        for s in org["steps"]:
            s2 = {**s, **over.get(s["id"], {})}
            f = law.Facts(place=ln["code"], decision=s2["decision"],
                          ai=s2["ai"], employees=org["employees"],
                          subject=s2.get("subject", "applicant"),
                          features=frozenset(s2.get("features", [])),
                          via_eor=ln.get("via_eor", False))
            for x in law.obligations(f, as_of, rules):
                yield ln["code"], s["id"], x


def report(rec, name, org, design, rules, as_of):
    """Print findings, folding places whose findings are identical."""
    per: dict[str, list] = {ln["code"]: [] for ln in lanes(org)}
    count = Counter()
    for site, step, x in run_org(org, design, rules, as_of):
        what = x.rule_id or x.note
        if x.outcome == "GAP" and x.note.startswith("no rules"):
            what, step = f"no rules recorded for {x.lane}", "*"
        when = "" if x.when in ("", "in force") else x.when[5:]
        item = (ORDER.index(x.outcome), x.outcome, step, what,
                ",".join(x.duties), when,
                x.note.split(";")[0] if x.outcome == "UNCLEAR"
                else "")
        if item not in per[site]:
            per[site].append(item)
            count[x.outcome] += 1
    groups: dict[tuple, list] = {}
    for site, items in per.items():
        groups.setdefault(tuple(sorted(items)), []).append(site)
    title = name + (f" ({design})" if design else "")
    rec.print(f"{title}: {len(per)} places")
    rec.print("  " + ", ".join(f"{k} {count[k]}" for k in ORDER))
    for items, sites in groups.items():
        head = " ".join(sites) if len(sites) <= 3 else (
            f"{len(sites)} places: " + " ".join(sites[:3]) + " ...")
        rec.print(f"  [{head}]")
        if not items:
            rec.print("    no recorded rule reaches this step")
        for _, out, step, what, duty, when, why in items:
            rec.print(f"    {out:<8}{step} {what} {duty} {when}"
                      .rstrip())
            if why:
                rec.print(f"{'':<15}{why}")
    rec.print("")


def main() -> None:
    data = yaml.safe_load((HERE / "sectors.yaml").read_text())
    as_of = date.fromisoformat(str(data["as_of"]))
    rules = law.load_rules()
    rec = RunRecorder("ch05", "sectors")
    rec.print(f"As of {as_of}; every finding is [VERIFY]")
    rec.print("")
    for name, org in data["orgs"].items():
        for design in (org.get("designs") or {"": None}):
            report(rec, name, org, design, rules, as_of)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
