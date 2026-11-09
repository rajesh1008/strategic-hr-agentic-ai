"""Chapter 19: the vendor-evaluation harness.

Book section "The harness: every candidate on the same
records". Any candidate for a screening step, whether a
vendor's add-on, a small model Hartwell trains or a large
model with a prompt, is scored on the same 1,200 synthetic
applications with the same measures:

  sel     how many it recommends
  posted  agreement with the posted requirements
  history agreement with the old Q4 2026 outcomes
  worst   lowest impact ratio by age, and by sex and age
  flags   the Chapter 7 flags on those rows
  GAP     how many answers gave GAP as the reason ("-"
          where the run kept no reasons)
  meets   of applicants who meet the posted requirements,
          how many it recommends, gap up to six months and
          gap over six months

Model outputs are read from committed run records; the
small models are recomputed (history.py, fixed seed).
No model is called here.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch19_build_buy.harness STAMP [STAMP ...]
"""
from __future__ import annotations

import json
import sys

from hrai.llm import REPO, RunRecorder

from chapters.ch07_adverse_impact import impact as ai
from chapters.ch07_adverse_impact.audit import joined
from chapters.ch07_adverse_impact.make_data import load

from .history import VERSIONS, fit_all, old_outcome, posted
from .history import split

S2 = "ch07/screen_S2/20261109T131533Z"


def recorded(run: str) -> tuple[str, dict, dict]:
    path = next((REPO / "runs").glob(f"{run}-*.json"))
    r = json.loads(path.read_text())
    ev = r["events"][0]
    return r["model"], ev["recommendations"], \
        ev.get("reasons")


def worst(recs, sel, group) -> tuple[str, list[str]]:
    rows, _ = ai.table(recs, group, sel)
    low = min((x for x in rows if x.ratio is not None),
              key=lambda x: x.ratio)
    return f"{low.group} {low.ratio:.2f}", low.flags


def card(rec, name, said, reasons, new, recs) -> dict:
    sel = lambda r: said.get(r["candidate_id"]) in (  # noqa
        True, "Y")
    yes = sum(sel(r) for r in recs)
    agree = sum(sel(a) == posted(a) for a in new)
    hist = sum(sel(a) == old_outcome(a) for a in new)
    w_age, f_age = worst(recs, sel, lambda r: r["age"])
    w_sa, f_sa = worst(recs, sel,
                       ai.intersect("sex_", "age"))
    gap = "-" if reasons is None else sum(
        1 for v in reasons.values() if v == "GAP")
    rec.print(f"{name}")
    rec.print(f"  sel {yes}  posted {agree}/{len(new)}"
              f"  history {hist}/{len(new)}  GAP {gap}")
    m_short = [a for a in new if posted(a)
               and int(a["longest_gap_months"]) <= 6]
    m_long = [a for a in new if posted(a)
              and int(a["longest_gap_months"]) > 6]
    k_s = sum(sel(a) for a in m_short)
    k_l = sum(sel(a) for a in m_long)
    rec.print(f"  meets: gap <=6 {k_s}/{len(m_short)}, "
              f"gap >6 {k_l}/{len(m_long)}")
    rec.print(f"  worst age {w_age} {' '.join(f_age)}")
    rec.print(f"  worst sex & age {w_sa} {' '.join(f_sa)}")
    return {"name": name, "sel": yes, "posted": agree,
            "history": hist, "gap": gap,
            "meets_short": [k_s, len(m_short)],
            "meets_long": [k_l, len(m_long)],
            "worst_age": w_age, "flags_age": f_age,
            "worst_sex_age": w_sa, "flags_sex_age": f_sa}


def main(stamps: list[str]) -> None:
    hist, new = split()
    recs = joined(new, load("hartwell-q4-2026-self-id.csv"))
    rec = RunRecorder("ch19", "harness")
    rec.print(f"harness: {len(new)} applications, "
              f"self-ID joined after the step")
    cards = []
    rule = {a["candidate_id"]: posted(a) for a in new}
    cards.append(card(rec, "R0 posted rule (code)", rule,
                      None, new, recs))
    for v, (w, cols, said) in fit_all().items():
        cards.append(card(rec, f"{v} small model, "
                          f"{VERSIONS[v][0]}", said, None,
                          new, recs))
    m, said, rs = recorded(S2)
    cards.append(card(rec, f"S2 retrieve rule, {m} (ch07)",
                      said, rs, new, recs))
    runs = {}
    for s in stamps:
        m, said, rs = recorded(f"ch19/fewshot/{s}")
        runs[s] = said
        cards.append(card(rec, f"F few-shot history, {m} "
                          f"{s}", said, rs, new, recs))
    if len(runs) >= 2:
        a, b = list(runs.values())[:2]
        same = sum(a.get(k) == b.get(k) for k in a)
        rec.print(f"two few-shot runs agree on {same} "
                  f"of {len(a)}")
    rec.note(cards=cards)
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1:])
