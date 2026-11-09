"""Chapter 28: does a raise keep people? Three answers.

Book sections "Prediction is not cause" and "The retention
test". The question people analytics was asked after DR-22-01
(October 18, 2027) is causal: if Hartwell raises pay for US
salaried staff paid below 0.92 of their range midpoint, how
many fewer resign in the next quarter? Three analyses answer
it on the synthetic world in world.py:

  1. naive     people who got a "retention raise" (the
               counter-offer code in HartwellOne) against
               people paid below 0.92 who got nothing
  2. by rule   only raises assigned by the range rule (market
               adjustments, given to whole business units when
               the budget allowed), against nothing
  3. test      the retention test of January 10 to April 7,
               2028: everyone eligible gets the raise; a coin
               decides who gets it in January (wave 1) and who
               in April (wave 2); compare resignations in the
               quarter between

The same test randomizes the order of managers' stay
conversations for everyone else, and reads the result by
whether the attrition model (v2, diagnostic) flagged them.

Because the world is simulated, the run can also print the
effect the world was set to have, which no real analysis can
see. Raise cost uses an illustrative midpoint, not Hartwell
pay data. No model API is called.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch28_people_analytics.causal
"""
from __future__ import annotations

import math

import numpy as np

from hrai.llm import RunRecorder
from chapters.ch22_shadow_gates.model import fit
from .world import (RAISED_COMPA, TEST_END, TEST_START, history,
                    resign_p, test_population)

MIDPOINT_USD = 96_000     # illustrative average range midpoint
SEED = 28


def rate(k: int, n: int) -> str:
    return f"{k}/{n} = {k / n:.1%}"


def diff_ci(k1, n1, k2, n2) -> tuple[float, float, float]:
    """Difference in proportions (2 minus 1) with a 95%
    normal-approximation interval."""
    p1, p2 = k1 / n1, k2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    d = p2 - p1
    return d, d - 1.96 * se, d + 1.96 * se


def needed(p0: float, d: float) -> int:
    """People per wave to detect a fall of d from p0 (two-
    sided 5% test, 80% power, normal approximation)."""
    p1 = p0 - d
    z = 1.96 + 0.84
    return math.ceil(z * z * (p0 * (1 - p0) + p1 * (1 - p1))
                     / (d * d))


def naive(rec, h) -> dict:
    none = [r for r in h if r.raise_kind is None]
    co = [r for r in h if r.raise_kind == "counter-offer"]
    mk = [r for r in h if r.raise_kind == "market"]
    k = lambda g: sum(r.resigned for r in g)
    rec.print("=== 1. history, 2025Q3 to 2027Q2: paid below 0.92"
              " of midpoint")
    rec.print(f"no raise           resigned {rate(k(none), len(none))}")
    rec.print(f"retention raise    resigned {rate(k(co), len(co))}")
    rec.print("  naive reading: retention raises barely keep"
              " anyone")
    rec.print("=== 2. same history, split by how the raise was"
              " assigned")
    rec.print(f"market adjustment  resigned {rate(k(mk), len(mk))}")
    rec.print("  (assigned by the range rule to whole units)")
    s = lambda g: sum(r.searching for r in g) / len(g)
    rec.print("unrecorded in HartwellOne, shown because the world"
              " is simulated:")
    rec.print(f"  already looking: retention raise {s(co):.0%},"
              f" market {s(mk):.0%}, no raise {s(none):.0%}")
    return {"none": [k(none), len(none)], "counter": [k(co), len(co)],
            "market": [k(mk), len(mk)],
            "searching": {"counter": s(co), "market": s(mk),
                          "none": s(none)}}


def test(rec) -> dict:
    rng = np.random.default_rng(SEED)
    tp = test_population()
    ps = [p for p, _ in tp]
    v2 = fit("v2", "US").score(ps)
    flag = v2 >= np.quantile(v2, 0.9)
    wave1 = rng.random(len(tp)) < 0.5
    out = {"pay": {1: [0, 0], 2: [0, 0]},
           "talk": {(f, w): [0, 0] for f in (True, False)
                    for w in (1, 2)},
           "set": {}}
    exp_pay = [0.0, 0.0]
    exp_talk = {True: [0.0, 0.0, 0], False: [0.0, 0.0, 0]}
    gap = []
    for i, (p, s) in enumerate(tp):
        w = 1 if wave1[i] else 2
        if p.compa < 0.92:                   # pay arm
            q = resign_p(p, s, raised=(w == 1))
            out["pay"][w][0] += int(rng.random() < q)
            out["pay"][w][1] += 1
            exp_pay[0] += resign_p(p, s)
            exp_pay[1] += resign_p(p, s, raised=True)
            gap.append(RAISED_COMPA - p.compa)
        else:                                # stay-talk arm
            q = resign_p(p, s, talk=(w == 1))
            c = out["talk"][(bool(flag[i]), w)]
            c[0] += int(rng.random() < q)
            c[1] += 1
            e = exp_talk[bool(flag[i])]
            e[0] += resign_p(p, s)
            e[1] += resign_p(p, s, talk=True)
            e[2] += 1
    rec.print(f"=== 3. retention test, {TEST_START:%b} "
              f"{TEST_START.day} to {TEST_END:%b} {TEST_END.day},"
              f" {TEST_END.year}: order set by coin")
    (k1, n1), (k2, n2) = out["pay"][1], out["pay"][2]
    d, lo, hi = diff_ci(k1, n1, k2, n2)
    rec.print("pay arm: paid below 0.92 of midpoint, raised to"
              f" {RAISED_COMPA}")
    rec.print(f"  wave 1 (raised Jan 10)  resigned {rate(k1, n1)}")
    rec.print(f"  wave 2 (raised Apr 10)  resigned {rate(k2, n2)}")
    rec.print(f"  difference {d:.1%} (95% interval {lo:.1%} to"
              f" {hi:.1%})")
    per100 = 100 * d
    rec.print(f"  resignations avoided per 100 raises: {per100:.1f}")
    n = n1 + n2
    cost = sum(gap) * MIDPOINT_USD
    rec.print(f"  cost of raising all {n}: ${cost:,.0f} a year")
    rec.print("    (illustrative midpoint)")
    avoided = d * n
    rec.print(f"  about {avoided:.0f} resignations avoided in the"
              " quarter,")
    rec.print(f"    ${cost / 4 / avoided:,.0f} of raise paid per"
              " resignation avoided")
    rec.print(f"  world was set to: {exp_pay[0] / n:.1%} without,"
              f" {exp_pay[1] / n:.1%} with")
    rec.print("    people per wave to detect it:"
              f" {needed(exp_pay[0] / n, (exp_pay[0] - exp_pay[1]) / n):,}")
    rec.print("talk arm: everyone else; wave 1 gets a stay"
              " conversation in January")
    res_t = {}
    for f, name in ((True, "flagged by v2"), (False, "not flagged")):
        (a, b), (c, e) = out["talk"][(f, 1)], out["talk"][(f, 2)]
        d, lo, hi = diff_ci(a, b, c, e)
        rec.print(f"  {name:<14} wave 1 {rate(a, b)}")
        rec.print(f"  {'':<14} wave 2 {rate(c, e)}")
        rec.print(f"  {'':<14} avoided per 100 talks {100 * d:.1f}")
        rec.print(f"  {'':<14}   (95% interval {100 * lo:.1f} to"
                  f" {100 * hi:.1f})")
        x = exp_talk[f]
        rec.print(f"  {'':<14} world was set to"
                  f" {100 * (x[0] - x[1]) / x[2]:.1f} per 100")
        rec.print(f"  {'':<14} people per wave to detect it:"
                  f" {needed(x[0] / x[2], (x[0] - x[1]) / x[2]):,}")
        res_t[name] = {"w1": [a, b], "w2": [c, e],
                       "set_per100": 100 * (x[0] - x[1]) / x[2]}
    out_j = {"pay": {"w1": [k1, n1], "w2": [k2, n2],
                     "set": [exp_pay[0] / n, exp_pay[1] / n],
                     "cost": cost},
             "talk": res_t}
    return out_j


def main() -> None:
    rec = RunRecorder("ch28", "causal")
    rec.print("Does a raise keep people? US salaried, Hartwell"
              " (synthetic)")
    a = naive(rec, history())
    b = test(rec)
    rec.note(history=a, test=b)
    print(rec.save())


if __name__ == "__main__":
    main()
