"""Chapter 33: the job-redesign canvas checks.

Book section "The job-redesign canvas". A canvas is the page
a role owner fills in before a job changes. Code checks it
against the task-exposure map (roles.yaml):
  JR-1 the new week adds up: tasks plus freed hours = 1.0
  JR-2 Keep tasks stay whole: no Keep task loses hours
  JR-3 work the agents add is in the job, with hours
  JR-4 freed hours go to a named use, or to a signed
       headcount line, never to "capacity"
  JR-5 no measure on an absorbed task is kept unchanged
  JR-6 every new task names its skills and a plan row
  JR-7 grade review dated when changed is 20% or more
  JR-8 consultation route recorded; job holders reviewed
No model.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch33_changing_job.canvas
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

from .exposure_map import load, reading

VAGUE = {"capacity", "efficiency", "productivity", "tbd"}


def check(c: dict, role: dict, d: dict) -> dict[str, str]:
    """Return check id -> "" (pass) or a short reason."""
    after = {t["task"]: t for t in c["after"]}
    before = {t["task"]: t for t in role["tasks"]}
    x = reading(role, d["weights"], d["review_share"])
    out: dict[str, str] = {}
    total = (sum(t["share"] for t in c["after"])
             + sum(f["share"] for f in c["freed_to"]))
    out["JR-1"] = ("" if abs(total - 1) <= 0.01
                   else f"week sums to {total:.2f}")
    lost = [k for k, t in before.items() if t["side"] == "keep"
            and after.get(k, {"share": 0})["share"]
            < t["share"] - 1e-9]
    out["JR-2"] = ("" if not lost
                   else "Keep task loses hours: " + lost[0])
    miss = [a["task"] for a in role.get("adds", [])
            if a["task"] not in after]
    out["JR-3"] = "" if not miss else "missing: " + miss[0]
    bad = [f["use"] for f in c["freed_to"]
           if f["use"].lower() in VAGUE
           or (f.get("headcount") and not f.get("signed"))]
    out["JR-4"] = "" if not bad else f'freed to "{bad[0]}"'
    gone = {k for k, t in before.items()
            if t["side"] == "automate" and t["rate"] > 0
            and d["weights"][t["status"]] > 0}
    kept = [m["name"] for m in c["measures"]
            if m["task"] in gone and m["action"] == "kept"]
    out["JR-5"] = "" if not kept else "kept: " + kept[0]
    noplan = [t["task"] for t in c["after"] if t.get("new")
              and not (t.get("skills") and t.get("plan"))]
    out["JR-6"] = "" if not noplan else "no plan: " + noplan[0]
    need = x["changed"] >= 0.20
    out["JR-7"] = ("" if not need or c.get("grade_review")
                   else f"changed {x['changed']:.0%}, "
                   "no grade review")
    out["JR-8"] = ("" if c.get("consultation")
                   and c.get("holders_reviewed")
                   else "no route or holders not asked")
    return out


def main() -> None:
    d = load()
    cs = yaml.safe_load((Path(__file__).resolve().parent
                         / "data" / "canvases.yaml").read_text())
    roles = {r["id"]: r for r in d["roles"]}
    rec = RunRecorder("ch33", "canvas")
    ids = [f"JR-{i}" for i in range(1, 9)]
    rec.print("Job-redesign canvas checks (synthetic)")
    rec.print(f"{'canvas':11}" + "".join(
        f"{i[3:]:>3}" for i in ids) + "  passed")
    results = []
    for c in cs["canvases"]:
        r = check(c, roles[c["role"]], d)
        n = sum(1 for v in r.values() if not v)
        rec.print(f"{c['id']:11}" + "".join(
            f"{'.' if not r[i] else 'x':>3}" for i in ids)
            + f"  {n} of 8")
        results.append((c["id"], r))
    rec.print(". = pass, x = fail; reasons:")
    for cid, r in results:
        for i in ids:
            if r[i]:
                rec.print(f"  {cid:11}{i}  {r[i][:44]}")
    rec.note(results={k: v for k, v in results})
    print(rec.save())


if __name__ == "__main__":
    main()
