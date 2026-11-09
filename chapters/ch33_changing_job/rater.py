"""Chapter 33: a model as task-exposure rater.

Book section "Which jobs change first". Published exposure
scores often use a model as one of the raters (Eloundou and
others used GPT-4 alongside people). Here the model rates
each task in the six roles (data/roles.yaml): could an
agent with read and draft access, under review, cut the
time the task takes by half or more? Yes or no. Code
compares three runs with each other and with the map's
"exposed" flag. A rating is a hypothesis about a task, not
a measurement of hours.
Run:  python -m chapters.ch33_changing_job.rater
      (needs ANTHROPIC_API_KEY; writes runs/ch33/rater/)
"""
from __future__ import annotations

import json
import re
import sys

from hrai.llm import RunRecorder, model

from .exposure_map import load

THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
SYS = ("You rate tasks for exposure to AI agents. For each "
       "task, answer yes if an agent with read and draft "
       "access to the employer's systems, with a person "
       "reviewing its work, could cut the time the task "
       "takes by half or more; otherwise no. Reply with JSON "
       "only: a list of objects {\"task\": ..., \"exposed\": "
       "true|false}, in the order given.")


def rate(rec: RunRecorder, role: dict) -> dict[str, bool]:
    user = (f"Role: {role['title']}\nTasks:\n" + "\n".join(
        f"- {t['task']}" for t in role["tasks"]))
    r = rec.create(max_tokens=1200, system=SYS,
                   thinking=THINK.get(model(),
                                      {"type": "disabled"}),
                   messages=[{"role": "user", "content": user}])
    text = "".join(b.text for b in r.content
                   if b.type == "text")
    m = re.search(r"\[.*\]", text, re.S)
    rows = json.loads(m.group(0)) if m else []
    return {x["task"]: bool(x["exposed"]) for x in rows}


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    d = load()
    rec = RunRecorder("ch33", "rater")
    got = [{r["id"]: rate(rec, r) for r in d["roles"]}
           for _ in range(runs)]
    rec.note(ratings=got)
    rec.print(f"Exposure rater, model {model()}, {runs} runs")
    rec.print(f"{'role':8}{'tasks':>6}{'agree w/ map':>14}"
              f"{'stable':>8}  hours-weighted yes")
    for r in d["roles"]:
        ts = r["tasks"]
        agree = [sum(1 for t in ts if g[r["id"]].get(t["task"])
                     == t["exposed"]) for g in got]
        stable = sum(1 for t in ts if len({g[r["id"]].get(
            t["task"]) for g in got}) == 1)
        yes = [sum(t["share"] for t in ts
                   if g[r["id"]].get(t["task"])) for g in got]
        mp = sum(t["share"] for t in ts if t["exposed"])
        rec.print(f"{r['id']:8}{len(ts):>6}"
                  f"{min(agree):>7}-{max(agree):<6}"
                  f"{stable:>8}  "
                  + " ".join(f"{y:.0%}" for y in yes)
                  + f" (map {mp:.0%})")
    rec.print("tasks rated differently across runs:")
    for r in d["roles"]:
        for t in r["tasks"]:
            v = [g[r["id"]].get(t["task"]) for g in got]
            if len(set(v)) > 1:
                rec.print(f"  {r['id']:7}{t['task'][:34]:34} "
                          + " ".join("y" if x else "n"
                                     for x in v))
    print(rec.save())


if __name__ == "__main__":
    main()
