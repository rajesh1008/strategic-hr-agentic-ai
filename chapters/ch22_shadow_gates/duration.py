"""Chapter 22: how long shadow has to run, from the shadow
itself.

Book section "How long shadow runs, and what ends it". The
flags are fixed on day one, so a gap in flag rates between
age groups shows at once. What shadow has to wait for is the
outcome that would explain or condemn the gap: do the
flagged groups actually resign more? Leavers are few, and a
small group's leavers are fewer, so that number fills
slowly, and more slowly in a small lane.

For each week this prints, in the US lane, the share of each
group that has resigned so far, beside the flag rates. Then,
for each lane and group, the weeks needed to reach the
plan's floor of 30 resignations at the rate observed.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch22_shadow_gates.duration
"""
from __future__ import annotations

from hrai.llm import RunRecorder
from .shadow import OVER50, UNDER40, WEEKS, simulate

FLOOR = 30
GROUPS = {"50+": OVER50, "under 40": UNDER40}


def main() -> None:
    rec = RunRecorder("ch22", "duration")
    rows = simulate()
    us = [r for r in rows if r.p.lane == "US"]
    flag = {g: sum(r.v1 for r in us if r.p.band in b)
            / sum(r.p.band in b for r in us)
            for g, b in GROUPS.items()}
    rec.print(f"US flag rate on day 1: 50+ {flag['50+']:.3f};"
              f" under 40 {flag['under 40']:.3f}")
    rec.print("wk | resigned so far: 50+ | under 40")
    weekly = []
    for w in range(1, WEEKS + 1):
        s = {}
        for g, b in GROUPS.items():
            grp = [r for r in us if r.p.band in b]
            k = sum(r.outcome == "resigned" and r.week <= w
                    for r in grp)
            s[g] = (k, len(grp))
        rec.print(f"{w:>2} | {s['50+'][0]:>3} ({s['50+'][0] / s['50+'][1]:.3f})"
                  f" | {s['under 40'][0]:>3}"
                  f" ({s['under 40'][0] / s['under 40'][1]:.3f})")
        weekly.append(s)
    rec.print(f"weeks to {FLOOR} resignations, at the observed"
              " rate:")
    need = {}
    for lane in ("US", "DE"):
        lr = [r for r in rows if r.p.lane == lane]
        for g, b in GROUPS.items():
            k = sum(r.outcome == "resigned" for r in lr
                    if r.p.band in b)
            wk = FLOOR / (k / WEEKS) if k else float("inf")
            need[f"{lane} {g}"] = [k, round(wk)]
            rec.print(f"  {lane} {g:<8} {k:>3} in {WEEKS} weeks"
                      f" -> about {wk:.0f} weeks")
    rec.note(flag=flag, weekly=weekly, need=need)
    print(rec.save())


if __name__ == "__main__":
    main()
