"""Chapter 21: three second organizations (no model).

Book sections "Crossfield: the intersectional test",
"Cobbleford Bank: proxies inside a promotion model" and
"Brightwater: one scheme, two countries". Fixtures are
generated here with a fixed seed; the rules that shape each
group's numbers are stated beside each generator.

Run:  HRAI_MODEL=no-model python -m chapters.ch21_fairness.sectors
"""
from __future__ import annotations

import random

from hrai.llm import REPO, RunRecorder

from chapters.ch07_adverse_impact import impact as ai

from . import fairness as fx

SEED = 21
RACES = [("White", .46), ("Black or African American", .24),
         ("Hispanic or Latino", .20), ("Asian", .07),
         ("Two or more races", .03)]


# --- Crossfield: RankRight trial, three client accounts ---
# Shortlist chance 0.30, times 0.55 for Black women aged 40
# and over (the ranking weighs unbroken weeks on assignment);
# nobody else differs. Every other gap is chance.
def crossfield(rng: random.Random) -> list[dict]:
    out = []
    for month in ("Jun", "Jul", "Aug"):
        for _ in range(1400):
            sex = "women" if rng.random() < .48 else "men"
            race = fx_pick(rng, RACES)
            old = "40+" if rng.random() < .3 else "under 40"
            p = .30
            if sex == "women" and old == "40+" and \
                    race.startswith("Black"):
                p *= .55
            out.append({"month": month, "sex": sex, "race": race,
                        "age": old, "shown": rng.random() < p})
    return out


# --- Cobbleford Bank: promotion-readiness model -----------
# Same performance for everyone. Women are more often part
# time, have more months of leave (parental leave), say yes
# to relocation less often and log fewer after-hours
# collaboration hours. "Ready now" is the top quarter.
WEIGHTS = {"rating": 2.0, "tenure": .4, "fte": 1.0,
           "leave": -.15, "mobile": .8, "after_hours": .12}


def cobbleford(rng: random.Random) -> list[dict]:
    out = []
    for site, n in (("Charlotte", 1700), ("Edinburgh", 700)):
        for _ in range(n):
            w = rng.random() < .5
            old = rng.random() < .35
            out.append({
                "site": site, "sex": "women" if w else "men",
                "age": "40+" if old else "under 40",
                "rating": rng.choice([2, 3, 3, 3, 4, 4, 5]),
                "tenure": rng.randint(1, 8),
                "fte": .6 if rng.random() < (.22 if w else .04)
                else 1.0,
                "leave": rng.choice([0, 0, 0, 2, 4, 6, 9, 12])
                if w else rng.choice([0] * 7 + [1, 2]),
                "mobile": rng.random() < ((.35 if w else .55)
                                          - (.15 if old else 0)),
                "after_hours": max(0, rng.gauss(
                    5 if w else 7, 2) - (1 if old else 0))})
    return out


def score(r: dict, drop: tuple[str, ...] = ()) -> float:
    return sum(w * float(r[k]) for k, w in WEIGHTS.items()
               if k not in drop)


def ready(rs: list[dict], drop=()) -> set[int]:
    s = sorted(range(len(rs)), key=lambda i: -score(rs[i], drop))
    return set(s[: len(rs) // 4])


# --- Brightwater: graduate scheme, Leeds and Lodz ----------
# The 2027 scheme asked for a first degree finished in 2025
# or later. Mature graduates are older by definition; the
# draft alternative asks for under two years of professional
# work since the first degree.
def brightwater(rng: random.Random) -> list[dict]:
    out = []
    for country, n in (("UK", 5200), ("Poland", 1900)):
        for _ in range(n):
            band = fx_pick(rng, [("under 25", .62),
                                 ("25 to 29", .26), ("30+", .12)])
            recent = rng.random() < {"under 25": .9,
                                     "25 to 29": .45,
                                     "30+": .2}[band]
            work = rng.random() < {"under 25": .95,
                                   "25 to 29": .75,
                                   "30+": .55}[band]
            out.append({"country": country, "age": band,
                        "sex": "women" if rng.random() < .52
                        else "men",
                        "window": recent, "experience": work,
                        "ethnicity": "not collected"
                        if country == "Poland" else "collected"})
    return out


def fx_pick(rng, table):
    x, acc = rng.random(), 0.0
    for name, p in table:
        acc += p
        if x < acc:
            return name
    return table[-1][0]


def main() -> None:
    rng = random.Random(SEED)
    rec = RunRecorder("ch21", "sectors")
    p = rec.print

    xs = crossfield(rng)
    p(f"Crossfield RankRight trial: {len(xs)} candidates, "
      f"Jun to Aug")
    p("single axes, lowest impact ratio (shortlist shown):")
    for label, key in (("sex", "sex"), ("race", "race"),
                       ("age", "age")):
        t, _, _ = fx.readable(xs, lambda r, k=key: r[k],
                              lambda r: r["shown"])
        low = min((r for r in t if "REF" not in r.flags),
                  key=lambda r: r.ratio)
        p(f"  {label:<5}{ai.SHORT.get(low.group, low.group)} "
          f"{low.ratio:.2f} {' '.join(low.flags)}".rstrip())
    g3 = ai.intersect("sex", "race", "age")
    t, _ = ai.table(xs, g3, lambda r: r["shown"])
    ref = next(r for r in t if "REF" in r.flags)
    pv = {r.group: r.p for r in t if r.p is not None}
    keep = fx.holm(pv)
    below = [r for r in t if r.ratio is not None and r.ratio < .8]
    p(f"sex x race x age: {len(t)} cells; reference "
      f"{_name(ref.group)} ({ref.n})")
    p(f"cells below 0.80: {len(below)}; p < 0.05: "
      f"{sum(v < .05 for v in pv.values())}; after Holm: "
      f"{sum(keep.values())}")
    for r in sorted(below, key=lambda r: r.ratio):
        p(f"  {_name(r.group):<31}{r.n:>5}{r.ratio:>6.2f}"
          f"{'  survives' if keep.get(r.group) else ''}")
    p("Black women 40+, by month and pooled:")
    bw = "women & Black or African American & 40+"
    for m in ("Jun", "Jul", "Aug", "pooled"):
        rows = xs if m == "pooled" else [r for r in xs
                                          if r["month"] == m]
        tt, _ = ai.table(rows, g3, lambda r: r["shown"])
        r = next(x for x in tt if x.group == bw)
        rf = next(x for x in tt if "REF" in x.flags)
        p(f"  {m:<7}n {r.n:>3}  ratio {r.ratio:.2f}  p "
          f"{_p(r.p)}  {fx.cell(r.n, rf.rate)}")

    cb = cobbleford(rng)
    p("")
    p(f"Cobbleford readiness model: {len(cb)} associates; "
      f"ready now = top quarter")
    p(f"{'model':<22}{'women/men':>10}{'40+/under 40':>14}")
    for name, drop in [("all six features", ()),
                       ("without leave", ("leave",)),
                       ("without part time", ("fte",)),
                       ("without after-hours", ("after_hours",)),
                       ("without relocation", ("mobile",)),
                       ("without those four", ("leave", "fte",
                                               "after_hours",
                                               "mobile"))]:
        top = ready(cb, drop)
        rs = [dict(r, top=i in top) for i, r in enumerate(cb)]
        sx, _ = ai.table(rs, lambda r: r["sex"], lambda r: r["top"])
        ag, _ = ai.table(rs, lambda r: r["age"], lambda r: r["top"])
        p(f"{name:<22}{_ratio(sx, 'women'):>10}"
          f"{_ratio(ag, '40+'):>14}")
    p("feature gap, women minus men (mean):")
    for k in ("leave", "fte", "after_hours", "mobile", "rating"):
        w = [float(r[k]) for r in cb if r["sex"] == "women"]
        m = [float(r[k]) for r in cb if r["sex"] == "men"]
        p(f"  {k:<12}{sum(w) / len(w) - sum(m) / len(m):>7.2f}")

    bw_ = brightwater(rng)
    p("")
    p(f"Brightwater graduate scheme 2027: {len(bw_)} applicants")
    for country in ("UK", "Poland"):
        rows = [r for r in bw_ if r["country"] == country]
        for rule in ("window", "experience"):
            t, _ = ai.table(rows, lambda r: r["age"],
                            lambda r, k=rule: r[k])
            cells = "  ".join(f"{r.group} {r.rate:.2f}"
                              for r in sorted(t, key=lambda r: r.group))
            p(f"  {country:<7}{rule:<11}{cells}")
            low = min(t, key=lambda r: r.ratio or 1)
            p(f"  {'':<18}lowest ratio {low.group} {low.ratio:.2f} "
              f"{' '.join(low.flags)}".rstrip())
    p("  ethnicity: UK collected; Poland not collected, "
      "not tested")
    rec.note(crossfield=len(xs), cobbleford=len(cb),
             brightwater=len(bw_))
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


def _name(g: str) -> str:
    return " & ".join(ai.SHORT.get(x, x) for x in g.split(" & "))


def _p(v):
    return "<0.001" if v < .001 else f"{v:.3f}"


def _ratio(t, group) -> str:
    r = next(x for x in t if x.group == group)
    return f"{r.ratio:.2f}"


if __name__ == "__main__":
    main()
