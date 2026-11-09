"""Chapter 36: the closing Scoreboard (deterministic).

Book section "The closing Scoreboard". The ten objectives
of the Hartwell program (synthetic) are split into the
commitments each made; every commitment carries the state
the record shows on June 30, 2028. The verdict for an
objective is computed, never typed: met when every
commitment is done, partly met when some are, open when
none is. The script also counts the decision records,
refusals, returns and falls, and weighs the board-pack
numbers with the Claim-Status Ledger's base-case weights.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch36_table.scoreboard
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from hrai.ledger import BASE_CASE_WEIGHT, Status
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
LEDGER = {"measured": Status.PRODUCTION, "shadow": Status.SHADOW,
          "tested": Status.TESTED, "claimed": Status.CLAIMED}


def load(name: str) -> dict:
    return yaml.safe_load((HERE / "data" / name).read_text())


def verdict(obj: dict) -> str:
    """Met, partly met or open, from the commitments only."""
    states = [c["state"] for c in obj["commitments"]]
    if all(s == "done" for s in states):
        return "met"
    if any(s in ("done", "partly") for s in states):
        return "partly met"
    return "open"


def weight(status: str) -> float:
    """Board weight: ledger base case; anything else is 0."""
    s = LEDGER.get(status)
    return BASE_CASE_WEIGHT[s] if s is not None else 0.0


def main() -> None:
    rec = RunRecorder("ch36", "scoreboard")
    sb, dr = load("scoreboard.yaml"), load("records.yaml")
    rec.print("Closing Scoreboard, June 30, 2028 (synthetic)")
    verdicts = Counter()
    for o in sb["objectives"]:
        v = verdict(o)
        if o["n"] == 10:
            v = "this chapter"
        else:
            verdicts[v] += 1
        done = sum(c["state"] == "done" for c in o["commitments"])
        rec.print(f"  O{o['n']:<2} {o['name']:<38} {done}/"
                  f"{len(o['commitments'])} done  {v}")
        for c in o["commitments"]:
            if c["state"] != "done":
                rec.print(f"      {c['state']:<6} {c['text']}: "
                          f"{c['evidence']}")
    rec.print(f"Objectives 1-9: met {verdicts['met']}, partly met "
              f"{verdicts['partly met']}, open {verdicts['open']}")
    nh = sb["named_human"]
    rec.print(f"Named-human count: {nh['before']} -> {nh['after']}, "
              f"reported 0 in {len(nh['reported_zero_in'])} of 35 "
              f"chapters; scope last stated: "
              f"{nh['scope_last_stated']}")
    records = dr["records"]
    dated = sorted(r["date"] for r in records if r["date"])
    rec.print(f"Decision records: {len(records)} ({len(dated)} dated,"
              f" {dated[0]:%B %-d, %Y} to {dated[-1]:%B %-d, %Y})")
    owners = Counter(r["owner"] for r in records)
    rec.print("  owners: " + ", ".join(
        f"{k} {v}" for k, v in owners.most_common()))
    refused = [r for r in records if r.get("refused")]
    kinds = Counter(r["refused"] for r in refused)
    rec.print(f"  records that refuse something: {len(refused)} "
              f"({', '.join(f'{k} {v}' for k, v in sorted(kinds.items()))})")
    ret = dr["returns"]
    rec.print(f"Returns to an earlier gate: {len(ret)} "
              f"({sum(r['gate'] for r in ret)} gate refusals)")
    rec.print(f"Planned falls: {len(dr['falls'])}; each answered by "
              f"a recorded change:")
    for f in dr["falls"]:
        rec.print(f"  ch{f['ch']:<2} {f['fall']} -> {f['after']}")
    rec.print("Board pack, by ledger base-case weight:")
    by = Counter()
    for p in sb["pack"]:
        w = weight(p["status"])
        by[p["status"]] += 1
        rec.print(f"  {w:.1f}  {p['status']:<12} {p['figure']}")
    full = sum(weight(p["status"]) == 1.0 for p in sb["pack"])
    rec.print(f"Results page carries {full} of {len(sb['pack'])}; "
              + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))
    rec.note(verdicts=dict(verdicts), records=len(records),
             refused=len(refused), returns=len(ret),
             falls=len(dr["falls"]), pack=dict(by), full=full,
             owners=dict(owners))
    rec.save()


if __name__ == "__main__":
    main()
