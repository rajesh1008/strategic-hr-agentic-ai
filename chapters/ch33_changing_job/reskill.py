"""Chapter 33: reskilling plan checks.

Book section "Reskilling tied to task change". A plan
passes only if it is built from a canvas and pays off in
work, not in course completions:
  RS-1 starts from a canvas, and every skill is one the
       canvas names for a new task
  RS-2 every skill has learning and supervised practice
  RS-3 a destination role with a start date
  RS-4 learning is paid and inside working hours
  RS-5 pay is held while people learn
  RS-6 outcome is doing the new tasks at six months and
       employed at twelve, not completion
No model.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch33_changing_job.reskill
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"
OUTCOMES = {"doing new tasks at 6 months",
            "employed at 12 months"}


def canvas_skills(canvases: list[dict]) -> dict[str, set]:
    return {c["id"]: {s for t in c["after"] if t.get("new")
                      for s in t.get("skills", [])}
            for c in canvases}


def check(p: dict, skills: dict[str, set]) -> dict[str, str]:
    out: dict[str, str] = {}
    src = p.get("from_canvas")
    if not src:
        out["RS-1"] = "no canvas"
    else:
        extra = [s["skill"] for s in p["skills"]
                 if s["skill"] not in skills.get(src, set())]
        out["RS-1"] = "" if not extra else "not on canvas: " \
            + extra[0]
    nop = [s["skill"] for s in p["skills"]
           if not (s.get("learning_h") and s.get("practice"))]
    out["RS-2"] = "" if not nop else "no practice: " + nop[0]
    dst = p.get("destination") or {}
    out["RS-3"] = ("" if dst.get("role") and dst.get("start")
                   else "no destination role or date")
    out["RS-4"] = ("" if p.get("paid_in_hours")
                   else "learning outside paid hours")
    out["RS-5"] = "" if p.get("pay_held") else "pay not held"
    out["RS-6"] = ("" if OUTCOMES <= set(p.get("outcomes", []))
                   else "outcome is " + ", ".join(p["outcomes"]))
    return out


def main() -> None:
    cs = yaml.safe_load((DATA / "canvases.yaml").read_text())
    ps = yaml.safe_load((DATA / "plans.yaml").read_text())
    skills = canvas_skills(cs["canvases"])
    rec = RunRecorder("ch33", "reskill")
    ids = [f"RS-{i}" for i in range(1, 7)]
    rec.print("Reskilling plan checks (synthetic)")
    rec.print(f"{'plan':8}{'people':>7}" + "".join(
        f"{i[3:]:>3}" for i in ids) + "  passed")
    res = []
    for p in ps["plans"]:
        r = check(p, skills)
        n = sum(1 for v in r.values() if not v)
        rec.print(f"{p['id']:8}{p['people']:>7,}" + "".join(
            f"{'.' if not r[i] else 'x':>3}" for i in ids)
            + f"  {n} of 6")
        res.append((p, r))
    rec.print(". = pass, x = fail; reasons:")
    for p, r in res:
        for i in ids:
            if r[i]:
                rec.print(f"  {p['id']:8}{i}  {r[i][:44]}")
    rec.print("first readings (synthetic), as of 2028-04-30:")
    for p, _ in res:
        rec.print(f"  {p['id']:8}{p['reading'][:52]}")
    rec.note(results={p["id"]: r for p, r in res})
    print(rec.save())


if __name__ == "__main__":
    main()
