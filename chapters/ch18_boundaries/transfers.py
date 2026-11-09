"""The transfer register, checked and reconciled.

Book section: "The transfer register". Two passes, no model.
1. Each register row needs the mechanism its source lane
   expects and, where the lane expects one, a dated
   assessment and an owner.
2. Every cross-border read in the access log must match a
   register row by store, lane and recipient site. Reads that
   match nothing are flows the agent stack created on its
   own: debug access, evaluation copies, index replicas.
A remote view is a transfer (Chapter 18 cites the EDPB and
ICO on this), so a read from another country counts even
when no file moves. All data synthetic.

Run: HRAI_MODEL=no-model python -m \\
         chapters.ch18_boundaries.transfers
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"
HOME = {"NL": "EU", "DE": "EU", "UK": "UK", "CA": "CA",
        "AU": "AU", "US": "US"}
# lane -> (mechanisms accepted, assessment required)
RULE = {"EU": ({"SCCs", "adequacy"}, True),
        "UK": ({"IDTA", "Addendum", "adequacy"}, True),
        "CA": ({"contract"}, True),
        "AU": ({"contract"}, True),
        "US": (set(), False)}


def check_row(x: dict) -> list[str]:
    gaps = []
    for lane in x["lanes"]:
        ok, need = RULE[HOME[lane]]
        m = x["mechanism"]
        m = m.get(lane, "") if isinstance(m, dict) else m
        if ok and m not in ok:
            gaps.append(f"{lane}: {m or 'nothing'} not a"
                        " mechanism for this lane")
        if need and not x["assessment"]:
            gaps.append(f"{lane}: no dated assessment")
    if not x["owner"]:
        gaps.append("no owner")
    return sorted(set(gaps))


def reconcile(reg: list[dict], log: list[dict]):
    for a in log:
        hit = [x["id"] for x in reg
               if x["store"] == a["store"]
               and a["lane"] in x["lanes"]
               and x["site"] == a["site"]]
        yield a, hit


def log_month(month: str) -> str:
    return {"": "May 2027", "aug": "August 2027"}[month]


def main(month: str = "") -> None:
    sfx = f"_{month}" if month else ""
    rec = RunRecorder("ch18", "transfers" + sfx)
    reg = yaml.safe_load(
        (DATA / f"register{sfx}.yaml").read_text())
    log = yaml.safe_load(
        (DATA / f"access_log{sfx}.yaml").read_text())
    rec.print("Register rows")
    for x in reg:
        gaps = check_row(x)
        rec.note(row=x["id"], gaps=gaps)
        rec.print(f"  {x['id']} {x['site']:<6} {x['mode']:<13}"
                  + (" ok" if not gaps else " GAP " +
                     "; ".join(gaps)))
    rec.print(f"Access log, {log_month(month)}")
    missing = 0
    for a, hit in reconcile(reg, log):
        who = f"{a['principal']} {a['lane']} {a['store']}"
        if hit:
            rec.print(f"  {who:<38} on {','.join(hit)}")
        else:
            missing += 1
            rec.print(f"  {who:<38} NOT ON REGISTER"
                      f" ({a['records']} records)")
    rec.print(f"Flows not on the register: {missing} of"
              f" {len(log)}")
    print(rec.save())


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:2])
