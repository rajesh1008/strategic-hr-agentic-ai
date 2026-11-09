"""Chapter 28: four sector cases, four ways to read a cause.

Book section "Four organizations, four causal questions".
All data synthetic, seeded, no model API.

  Lakemont Health   nurse residency for first-year RNs,
                    started at two of four hospitals with the
                    2027 cohort and at the other two in 2028:
                    before-and-after against difference-in-
                    differences, with the pre-trend check
  Pennant Stores    "stores that lose a manager lose sales":
                    the sales path in the quarters before and
                    after a store-manager departure
  Hartwell Energy   when new rotation-crew hires leave, by
    Services Canada rotation, before and after the pay
                    cut-off fix (Chapter 10)
  Quayfen           the Hartwell seat plan (Chapter 8) under
                    lower adviser attrition: the forecast is a
                    planning input, not a list of people

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch28_people_analytics.sectors
"""
from __future__ import annotations

import math

import numpy as np

from hrai.llm import RunRecorder
from chapters.ch08_global_ops import transition

LAKEMONT = {  # hospital: (wave, first-year RNs a year, base)
    "Duluth": (1, 120, 0.27), "Rochester": (1, 110, 0.25),
    "Minneapolis": (2, 130, 0.28), "St. Paul": (2, 100, 0.26)}
YEARS = (2025, 2026, 2027)
TREND = {2025: 0.0, 2026: -0.01, 2027: -0.04}  # labor market
RESIDENCY = -0.06                               # set, not measured


def lakemont(rec, rng) -> dict:
    left = {}
    for h, (wave, n, base) in LAKEMONT.items():
        for y in YEARS:
            p = base + TREND[y] + (RESIDENCY if wave == 1
                                   and y == 2027 else 0)
            left[(h, y)] = (int(rng.binomial(n, p)), n)
    rec.print("=== Lakemont: first-year RNs leaving within 12"
              " months")
    rec.print("hospital     wave   2025   2026   2027")
    for h, (wave, _, _) in LAKEMONT.items():
        rec.print(f"{h:<12} {wave:>4} " + " ".join(
            f"{left[(h, y)][0] / left[(h, y)][1]:>6.1%}"
            for y in YEARS))

    def pooled(wave, y):
        k = sum(left[(h, y)][0] for h, v in LAKEMONT.items()
                if v[0] == wave)
        n = sum(left[(h, y)][1] for h, v in LAKEMONT.items()
                if v[0] == wave)
        return k / n, n
    (a26, na), (a27, _) = pooled(1, 2026), pooled(1, 2027)
    (b26, nb), (b27, _) = pooled(2, 2026), pooled(2, 2027)
    (a25, _), (b25, _) = pooled(1, 2025), pooled(2, 2025)
    before_after = a27 - a26
    did = (a27 - a26) - (b27 - b26)
    se = math.sqrt(sum(p * (1 - p) / n for p, n in
                       ((a26, na), (a27, na), (b26, nb),
                        (b27, nb))))
    pre = (a26 - a25) - (b26 - b25)
    rec.print(f"before and after, wave 1: {before_after:+.1%}")
    rec.print(f"difference-in-differences: {did:+.1%}")
    rec.print(f"  (95% interval {did - 1.96 * se:+.1%} to"
              f" {did + 1.96 * se:+.1%})")
    rec.print(f"pre-trend check, 2025 to 2026: {pre:+.1%}")
    rec.print(f"set in the simulation: {RESIDENCY:+.1%}")
    return {"rates": {f"{h}|{y}": v for (h, y), v in left.items()},
            "before_after": before_after, "did": did, "se": se,
            "pre": pre}


def pennant(rec, rng) -> dict:
    stores, quarters = 310, 12          # 2025Q1 to 2027Q4
    sales = np.zeros((stores, quarters))
    left = []
    for s in range(stores):
        x, gone = 100.0, False
        for q in range(quarters):
            x += rng.normal(0, 2.0)
            sales[s, q] = x
            if q >= 4 and not gone:
                fall = sales[s, q - 1] - sales[s, q - 3]
                # bonus missed after two falling quarters
                p = 0.012 + (0.06 if fall < -3 else 0.0)
                if rng.random() < p:
                    left.append((s, q))
                    gone = True
                    x -= 1.0             # small real dip
    rec.print("=== Pennant: sales index around a store-manager"
              " exit")
    rec.print(f"stores {stores}, departures {len(left)}"
              " (2026 to 2027)")
    rows = {}
    for k in range(-3, 3):
        d = [sales[s, q + k] - sales[s, q - 3] for s, q in left
             if 0 <= q - 3 and q + k < quarters]
        rows[k] = (float(np.mean(d)), len(d))
    rec.print("quarter vs departure, change since quarter -3:")
    rec.print("  " + "  ".join(f"{k:+d} {v[0]:+.1f}"
                               for k, v in rows.items()))
    after = [sales[s, q + 1] for s, q in left if q + 1 < quarters]
    chain = [float(np.mean(sales[:, q + 1])) for s, q in left
             if q + 1 < quarters]
    gap = float(np.mean(np.array(after) - np.array(chain)))
    rec.print(f"dashboard reading: a quarter after, these stores"
              f" are {gap:+.1f}")
    rec.print("  points against the chain average")
    rec.print("set in the simulation: departures follow two"
              " falling")
    rec.print("  quarters; the departure itself costs 1 point")
    return {"departures": len(left), "event": rows, "gap": gap}


def energy(rec, rng) -> dict:
    cohorts = {"hired Jul to Dec 2026": (130, True),
               "hired Jan to Jun 2027": (140, False)}
    rec.print("=== Energy Services Canada: new rotation hires"
              " still employed")
    rec.print("cohort                 hired  r1  r2  r3  r4  r6")
    out = {}
    for name, (n, pay_error) in cohorts.items():
        alive, curve = n, []
        for r in range(1, 7):
            h = 0.05
            if r == 2 and pay_error:
                h += 0.12   # first full pay run after rotation 1
            alive -= int(rng.binomial(alive, h))
            curve.append(alive)
        out[name] = [n, curve]
        rec.print(f"{name:<22} {n:>5} " + " ".join(
            f"{curve[i]:>3}" for i in (0, 1, 2, 3, 5)))
    rec.print("pay cut-off fix: crew changes loaded before the")
    rec.print("  pay cut-off from January 2027 (Chapter 10)")
    return out


def quayfen(rec) -> dict:
    cfg = transition.load()
    plan = next(c for c in cfg["cases"] if c["name"] == "Plan")
    t = transition.target(cfg, plan)["target"]
    rec.print("=== Quayfen: Hartwell tier-1 seats, plan case"
              " (Chapter 8)")
    rec.print(f"target {t} seats; SOW: 80 fewer by March 31, 2028,")
    rec.print("  with no forced exits")
    out = {}
    for a in (0.38, 0.30, 0.20):
        c = dict(cfg, annual_attrition=a)
        rows = transition.schedule(c, plan, n=8)
        q1 = next(r for r in rows if r["q"] == "2028Q1")["end"]
        hit = next((r["q"] for r in rows if r["end"] <= t), "later")
        rec.print(f"attrition {a:.0%}: seats at end of 2028Q1"
                  f" {q1}, target {hit}")
        out[a] = {"q1": q1, "reached": hit}
    return out


def main() -> None:
    rec = RunRecorder("ch28", "sectors")
    rng = np.random.default_rng(2828)
    res = {"lakemont": lakemont(rec, rng),
           "pennant": pennant(rec, rng),
           "energy": energy(rec, rng),
           "quayfen": quayfen(rec)}
    rec.note(**{k: v for k, v in res.items() if k != "quayfen"},
             quayfen={str(k): v for k, v in res["quayfen"].items()})
    print(rec.save())


if __name__ == "__main__":
    main()
