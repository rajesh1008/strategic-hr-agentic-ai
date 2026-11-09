"""What an answer costs, from the gateway logs in the recorded
test-set runs (book section "What a run costs"). No model is
called: the numbers are read from run records.

Cost uses the illustrative contract rates in rates.yaml. The
monthly figure uses an illustrative volume, printed as such.

Run: HRAI_MODEL=no-model python -m chapters.ch17_surface_brain.cost
(writes runs/ch17/cost/...)
"""
from __future__ import annotations

import json
from collections import defaultdict

from hrai.llm import REPO, RunRecorder

MONTHLY_QUESTIONS = 30_000  # illustrative volume, not a forecast


def logs():
    for p in sorted((REPO / "runs" / "ch17").glob("eval_*/*.json")):
        r = json.loads(p.read_text())
        org, design = p.parent.name.split("_", 2)[1:]
        for ev in r["events"]:
            for e in ev.get("gateway_log", []):
                if e.get("status") == "ok":
                    yield org, design, e


def main() -> None:
    rec = RunRecorder("ch17", "cost")
    rows = defaultdict(list)
    for org, design, e in logs():
        rows[(org, design, e["model"].split("-")[1])].append(e)
    rec.print("Cost per answer from gateway logs (illustrative rates)")
    rec.print(f"{'org':<12}{'design':<11}{'model':<7}{'calls':>5}"
              f"{'in':>6}{'out':>5}{'$/1,000':>9}")
    for (org, design, m), es in sorted(rows.items()):
        n = len(es)
        tin = sum(e["tokens_in"] for e in es) / n
        tout = sum(e["tokens_out"] for e in es) / n
        per = sum(e["cost_usd"] for e in es) / n
        rec.print(f"{org:<12}{design:<11}{m:<7}{n:>5}{tin:>6.0f}"
                  f"{tout:>5.0f}{per * 1000:>9.2f}")
    h = rows.get(("hartwell", "entitled", "haiku"))
    if h:
        per = sum(e["cost_usd"] for e in h) / len(h)
        rec.print(f"Hartwell entitled on Haiku at an illustrative "
                  f"{MONTHLY_QUESTIONS:,}")
        rec.print(f"questions a month: ${per * MONTHLY_QUESTIONS:,.0f}"
                  f" in model charges")
    rec.note(groups={"/".join(k): len(v) for k, v in rows.items()})
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
