"""Chapter 21: the fairness test record, and its checks.

Book section "The fairness test record". One record per
step, per version, per period. It is written before the data
is read (the plan half) and completed after (the result
half). The checks say whether a record could be shown to a
regulator, a tribunal or an opposing expert without the
first question ending it.

  FT-1 version   step, model, configuration, guidance named
  FT-2 people    population, period, counts, not reported
  FT-3 groups    axes and intersections per lane; reference
                 group must have 30 or more
  FT-4 fixed     primary comparisons written before the data;
                 a correction named for the rest
  FT-5 small     a minimum cell rule, and what small cells get
  FT-6 proxies   inputs scanned, and counterfactual pairs
                 with a retest noise floor
  FT-7 errors    wrong screen-outs among people who met the
                 bar, on a yardstick the vendor did not set
  FT-8 lanes     each jurisdiction's test and reading, with
                 counsel's review
  FT-9 decision  decision, owner, date and what reruns it

Run:  HRAI_MODEL=no-model python -m chapters.ch21_fairness.record
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder

HERE = Path(__file__).resolve().parent / "data" / "records"


def check(r: dict) -> dict[str, str]:
    """Each check returns 'ok' or the reason it fails."""
    v, pop = r.get("version") or {}, r.get("population") or {}
    g, plan = r.get("groups") or {}, r.get("plan") or {}
    out = {}
    out["FT-1"] = "ok" if all(v.get(k) for k in (
        "step", "model", "configuration", "guidance")) \
        else "version not fully named"
    out["FT-2"] = "ok" if all(k in pop for k in (
        "who", "period", "n", "not_reported")) \
        else "population, period or not-reported count missing"
    ref_min = g.get("reference_min_n", 0)
    out["FT-3"] = "ok" if g.get("axes") and g.get(
        "intersections") and ref_min >= 30 \
        else "no intersections, or reference group may be tiny"
    out["FT-4"] = "ok" if plan.get("fixed_before_data") and \
        plan.get("primary") and plan.get("correction") \
        else "comparisons not fixed before the data"
    out["FT-5"] = "ok" if plan.get("min_cell") and \
        plan.get("small_cells") else "no minimum cell rule"
    px = r.get("proxies") or {}
    out["FT-6"] = "ok" if px.get("inputs_scanned") and \
        px.get("counterfactual") and px.get("retest_floor") \
        else "no proxy scan or no counterfactual with retest"
    er = r.get("errors") or {}
    out["FT-7"] = "ok" if er.get("yardstick") and \
        er.get("yardstick_owner") not in (None, "vendor") \
        else "no error test on an independent yardstick"
    lanes = r.get("lanes") or []
    out["FT-8"] = "ok" if lanes and all(
        x.get("test") and x.get("counsel_reviewed")
        for x in lanes) else "lanes missing or not reviewed"
    d = r.get("decision") or {}
    out["FT-9"] = "ok" if all(d.get(k) for k in (
        "outcome", "owner", "date", "rerun_on")) \
        else "no decision, owner, date or rerun trigger"
    return out


def main() -> None:
    rec = RunRecorder("ch21", "record")
    for path in sorted(HERE.glob("*.yaml")):
        r = yaml.safe_load(path.read_text())
        res = check(r)
        ok = sum(x == "ok" for x in res.values())
        rec.print(f"{r['title']}")
        rec.print(f"  {ok} of {len(res)} checks ok")
        for k, x in res.items():
            if x != "ok":
                rec.print(f"  {k} {x}")
        rec.note(record=path.name, result=res)
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
