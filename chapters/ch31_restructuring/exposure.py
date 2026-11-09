"""Chapter 31: the task-exposure table.

Book section "Task exposure is not absorption". For each
role: the share of hours an exposure score calls exposed,
the vendor reading (exposed x a flat rate), and the share
measured as absorbed, weighted by claim status, net of the
review hours that stay with people.
"""
from __future__ import annotations

from hrai.llm import RunRecorder

from .model import absorbed, exposed, load

FULL = {"Claimed": 0.0, "Tested": 1.0, "Shadow": 1.0,
        "Production": 1.0}
PROD = {"Claimed": 0.0, "Tested": 0.0, "Shadow": 0.0,
        "Production": 1.0}


def readings(cfg: dict) -> dict[str, dict]:
    """Four readings of the same task table, per role."""
    out, rv = {}, cfg["review_ratio"]
    for role, tasks in cfg["roles"].items():
        e = exposed(tasks)
        out[role] = {
            "exposed": e,
            "vendor": e * cfg["vendor_rate"],
            "base": absorbed(tasks, PROD) * (1 - rv),
            "plan": absorbed(tasks, cfg["weights"]) * (1 - rv),
            "high": absorbed(tasks, FULL) * (1 - rv)}
    return out


def main() -> None:
    cfg = load()
    rec = RunRecorder("ch31", "exposure")
    p = rec.print
    p("Task-exposure table (synthetic), share of hours")
    p(f"{'role':<15}{'exposed':>8}{'vendor':>8}"
      f"{'base':>7}{'plan':>7}{'high':>7}")
    rows = readings(cfg)
    for role, r in rows.items():
        p(f"{role:<15}{r['exposed']:>8.0%}"
          f"{r['vendor']:>8.0%}{r['base']:>7.1%}"
          f"{r['plan']:>7.1%}{r['high']:>7.1%}")
    p("vendor = exposed x 0.60, no review hours")
    p("base = Production rates only; plan = ch04 weights;")
    p("high = every Tested and Shadow rate holds; all net")
    p(f"of review hours ({cfg['review_ratio']:.0%} of "
      "absorbed hours)")
    for role, tasks in cfg["roles"].items():
        p("")
        p(f"{role}: task, share, side, rate, status")
        for t in tasks:
            mark = "E" if t["exposed"] else "-"
            p(f"  {mark} {t['task']:<29}"
              f"{t['share']:>5.0%} {t['side']:<8}"
              f"{t['rate']:>4.0%} {t['status']}")
    rec.note(readings=rows)
    print(rec.save())


if __name__ == "__main__":
    main()
