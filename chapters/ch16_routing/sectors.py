"""Chapter 16: the routing line at three other employers.

Book section "Four organizations, four lines". No model is
called; the fixtures in data/sectors.yaml are synthetic.

  Crossfield  where to draw the line when review capacity
              runs out at peak (the line holds; capacity
              moves, not the threshold)
  Pennant     the same score means less when the applicant
              pool changes (base rates move precision)
  Lakemont    rules first; the score only orders a queue,
              and fails closed in both directions

Run:  HRAI_MODEL=no-model \\
      python -m chapters.ch16_routing.sectors
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai import routing as rt
from hrai.llm import REPO, RunRecorder

HERE = Path(__file__).resolve().parent


def crossfield(p, c: dict) -> None:
    p.print("Crossfield: peak-week line by threshold")
    p.print("line   auto share  right in auto  wrong/week"
            "  review hours")
    audit = c["audit"]
    total = sum(b["n"] for b in audit)
    for i in range(1, len(audit)):
        auto = audit[:i]
        n = sum(b["n"] for b in auto)
        right = sum(b["right"] for b in auto)
        share = n / total
        week = c["peak_week_matches"]
        wrong = round(week * share * (1 - right / n))
        hours = round(week * (1 - share)
                      * c["review_minutes"] / 60)
        lo, _ = rt.wilson(right, n)
        p.print(f"{audit[i - 1]['lo']:.2f}   {share:6.1%}"
                f"      {right / n:.3f} ({lo:.3f})"
                f"     {wrong:4d}       {hours:4d}")
    p.print(f"coordinator hours for review at peak: "
            f"{c['coordinator_review_hours']}")


def pennant(p, c: dict) -> None:
    met, nm = c["met"], c["not_met"]
    at = c["advance_at"]
    p_met = sum(v for k, v in met.items() if k >= at)
    p_nm = sum(v for k, v in nm.items() if k >= at)
    p.print(f"Pennant: auto-advance at fit score {at}; "
            f"P(score>=line | met) {p_met:.2f}, "
            f"| not met {p_nm:.2f}")
    p.print("month      applications  met  advanced  "
            "right  precision")
    for m, v in c["months"].items():
        a, s = v["applications"], v["met_share"]
        adv_right = a * s * p_met
        adv_wrong = a * (1 - s) * p_nm
        adv = adv_right + adv_wrong
        p.print(f"{m:<10} {a:6d}       {s:.2f}  {adv:6.0f}"
                f"   {adv_right:6.0f}   {adv_right / adv:.3f}")


def lakemont(p, c: dict) -> None:
    line = rt.RoutingLine(
        step="agency credential check", version="2",
        model="vendor matcher", complete_at=1.01,
        review_at=0.0,
        fail_closed=["lapsed", "residual"],
        owner="Credentialing coordinator")
    res = sum(c["residual"].values())
    p.print(f"Lakemont: {c['checks']} agency-nurse checks, "
            f"2027 Q1")
    p.print(f"  cleared by rule (license and name match, "
            f"board active): {c['exact_active']}")
    p.print(f"  stopped by rule (board lapsed), to the "
            f"coordinator: {c['exact_lapsed']}")
    p.print(f"  residual, to the coordinator whatever the "
            f"score: {res} " + str(c["residual"]))
    for prop, score in (("residual", 0.97), ("lapsed", 0.99)):
        lane, why = rt.route(rt.Case("x", prop, score), line)
        p.print(f"  route({prop}, {score}) -> {lane} ({why})")
    p.print(f"  residual cases the vendor scored 0.90 or more "
            f"that were wrong: {c['vendor_said_match_wrong']}")


def main() -> None:
    cfg = yaml.safe_load((HERE / "data" / "sectors.yaml")
                         .read_text())
    p = RunRecorder("ch16", "sectors")
    crossfield(p, cfg["crossfield"])
    pennant(p, cfg["pennant"])
    lakemont(p, cfg["lakemont"])
    path = p.save()
    print(f"saved {Path(path).relative_to(REPO)}")


if __name__ == "__main__":
    main()
