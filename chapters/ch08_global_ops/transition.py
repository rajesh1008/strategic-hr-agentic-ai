"""Chapter 8: what happens to tier 1 when an agent absorbs work.

The plan sizes the work the agent absorbs from a measured rate,
keeps review and human-route seats, and reaches the new size by
not backfilling leavers (the glide path). The vendor draft cuts
the whole claimed amount in one quarter. Both are computed the
same way so the difference is the cut policy and the evidence,
not the arithmetic. People are counted as seats; no model.

Run: HRAI_MODEL=no-model python -m chapters.ch08_global_ops.transition
(writes runs/ch08/transition/...)
"""
from __future__ import annotations

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


def target(cfg: dict, case: dict) -> dict:
    absorbed = round(cfg["seats"] * cfg["scope_share"]
                     * case["rate"])
    review = (round(absorbed * cfg["review_ratio"])
              if case.get("review", True) else 0)
    return {"absorbed": absorbed, "review": review,
            "target": cfg["seats"] - absorbed + review}


def quarters(start: str, n: int) -> list[str]:
    y, q = int(start[:4]), int(start[-1])
    out = []
    for _ in range(n):
        out.append(f"{y}Q{q}")
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)
    return out


def schedule(cfg: dict, case: dict, n: int = 4) -> list[dict]:
    """Quarter by quarter: leavers, backfills, exits forced."""
    t = target(cfg, case)["target"]
    rate = cfg["annual_attrition"] / 4
    seats, rows = cfg["seats"], []
    for i, q in enumerate(quarters(cfg["start"], n)):
        leavers = round(seats * rate)
        if case["cut"] == "one quarter" and i == 0:
            end = t
        else:
            end = max(t, seats - leavers)
        forced = max(0, seats - leavers - end)
        backfill = max(0, end - (seats - leavers))
        rows.append({"q": q, "start": seats, "leavers": leavers,
                     "backfill": backfill, "forced": forced,
                     "end": end})
        seats = end
    return rows


def load() -> dict:
    return yaml.safe_load((HERE / "transition.yaml").read_text())


def main() -> None:
    from hrai.llm import RunRecorder
    cfg = load()
    rec = RunRecorder("ch08", "transition")
    rec.print(f"Meridian tier 1, {cfg['seats']} seats, "
              f"attrition {cfg['annual_attrition']:.0%} a year"
              " (synthetic)")
    for case in cfg["cases"]:
        t = target(cfg, case)
        rec.print("")
        rec.print(f"{case['name']}: rate {case['rate']:.1%} "
                  f"[{case['status']}]")
        rec.print(f"  absorbed {t['absorbed']}, review seats "
                  f"{t['review']}, new size {t['target']}")
        rec.print("  quarter start leavers backfill forced end")
        rows = schedule(cfg, case)
        for r in rows:
            rec.print(f"  {r['q']}  {r['start']:>5} "
                      f"{r['leavers']:>7} {r['backfill']:>8} "
                      f"{r['forced']:>6} {r['end']:>4}")
        forced = sum(r["forced"] for r in rows)
        rec.print(f"  exits not by choice: {forced}")
        rec.note(case=case["name"], **t, forced=forced,
                 rows=rows)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
