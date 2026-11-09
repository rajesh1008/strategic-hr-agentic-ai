"""Chapter 21: Hartwell's audit, one version at a time.

Book sections "Hartwell's audit, one version at a time",
"Errors, not only selections" and "When protected data is
missing". The step is A04 (Keep at recommend, Chapter 11).
A version is the model plus its configuration plus the
screening guidance: change any one and the tables are new.

The answers come from Chapter 16's recorded runs on the same
400 double-read applications, read here unchanged:
  Haiku fast   the pilot's configuration (two runs)
  Sonnet 5.5   asked in words, no thinking
  Haiku work   routing line A04 v1.0's configuration
"rule" is the answer the double read reached under guidance
v1, so its table is the table of the posted requirements.

Self-ID (selfid.py) is joined by candidate ID after the
step. No model is called.

Run:  HRAI_MODEL=no-model python -m chapters.ch21_fairness.versions
"""
from __future__ import annotations

import json

from hrai.llm import REPO, RunRecorder

from chapters.ch07_adverse_impact import impact as ai
from chapters.ch16_routing.make_data import load

from . import fairness as fx
from .selfid import read

RUNS = {
    "Haiku fast 1": "ch16/screen_fast/20261109T141356Z",
    "Haiku fast 2": "ch16/screen_fast/20261109T142200Z",
    "Sonnet 5.5": "ch16/screen_fast/20261109T141812Z",
    "Haiku work": "ch16/screen_work/20261109T141356Z",
}
WORDS = {"sex": {"F": "women", "M": "men"},
         "age_40_plus": {"Y": "40+", "N": "under 40"},
         "veteran": {"Y": "veteran", "N": "not veteran"},
         "disability": {"Y": "disabled", "N": "not disabled"}}
AXES = [("sex", "sex"), ("age", "age_40_plus"),
        ("race", "race_ethnicity"), ("veteran", "veteran")]


def answers(run_id: str) -> dict:
    folder = REPO / "runs" / run_id.rsplit("/", 1)[0]
    stamp = run_id.rsplit("/", 1)[1]
    path = next(folder.glob(f"{stamp}-*.json"))
    rec = json.loads(path.read_text())
    return rec["events"][-1]["answers"]


def records(said: dict | None) -> list[dict]:
    sid = {r["candidate_id"]: r for r in read()}
    out = []
    for a in load():
        s = sid[a["candidate_id"]]
        r = {k: WORDS.get(k, {}).get(v, v) for k, v in s.items()}
        r["meets"], r["kind"] = a["meets"], a["kind"]
        o = None if said is None else said.get(a["candidate_id"])
        r["said"] = a["meets"] if said is None else \
            bool(o and o["meets"])
        out.append(r)
    return out


def lowest(rows) -> str:
    cmp = [r for r in rows if r.ratio is not None
           and "REF" not in r.flags]
    if not cmp:
        return "no group of 30 or more to compare"
    r = min(cmp, key=lambda r: r.ratio)
    name = ai.SHORT.get(r.group, r.group)
    fl = " ".join(f for f in r.flags if f != "1P")
    return f"{name} {r.ratio:.2f}" + (f" {fl}" if fl else "")


def main() -> None:
    rec = RunRecorder("ch21", "versions")
    rec.print("A04 fairness by version: 400 applications,")
    rec.print("self-ID joined by candidate ID after the step")
    base = records(None)
    gone = sum(r["sex"] == "declined" for r in base)
    blank = sum(r["race_ethnicity"] == "declined"
                for r in base) - gone
    rec.print(f"self-ID declined {gone}; race left blank {blank}")
    summary = {}
    for name, run_id in [("rule", None)] + list(RUNS.items()):
        said = None if run_id is None else answers(run_id)
        rs = records(said)
        right = sum(r["said"] == r["meets"] for r in rs)
        rec.print("")
        rec.print(f"== {name}" + (f" ({run_id})" if run_id else
                                  " (posted requirements)"))
        rec.print(f"right {right}/400; says meets "
                  f"{sum(r['said'] for r in rs)}")
        rec.print("selection, lowest impact ratio by axis:")
        row = {}
        for label, key in AXES + [("sex & age", None)]:
            g = ai.intersect("sex", "age_40_plus") if key is None \
                else (lambda r, k=key: r[k])
            t, _, small = fx.readable(rs, g, lambda r: r["said"])
            row[label] = lowest(t)
            rec.print(f"  {label:<10}{row[label]}")
            if small and name == "rule":
                words = ", ".join(f"{ai.SHORT.get(s, s)} {k}"
                                  for s, k in small)
                rec.print(" " * 12 + f"too few to read: {words}"
                          if len(words) < 36 else
                          " " * 12 + "too few to read: "
                          + ", ".join(f"{ai.SHORT.get(s, s)} {k}"
                                      for s, k in small[:2]) + ",")
                if len(words) >= 36:
                    rec.print(" " * 14 + ", ".join(
                        f"{ai.SHORT.get(s, s)} {k}"
                        for s, k in small[2:]))
        qual = sum(r["meets"] for r in rs)
        wrong = sum(r["meets"] and not r["said"] for r in rs)
        rec.print(f"met the bar {qual}; screened out anyway {wrong}")
        errs = {}
        if wrong:
            for label, key in AXES:
                t, miss = fx.errors(rs, lambda r, k=key: r[k],
                                    lambda r: r["meets"],
                                    lambda r: r["said"])
                errs[label] = [vars(e) for e in t]
                for line in fx.render_errors(
                        t, f"-- wrongly screened out, {label}"):
                    rec.print(line)
            n, k = fx.declined(rs, lambda r: r["sex"],
                               lambda r: r["meets"],
                               lambda r: r["said"])
            rec.print(f"declined self-ID: {n} met the bar, "
                      f"{k} screened out ({k / n:.2f})")
        summary[name] = {"run": run_id, "right": right,
                         "lowest": row, "wrong": wrong,
                         "errors": errs}
    rec.print("")
    rec.print("bounds, posted requirements, under 40 vs 40+:")
    seen, lo, hi = fx.bounds(base, lambda r: r["age_40_plus"],
                             lambda r: r["said"], "under 40", "40+")
    rec.print(f"  as reported {seen:.2f}; decliners all on one "
              f"side {lo:.2f} to {hi:.2f}")
    rec.note(summary=summary)
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
