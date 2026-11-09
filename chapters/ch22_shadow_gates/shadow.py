"""Chapter 22: the shadow comparator for the attrition model.

Book sections "The attrition model in shadow", "Hartwell
Germany: a shadow run designed with the Betriebsrat" and
"How long shadow runs". In shadow the model scores everyone,
and nobody outside the shadow team sees a score: managers
are not told, no brief is sent, nothing changes. The plan
(data/shadow_plan.yaml) fixed before July 12, 2027 what is
compared and by which groups:

  against outcomes  who resigned or retired in 13 weeks
  against people    the HR partners' own watch list (US)
  by group          flag rates among people with the SAME
                    outcome, by age band and sex, because a
                    flag rate that differs among people who all
                    stayed is a difference the model made

The score is frozen on the first day, so no outcome can leak
into it. The German lane reports to the joint committee
monthly, in aggregates of 10 or more, as its agreement says.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch22_shadow_gates.shadow
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hrai.llm import RunRecorder
from .model import fit
from .workforce import BANDS, START, Person, hazards, people

TOP = 0.10        # production design: top 10% go to managers
WATCH = 0.05      # HR partners' watch list, about 5% (US)
WEEKS = 13
UNDER40 = ("18-24", "25-29", "30-39")
OVER50 = ("50-59", "60+")


@dataclass
class Seen:
    p: Person
    v1: bool          # flagged by v1 (as built)
    v2: bool          # flagged by v2 (diagnostic only)
    watch: bool       # on an HR partner's watch list (US)
    outcome: str      # stayed, resigned, retired
    week: int | None  # week of leaving, 1 to 13


def simulate(seed: int = 22) -> list[Seen]:
    ps = people()
    rng = np.random.default_rng(seed)
    hr = np.random.default_rng(seed + 1)
    out: list[Seen] = []
    for lane in ("US", "DE"):
        lp = [p for p in ps if p.lane == lane]
        flags = {}
        for v in ("v1", "v2"):
            s = fit(v, lane).score(lp)
            cut = np.quantile(s, 1 - TOP)
            flags[v] = s >= cut
        # HR partners know some of what drives resignation,
        # with noise; they do not see retirement plans
        know = np.array([np.log(hazards(p)[0])
                         + hr.normal(0, 1.0) for p in lp])
        wcut = np.quantile(know, 1 - WATCH)
        for i, p in enumerate(lp):
            resign, retire = hazards(p)
            u = rng.random()
            o = ("retired" if u < retire else "resigned"
                 if u < retire + resign else "stayed")
            wk = int(rng.integers(1, WEEKS + 1)) \
                if o != "stayed" else None
            out.append(Seen(p, bool(flags["v1"][i]),
                            bool(flags["v2"][i]),
                            lane == "US" and know[i] >= wcut,
                            o, wk))
    return out


def rate(rows: list[Seen], flag: str) -> tuple[int, int]:
    return sum(getattr(r, flag) for r in rows), len(rows)


def table(rec, rows: list[Seen], flag: str) -> dict:
    rec.print("band   stayed flag  rate | resigned caught"
              " | retired caught")
    res = {}
    for b in BANDS:
        g = [r for r in rows if r.p.band == b]
        st = [r for r in g if r.outcome == "stayed"]
        rs = [r for r in g if r.outcome == "resigned"]
        rt = [r for r in g if r.outcome == "retired"]
        k, n = rate(st, flag)
        c, m = rate(rs, flag)
        t, q = rate(rt, flag)
        res[b] = {"stayed": n, "stayed_flagged": k,
                  "resigned": m, "resigned_caught": c,
                  "retired": q, "retired_caught": t}
        rec.print(f"{b:<6} {n:>6} {k:>4} {k / n:>5.2f} |"
                  f" {m:>8} {c:>6} | {q:>7} {t:>6}")
    return res


def pair(rows, flag, a, b, outcome="stayed"):
    x = [r for r in rows if r.p.band in a
         and r.outcome == outcome]
    y = [r for r in rows if r.p.band in b
         and r.outcome == outcome]
    return rate(x, flag), rate(y, flag)


def lane_report(rec, rows: list[Seen], lane: str,
                flag: str) -> dict:
    n = len(rows)
    f = sum(getattr(r, flag) for r in rows)
    oc = {o: sum(r.outcome == o for r in rows)
          for o in ("stayed", "resigned", "retired")}
    rec.print(f"{lane}: {n} people, {f} flagged; stayed"
              f" {oc['stayed']}, resigned {oc['resigned']},"
              f" retired {oc['retired']}")
    res = table(rec, rows, flag)
    (k1, n1), (k2, n2) = pair(rows, flag, OVER50, UNDER40)
    r1, r2 = k1 / n1, k2 / n2
    rec.print(f"stayers flagged: 50+ {k1}/{n1} = {r1:.3f};"
              f" under 40 {k2}/{n2} = {r2:.3f}")
    rec.print(f"  ratio 50+ to under 40: {r1 / r2:.2f}")
    sx = {s: rate([r for r in rows if r.p.sex == s
                   and r.outcome == "stayed"], flag)
          for s in sorted({r.p.sex for r in rows})}
    rec.print("stayers flagged by sex: " + "; ".join(
        f"{s} {k}/{m} = {k / m:.3f}" for s, (k, m)
        in sx.items()))
    old = [r for r in rows if getattr(r, flag)
           and r.p.band in OVER50]
    rec.print(f"flags on 50+: {len(old)} of {f}; of them"
              f" retired {sum(r.outcome == 'retired' for r in old)},"
              f" resigned {sum(r.outcome == 'resigned' for r in old)}")
    hit = sum(getattr(r, flag) and r.outcome == "resigned"
              for r in rows)
    rec.print(f"resignations among flags: {hit}/{f}"
              f" ({hit / f:.1%}); base rate"
              f" {oc['resigned'] / n:.1%}")
    return {"bands": res, "over50": [k1, n1],
            "under40": [k2, n2], "sex": sx,
            "flags_over50": len(old), "flags": f,
            "hits": hit, "outcomes": oc}


def watch_report(rec, rows: list[Seen]) -> dict:
    w = [r for r in rows if r.watch]
    hit = sum(r.outcome == "resigned" for r in w)
    (k1, n1), (k2, n2) = pair(rows, "watch", OVER50, UNDER40)
    rec.print(f"HR partners' watch list: {len(w)} people,"
              f" {hit} resigned ({hit / len(w):.1%})")
    rec.print(f"  stayers on the list: 50+ {k1 / n1:.3f};"
              f" under 40 {k2 / n2:.3f}")
    return {"listed": len(w), "hits": hit,
            "over50": [k1, n1], "under40": [k2, n2]}


def de_months(rec, rows: list[Seen]) -> list[dict]:
    """The joint committee's monthly report: aggregates only,
    cells under 10 shown as '<10'."""
    out = []
    for m, upto in ((1, 4), (2, 9), (3, 13)):
        cur = [r for r in rows if r.week is None
               or r.week > upto]       # still employed
        def cell(bands):
            g = [r for r in cur if r.p.band in bands]
            k = sum(r.v1 for r in g)
            return k, len(g)
        a, b = cell(OVER50), cell(UNDER40)
        show = lambda k, n: ("<10" if k < 10 else str(k)) + \
            f"/{n}"
        rec.print(f"DE month {m} (to week {upto}): flagged"
                  f" 50+ {show(*a)}, under 40 {show(*b)}")
        out.append({"month": m, "over50": a, "under40": b})
    return out


def main() -> None:
    rec = RunRecorder("ch22", "shadow")
    rows = simulate()
    us = [r for r in rows if r.p.lane == "US"]
    de = [r for r in rows if r.p.lane == "DE"]
    rec.print(f"Attrition model v1 in shadow, {START:%b %d, %Y}"
              f" + {WEEKS} weeks")
    rec.print("score frozen at start; top 10% flagged; no"
              " flag shown to anyone")
    rec.print("=== US salaried")
    u = lane_report(rec, us, "US", "v1")
    h = watch_report(rec, us)
    rec.print("=== Hartwell Germany (joint committee)")
    d = lane_report(rec, de, "DE", "v1")
    m = de_months(rec, de)
    rec.print("=== v2 diagnostic (resignation label, no"
              " milestone): not a gate result")
    v2 = {}
    for lane, rr in (("US", us), ("DE", de)):
        (k1, n1), (k2, n2) = pair(rr, "v2", OVER50, UNDER40)
        (y1, z1), _ = pair(rr, "v2", ("18-24",), UNDER40)
        rec.print(f"{lane} v2 stayers flagged: 50+ {k1 / n1:.3f};"
                  f" under 40 {k2 / n2:.3f};"
                  f" 18-24 {y1 / z1:.3f}")
        v2[lane] = {"over50": [k1, n1], "under40": [k2, n2],
                    "u25": [y1, z1]}
    rec.note(us=u, watch=h, de=d, de_months=m, v2=v2)
    print(rec.save())


if __name__ == "__main__":
    main()
