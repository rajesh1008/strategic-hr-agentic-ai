"""Hours, not heads: a business case the ledger is allowed to write.

Reads cases/<name>.yaml. Each benefit line points at a Claim-Status Ledger entry and the
calculator counts it three ways:

  vendor case    the claimed value, shown so the reader sees what was promised
  planning case  tested evidence at half weight, shadow at 0.8, production at full weight
  base case      production measurements only (the only column a board number may use)

Hours released minus oversight hours added is the capacity the case creates. It is shown
in hours and FTE-equivalents with headcount_change fixed by the case (Hartwell: 0). Money
appears only as licence and run cost against cash that actually stops.

Run:  HRAI_MODEL=no-model python -m chapters.ch04_claim_ledger.business_case hartwell-screening
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import yaml

from hrai.ledger import Ledger
from hrai.llm import REPO, RunRecorder

from . import deflection, rerun_claim

HERE = Path(__file__).resolve().parent


def ledger_for(case: dict) -> Ledger:
    if "ledger" in case:
        return Ledger.from_dict(case["ledger"])
    led = rerun_claim.build_ledger()
    led.claims["D-01"] = deflection.build_claim()
    return led


def tokens_per_action(run_dir: str) -> tuple[float, float, int]:
    """Mean input and output tokens per proposed action across every saved run."""
    tin = tout = acts = 0
    files = sorted(glob.glob(str(REPO / run_dir / "*.json")))
    for f in files:
        r = json.loads(Path(f).read_text())
        for c in r["calls"]:
            tin += c["response"]["usage"]["input_tokens"]
            tout += c["response"]["usage"]["output_tokens"]
        acts += sum(1 for e in r["events"] if "proposed" in e)
    return tin / acts, tout / acts, len(files)


def line_hours(b: dict, value: float, column: str) -> float:
    if b.get("value_is") == "hours_per_unit":
        return b["volume"] * value
    hours = b["volume"] * b["unit_minutes"] * value / 100 / 60
    if "return_rate" in b and value and column != "vendor":
        # measured columns carry the returns the vendor's figure leaves out
        hours -= b["volume"] * b["return_rate"] * b["return_extra_minutes"] / 60
    return hours


def evaluate(case: dict) -> dict:
    led = ledger_for(case)
    cols = {"vendor": 0.0, "planning": 0.0, "base": 0.0}
    lines = []
    for b in case["benefits"]:
        c = led[b["claim"]]
        vals = {"vendor": c.value, "planning": c.case_value("planning"), "base": c.case_value("base")}
        hrs = {k: line_hours(b, v, k) for k, v in vals.items()}
        for k in cols:
            cols[k] += hrs[k]
        lines.append((b["name"], c, vals, hrs))
    oversight = sum(o["hours"] for o in case["oversight"])
    costs = sum(x["amount"] for x in case["costs"])
    run = None
    if case.get("run_cost"):
        rc = case["run_cost"]
        tin, tout, nruns = tokens_per_action(rc["runs"])
        per = (tin * rc["rate_per_mtok"]["input"] + tout * rc["rate_per_mtok"]["output"]) / 1e6
        run = {"tin": tin, "tout": tout, "nruns": nruns, "per": per,
               "year": per * rc["actions_per_year"], "action": rc["action"]}
        costs += run["year"]
    blocked = [k for k in case.get("blockers", []) if led[k].contested]
    return {"led": led, "lines": lines, "cols": cols, "oversight": oversight,
            "costs": costs, "run": run, "blocked": blocked}


def main(name: str) -> None:
    case = yaml.safe_load((HERE / "cases" / f"{name}.yaml").read_text())
    r = evaluate(case)
    cur, fte = case["currency"], case["fte_hours"]
    rec = RunRecorder("ch04", f"business_case_{name.replace('-', '_')}")
    p = rec.print
    p(f"{case['organization']}: {case['title']}")
    p(f"{'benefit line':<34}{'status':<24}{'vendor':>8}{'plan':>8}{'base':>8}")
    for nm, c, vals, hrs in r["lines"]:
        p(f"{nm[:33]:<34}{c.effective_status().label[:23]:<24}"
          f"{hrs['vendor']:>8,.0f}{hrs['planning']:>8,.0f}{hrs['base']:>8,.0f}")
    p(f"{'oversight hours added':<58}{-r['oversight']:>8,}{-r['oversight']:>8,}{-r['oversight']:>8,}")
    net = {k: v - r["oversight"] for k, v in r["cols"].items()}
    p(f"{'net hours released':<58}{net['vendor']:>8,.0f}{net['planning']:>8,.0f}{net['base']:>8,.0f}")
    p(f"{'FTE-equivalent capacity':<58}{net['vendor'] / fte:>8.1f}{net['planning'] / fte:>8.1f}"
      f"{net['base'] / fte:>8.1f}")
    p(f"headcount change in every column: {case['headcount_change']}")
    plan = sum(x["hours"] for x in case["redeploy"])
    p(f"redeployment plan: {plan:,} hours named; planning case releases {net['planning']:,.0f}")
    if r["run"]:
        x = r["run"]
        p(f"run cost per action ({x['action']}): {x['tin']:.0f} input + {x['tout']:.0f} output "
          f"tokens, {cur}{x['per']:.4f} ({x['nruns']} runs)")
        p(f"run cost per year: {cur}{x['year']:,.0f}")
    left, cash = max(net["planning"], 0), 0.0
    for o in case["cash_offsets"]:   # released hours first replace spend that stops
        used = min(left, o["hours_cap"])
        cash += o["amount"] * used / o["hours_cap"]
        left -= used
    named = min(left, plan)          # the rest counts only where the work is named
    value = named * case["loaded_rate"]
    p(f"annual cost {cur}{r['costs']:,.0f}; cash that stops {cur}{cash:,.0f}; "
      f"named redeployment {named:,.0f} h worth {cur}{value:,.0f}")
    if r["blocked"]:
        p("decision: NO GO until resolved: " + ", ".join(
            f"{k} contested ({r['led'][k].statement})" for k in r["blocked"]))
    elif value + cash < r["costs"]:
        p("decision: the case does not pay on tested evidence; do not buy at this price")
    else:
        p("decision: proceed to shadow, then production measurement")
    rec.save()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "hartwell-screening")
