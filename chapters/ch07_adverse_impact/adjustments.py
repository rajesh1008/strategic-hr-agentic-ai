"""Chapter 7: the reasonable-adjustments test (no model).

Book section "Disability, adjustments and the AI step". Six
checks on how one assessment step is set up, read from the
step's own configuration, then the outcome table: pass rates
by disability status and by whether an adjustment was made.

Run:  HRAI_MODEL=no-model python -m chapters.ch07_adverse_impact.adjustments
"""
from __future__ import annotations

import statistics
from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder

from . import impact as ai
from .make_data import load

HERE = Path(__file__).resolve().parent
SCORED = {"face", "voice", "speech pace", "typing speed",
          "emotion", "eye contact"}


def checks(step: dict) -> list[tuple[str, bool, str]]:
    """The six checks. Each returns (name, passed, why)."""
    n, r = step["notice"], step["request"]
    alts = step["alternatives"]
    inf = set(step["scores"]) & SCORED
    return [
        ("R1 notice", n["before_step"] and n["says_what"],
         "says what is measured, how and for how long"),
        ("R2 route", r["on_invitation"]
         and not r["evidence_to_ask"],
         "ask on the invitation; no proof needed to ask"),
        ("R3 alternatives", {"time", "format", "person"}
         <= set(alts), "more time, another format, a person"),
        ("R4 decision", r["decider"] != "vendor"
         and r["days"] <= 2,
         "a named person decides within 2 business days"),
        ("R5 no inference", not inf or step.get("job_need"),
         "scores " + ", ".join(sorted(inf))
         if inf else "no face, voice or pace scoring"),
        ("R6 monitoring", step["monitor_quarterly"],
         "pass rates by disability and adjustment"),
    ]


def main() -> None:
    rec = RunRecorder("ch07", "adjustments")
    cfg = yaml.safe_load((HERE / "lakemont_steps.yaml")
                         .read_text())
    rows = load("lakemont-rn.csv")
    for version, step in cfg["versions"].items():
        res = checks(step)
        ok = sum(p for _, p, _ in res)
        rec.print(f"== {version}: {ok} of 6 checks pass")
        for name, passed, why in res:
            rec.print(f"{name:<17}{'pass' if passed else 'FAIL':<6}"
                      f"{why}")
        s = [r for r in rows if r["period"] == step["period"]]
        dis = [r for r in s if r["disability"] == "Y"]
        asked = [r for r in dis if r["asked"] == "Y"]
        days = [int(r["days_to_decide"]) for r in asked]
        rec.print(f"applicants {len(s)}; disabled {len(dis)}; "
                  f"asked {len(asked)}; adjusted "
                  f"{sum(r['adjusted'] == 'Y' for r in dis)}; "
                  f"median days {statistics.median(days):g}")
        g = lambda r: {"Y": "disabled", "N": "not disabled"}.get(
            r["disability"], "declined")  # noqa: E731
        t, miss = ai.table(s, g, lambda r: r["passed"] == "Y")
        for line in ai.render(t, "-- pass rate", miss):
            rec.print(line)
        a = lambda r: ("adjusted" if r["adjusted"] == "Y" else
                       "not adjusted") if r["disability"] == "Y" \
            else "declined"  # noqa: E731
        t, _ = ai.table(dis, a, lambda r: r["passed"] == "Y")
        for line in ai.render(t, "-- disabled applicants"):
            rec.print(line)
        rec.print()
    print(f"saved {Path(rec.save()).relative_to(REPO)}")


if __name__ == "__main__":
    main()
