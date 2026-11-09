"""Chapter 10: the Pilot Trap check.

Six checks per pilot. A pilot with no owner stops. A pilot whose
value needs a write that nobody has built is stalled at the
integration layer; one that changes something for a person with
no named approver is stalled at the authority layer. Only a pilot
with a baseline, kill criteria and a run owner continues.

Run: HRAI_MODEL=no-model python -m chapters.ch10_diagnose.pilots
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent / "data"
CHECKS = ("baseline", "owner", "write path", "authority",
          "kill criteria", "run owner")


def checks(p: dict) -> dict[str, bool]:
    return {
        "baseline": bool(p.get("baseline")),
        "owner": bool(p.get("owner")),
        "write path": not p["needs_write"] or p["write_built"],
        "authority": not p["changes_person"] or bool(p["approver"]),
        "kill criteria": bool(p.get("kill")),
        "run owner": bool(p.get("run_owner")),
    }


def verdict(c: dict[str, bool]) -> str:
    if not c["owner"]:
        return "stop: no owner"
    if not c["write path"]:
        return "stalled: integration"
    if not c["authority"]:
        return "stalled: authority"
    if c["baseline"] and c["kill criteria"] and c["run owner"]:
        return "continue with kill criteria"
    return "re-scope: problem statement first"


def load() -> list[dict]:
    return yaml.safe_load((DATA / "pilots.yaml").read_text())


def main() -> None:
    from hrai.llm import RunRecorder
    rec = RunRecorder("ch10", "pilots")
    p = rec.print
    pilots = load()
    p(f"HR AI pilots found: {len(pilots)}")
    p("     " + " ".join(f"{c.split()[0][:5]:>5}" for c in CHECKS)
      + "  verdict")
    tally: Counter = Counter()
    for pl in pilots:
        c = checks(pl)
        v = verdict(c)
        tally[v] += 1
        p(f"{pl['id']}  " + " ".join(
            f"{'yes' if c[k] else '-':>5}" for k in CHECKS)
          + f"  {v}")
        rec.note(pilot=pl["id"], name=pl["name"], checks=c,
                 verdict=v)
    p("Passing each check: " + ", ".join(
        f"{k} {sum(checks(x)[k] for x in pilots)}"
        for k in CHECKS))
    full = sum(all(checks(x)[k] for k in
                   ("baseline", "owner", "kill criteria"))
               for x in pilots)
    p(f"Baseline, owner and kill criteria together: {full} of "
      f"{len(pilots)}")
    for v, n in tally.most_common():
        p(f"  {v:<34}{n}")
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
