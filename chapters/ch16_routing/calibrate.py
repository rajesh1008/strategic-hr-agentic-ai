"""Chapter 16: what the score said and what happened.

Book sections "What the score said and what happened" and
"Drawing the routing line". No model is called. The script
reads one recorded screening run, compares each stated
confidence with the answer a recruiter reaches under
guidance v1, and prints the reliability table. It then
fits a calibration map on one half of the applications
(odd candidate numbers) and checks the new routing line on
the other half (even numbers), so the line is never judged
on the cases that drew it.

Run:  python -m chapters.ch16_routing.calibrate \\
          ch16/screen_fast/<stamp>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from hrai import routing as rt
from hrai.llm import REPO, RunRecorder

from .flags import flags
from .make_data import load

EDGES = [0.0, 0.80, 0.85, 0.90, 0.95, 1.0]
SPLIT = [0.0, 0.85, 0.90, 0.93, 0.95, 1.0]
PILOT_AT = 0.85          # the pilot's confirm-lane setting
TARGET = 0.92            # lower bound for the confirm lane
REVIEW_AT = 0.80         # calibrated: below this, escalate


def run_record(run_id: str) -> dict:
    folder = REPO / "runs" / Path(run_id).parent
    stamp = Path(run_id).name
    path = next(folder.glob(f"{stamp}-*.json"))
    return json.loads(path.read_text())


def joined(record: dict) -> list[dict]:
    answers = record["events"][-1]["answers"]
    out = []
    for a in load():
        o = answers.get(a["candidate_id"])
        conf = o.get("confidence") if o else None
        ok = isinstance(conf, (int, float))
        out.append({**a, "said": o["meets"] if o else None,
                    "got": o or {},
                    "conf": float(conf) if ok else None,
                    "flags": flags(a["resume"],
                                   o.get("field_months")
                                   if o else None),
                    "half": "fit" if int(a["candidate_id"][-4:])
                    % 2 else "check"})
    return out


def lane(rows, rule) -> tuple[int, int, int]:
    """Share in the confirm lane, and how many were right."""
    inl = [r for r in rows if rule(r)]
    right = sum(r["meets"] for r in inl)
    return len(inl), right, len(rows)


def main(run_id: str) -> None:
    record = run_record(run_id)
    rows = joined(record)
    p = RunRecorder("ch16", "calibrate")
    p.print(f"Calibration of {run_id} ({record['model']})")
    use = [r for r in rows if r["said"] is not None
           and r["conf"] is not None]
    right = sum(r["said"] == r["meets"] for r in use)
    p.print(f"applications {len(rows)}; usable answers "
            f"{len(use)}; right {right} "
            f"({right / len(use):.1%})")
    pairs = [(r["conf"], r["said"] == r["meets"]) for r in use]
    p.print("stated       n   said  right  95% interval")
    table = rt.reliability(pairs, EDGES)
    for b in table:
        if not b["n"]:
            continue
        lo, hi = b["ci"]
        p.print(f"{b['lo']:.2f}-{b['hi']:.2f} {b['n']:4d}  "
                f"{b['said']:.2f}  {b['right']:.2f}  "
                f"{lo:.2f} to {hi:.2f}")
    p.print(f"ECE {rt.ece(pairs, EDGES):.3f}; "
            f"Brier {rt.brier(pairs):.3f}")
    p.print("by answer   stated       n   said  right")
    split = {}
    for name, d in (("meets", True), ("not meets", False)):
        split[name] = rt.reliability(
            [(r["conf"], r["said"] == r["meets"])
             for r in use if r["said"] is d], SPLIT)
        for b in split[name]:
            if b["n"]:
                p.print(f"{name:<11} {b['lo']:.2f}-{b['hi']:.2f}"
                        f" {b['n']:4d}  {b['said']:.2f}  "
                        f"{b['right']:.2f}")
    kinds: dict[str, list] = {}
    for r in use:
        kinds.setdefault(r["kind"], []).append(r)
    # the model applied the rule to its own extraction; where
    # did the wrong answers go wrong?
    def months(r):
        try:
            return int(r["got"].get("field_months"))
        except (TypeError, ValueError):
            return None
    agree = sum(r["said"] == (bool(r["got"].get("epa608"))
                and (months(r) or 0) >= 24) for r in use)
    p.print(f"verdict agrees with rule on own extraction: "
            f"{agree} of {len(use)}")
    wrong = [r for r in use if r["said"] != r["meets"]]
    cert = sum(bool(r["got"].get("epa608")) != r["epa608"]
               for r in wrong)
    mon = sum(months(r) is None or (months(r) >= 24)
              != (r["field_months"] >= 24) for r in wrong)
    p.print(f"wrong answers {len(wrong)}: certificate misread "
            f"{cert}; month count on wrong side of 24 {mon}")
    p.print("case type            n  right  mean stated")
    for k, rs in sorted(kinds.items()):
        ok = sum(r["said"] == r["meets"] for r in rs)
        m = sum(r["conf"] for r in rs) / len(rs)
        p.print(f"{k:<20}{len(rs):3d}  {ok / len(rs):.2f}"
                f"   {m:.2f}")
    # the pilot: "meets" at stated 0.85 or more is confirmed
    n, k, tot = lane(use, lambda r: r["said"]
                     and r["conf"] >= PILOT_AT)
    lo, hi = rt.wilson(k, n)
    p.print(f"PILOT line (stated >= {PILOT_AT}): confirm lane "
            f"{n} of {tot} ({n / tot:.1%}); right {k} "
            f"({k / n:.1%}, {lo:.2f} to {hi:.2f}); "
            f"wrong advances {n - k}")
    # the new line: fit on odd numbers, check on even
    allfit = rt.isotonic([(r["conf"], r["said"] == r["meets"])
                          for r in use if r["half"] == "fit"
                          and r["said"]])
    p.print("calibration map, all 'meets' answers (fit half):")
    for top, v in allfit:
        p.print(f"  stated up to {top:.2f} -> right {v:.2f}")
    # flagged "meets" answers go to review, whatever the
    # score, so the map is fitted on unflagged ones only
    n, k, tot = lane(use, lambda r: r["said"] and r["flags"])
    p.print(f"flagged 'meets' answers {n}; right {k}")
    n, k, tot = lane(use, lambda r: r["said"]
                     and not r["flags"])
    p.print(f"unflagged 'meets' answers {n}; right {k}")
    fit_rows = [r for r in use if r["half"] == "fit"
                and not r["flags"]]
    fit = rt.isotonic([(r["conf"], r["said"] == r["meets"])
                       for r in fit_rows if r["said"]])
    p.print("calibration map, unflagged 'meets' (fit half):")
    for top, v in fit:
        p.print(f"  stated up to {top:.2f} -> right {v:.2f}")
    for r in use:
        r["score"] = rt.calibrate(fit, r["conf"]) \
            if r["said"] and fit else None
    safe = rt.lowest_safe(
        [(r["score"], r["said"] == r["meets"])
         for r in fit_rows if r["said"]], TARGET)
    t, nfit, lofit = safe
    if t is None:
        p.print(f"no calibrated score is safe at {TARGET}: "
                f"the confirm lane stays closed")
        t = 1.01
    else:
        p.print(f"lowest safe calibrated score {t:.2f} "
                f"({nfit} fit-half cases, lower bound "
                f"{lofit:.3f})")
    line = rt.RoutingLine(
        step="A04", version="1.0", model=record["model"],
        complete_at=t, review_at=REVIEW_AT,
        fail_closed=["not_meets", "no_answer"],
        review_if=["OVERLAP", "NEAR", "NONFIELD",
                   "TRAINING", "NO_COUNT"],
        owner="Head of TA (Daniel Brooks)",
        review_by="quarterly")
    chk = [r for r in use if r["half"] == "check"]
    n, k, tot = lane(chk, lambda r: r["said"]
                     and not r["flags"] and r["score"] >= t)
    lo, hi = rt.wilson(k, n) if n else (0, 0)
    p.print(f"NEW line on check half: confirm lane {n} of "
            f"{tot} ({n / tot:.1%}); right {k}"
            + (f" ({k / n:.1%}, {lo:.2f} to {hi:.2f})"
               if n else ""))
    lanes: dict[str, int] = {}
    for r in rows:
        if r["said"] is None or r["conf"] is None:
            prop = "no_answer"
        else:
            prop = "meets" if r["said"] else "not_meets"
        c = rt.Case(r["candidate_id"], prop, r.get("score"),
                    flags=r["flags"])
        lanes[rt.route(c, line)[0]] = \
            lanes.get(rt.route(c, line)[0], 0) + 1
    p.print("routing, all 400: " + ", ".join(
        f"{k} {lanes.get(k, 0)}" for k in
        ("complete", "review", "escalate", "fail_closed")))
    p.note(source=run_id, table=table, split=split, fit=fit,
           line=line.__dict__, lanes=lanes, allfit=allfit,
           kinds={k: [len(v), sum(r["said"] == r["meets"]
                                  for r in v)]
                  for k, v in kinds.items()})
    path = p.save()
    print(f"saved {Path(path).relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1])
