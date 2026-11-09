"""Chapter 19: the vendor due-diligence pack.

Book section "The due-diligence pack". Twelve checks, each
answered with evidence (data/vendors.yaml). A FAIL on a
gate check rejects the vendor whatever its score; every
FIX becomes a contract clause (clauses.py); a PASS needs
evidence a person at Hartwell has seen, not a slide.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch19_build_buy.diligence
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder

HERE = Path(__file__).resolve().parent


def assess(v: dict, gates: list[str]) -> dict:
    st = {c: a[0] for c, a in v["answers"].items()}
    failed = [c for c, s in st.items() if s == "FAIL"]
    gate_fail = [c for c in failed if c in gates]
    if gate_fail:
        verdict = "REJECT"
    elif failed:
        verdict = "HOLD"
    else:
        verdict = "PROCEED"
    return {"verdict": verdict, "gate_fail": gate_fail,
            "fail": failed,
            "fix": [c for c, s in st.items() if s == "FIX"],
            "pass": [c for c, s in st.items() if s == "PASS"]}


def main() -> None:
    cfg = yaml.safe_load((HERE / "data" / "vendors.yaml")
                         .read_text())
    rec = RunRecorder("ch19", "diligence")
    out = {}
    for key, v in cfg["vendors"].items():
        r = assess(v, cfg["gates"])
        out[key] = r
        rec.print(f"{v['name']}")
        rec.print(f"  {r['verdict']}: pass {len(r['pass'])}, "
                  f"fix {len(r['fix'])}, fail {len(r['fail'])}")
        if r["gate_fail"]:
            rec.print("  gate failed: "
                      + ", ".join(r["gate_fail"]))
        for c in r["fail"]:
            rec.print(f"    {c} {v['answers'][c][1]}")
        if r["verdict"] == "PROCEED":
            rec.print("  to contract: " + ", ".join(r["fix"]))
    rec.note(results=out)
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
