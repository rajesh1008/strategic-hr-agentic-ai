"""Chapter 33: the task-exposure map.

Book section "Which jobs change first". For each role, from
a two-week diary of tasks and hours, code reports five
numbers side by side so none can stand in for another:
  exposed  share of hours an occupation-level score flags
  gone     hours the agents absorb, each rate weighted by
           its claim status (Chapter 4 planning weights)
  review   hours of checking that absorbed work creates
           (15% of absorbed hours, as in Chapter 8)
  added    new tasks the agents hand to the job holder
  changed  gone + review + added: the share of the old week
           that is now different work
and freed, the net hours a week returned (gone less review
less added). Roles, never people. No model.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch33_changing_job.exposure_map
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"


def load(name: str = "roles.yaml") -> dict:
    return yaml.safe_load((DATA / name).read_text())


def reading(role: dict, weights: dict, review: float) -> dict:
    t = role["tasks"]
    exposed = sum(x["share"] for x in t if x["exposed"])
    gone = sum(x["share"] * x["rate"] * weights[x["status"]]
               for x in t if x["side"] == "automate")
    rev = gone * review
    added = sum(a["share"] for a in role.get("adds", []))
    return {"exposed": exposed, "gone": gone, "review": rev,
            "added": added, "changed": gone + rev + added,
            "freed": gone - rev - added}


def main() -> None:
    d = load()
    rec = RunRecorder("ch33", "exposure_map")
    rows = []
    for r in d["roles"]:
        x = reading(r, d["weights"], d["review_share"])
        x.update(id=r["id"], people=r["people"],
                 hours=r["hours"])
        rows.append(x)
    rec.print("Task-exposure map (synthetic), share of the "
              "old week")
    rec.print(f"{'role':7}{'people':>7}{'exposed':>9}"
              f"{'gone':>7}{'review':>7}{'added':>7}"
              f"{'changed':>9}{'freed':>7}")
    for x in rows:
        rec.print(f"{x['id']:7}{x['people']:>7}"
                  f"{x['exposed']:>9.0%}{x['gone']:>7.1%}"
                  f"{x['review']:>7.1%}{x['added']:>7.1%}"
                  f"{x['changed']:>9.1%}{x['freed']:>7.1%}")
    rec.print("gone: absorbed at ch04 weights; review: 15% "
              "of gone")
    rec.print("changed = gone + review + added")
    rec.print("freed = gone - review - added")
    by_exp = [x["id"] for x in sorted(
        rows, key=lambda x: -x["exposed"])]
    by_chg = [x["id"] for x in sorted(
        rows, key=lambda x: -x["changed"])]
    rec.print("rank by exposed: " + ", ".join(by_exp))
    rec.print("rank by changed: " + ", ".join(by_chg))
    rec.print("net hours a week returned, all holders:")
    for x in rows:
        h = x["freed"] * x["hours"] * x["people"]
        rec.print(f"  {x['id']:7}{x['freed'] * x['hours']:>5.1f}"
                  f" h each{h:>9,.0f} h in total")
    fs = next(r for r in d["roles"] if r["id"] == "FS-US")
    rec.print("FS-US tasks: share, side, rate, status")
    for t in fs["tasks"]:
        rec.print(f"  {t['task'][:34]:34}{t['share']:>4.0%} "
                  f"{t['side']:8}{t['rate']:>4.0%} {t['status']}")
    for a in fs["adds"]:
        rec.print(f"  + {a['task'][:42]:42}{a['share']:>4.0%}"
                  " new")
    rec.note(rows=rows)
    print(rec.save())


if __name__ == "__main__":
    main()
