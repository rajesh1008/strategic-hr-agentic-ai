"""Chapter 19: the contract clauses that matter.

Book section "Twelve clauses". Each clause C-nn answers
due-diligence check DD-nn. The checker reads a structured
term sheet (data/terms.yaml), not the prose of the contract:
counsel keeps the term sheet in step with the text, and the
checker keeps the term sheet honest about the numbers.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch19_build_buy.clauses
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder

HERE = Path(__file__).resolve().parent
NEED = {"inputs", "reason", "version", "time"}

RULES = {
    "C-01": ("claims are warranties, measured on our records",
             lambda t: t["claims_as_warranty"]),
    "C-02": ("data for an impact table per version",
             lambda t: t["impact_data_per_version"]),
    "C-03": ("per-decision record: inputs, reason, version",
             lambda t: NEED <= set(t["fields"])),
    "C-04": ("decision records exported daily to our trail",
             lambda t: t["daily_export"]),
    "C-05": ("30 days' notice and a re-test before go-live",
             lambda t: t["notice_days"] >= 30
             and t["retest_before_live"]),
    "C-06": ("we can switch a feature off in 15 minutes",
             lambda t: t["switch_off_minutes"] <= 15),
    "C-07": ("new AI features ship switched off",
             lambda t: t["default_off"]),
    "C-08": ("AI Act roles named; instructions for use",
             lambda t: t["roles_named"]
             and t["instructions_for_use"]),
    "C-09": ("processor terms; every sub-processor listed",
             lambda t: t["processor_terms"]
             and t["subprocessors_listed"]
             and t["model_host_listed"]),
    "C-10": ("no training on our data or decisions",
             lambda t: t["training_on_customer_data"]
             == "none"),
    "C-11": ("exit: everything in 30 days, no fee",
             lambda t: t["export_days"] <= 30
             and t["derived_data"] and t["logs"]
             and not t["fee"]),
    "C-12": ("writes only through our adapter",
             lambda t: t["writes_via_customer_adapter"]),
}


def check(doc: dict) -> dict:
    out = {}
    for cid, (_, ok) in RULES.items():
        if cid not in doc:
            out[cid] = "missing"
        else:
            out[cid] = "ok" if ok(doc[cid]) else "short"
    return out


def main() -> None:
    cfg = yaml.safe_load((HERE / "data" / "terms.yaml")
                         .read_text())
    rec = RunRecorder("ch19", "clauses")
    res = {}
    for key, doc in cfg["documents"].items():
        r = check(doc)
        res[key] = r
        ok = sum(v == "ok" for v in r.values())
        rec.print(f"{doc['title']}: {ok} of {len(RULES)} ok")
        for cid, v in r.items():
            if v != "ok":
                rec.print(f"  {cid} {v:<7} {RULES[cid][0]}")
    rec.note(results=res)
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
