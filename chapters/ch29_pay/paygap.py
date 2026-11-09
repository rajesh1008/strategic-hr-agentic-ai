"""Chapter 29: pay-gap analysis Hartwell can defend.

Book section "The pay-gap analysis". Two lanes on the same
synthetic workforce (fixtures/hartwell/employees.csv.gz):
- Hartwell UK, 3,200 staff: the six gender pay gap measures
  and pay quartiles on a snapshot (UK reporting regulations,
  [VERIFY] in the chapter).
- Hartwell Netherlands, 900 staff: the gap by category of
  workers (pay grade from the job evaluation), raw and
  within the collective agreement's seniority step, with any
  category at 5% or more flagged (Directive (EU) 2023/970,
  Arts 9 and 10, [VERIFY] in the chapter).
Pay is generated here with seed 29. Only women and men are
compared, as both regimes require; the count of other and
undisclosed records is printed, never dropped silently.

Run:  HRAI_MODEL=no-model python -m chapters.ch29_pay.paygap
"""
from __future__ import annotations

import csv
import gzip
import random
from statistics import mean, median

from hrai.llm import REPO, RunRecorder

UK_BASE = {"G3": 13.40, "G4": 16.20, "G5": 20.10}
NL_BASE = {"G3": 17.10, "G4": 20.40, "G5": 24.90}
TRADES = {"Engineering", "Electrician", "HVAC Technician"}


def staff(entity: str) -> list[dict]:
    p = REPO / "fixtures" / "hartwell" / "employees.csv.gz"
    with gzip.open(p, "rt") as f:
        rows = csv.DictReader(l for l in f
                              if not l.startswith("#"))
        return [r for r in rows if r["entity"] == entity]


def uk_pay() -> list[dict]:
    """Inside a grade, two discretionary elements differ by
    sex: a market supplement (trades, G4 and G5) and the
    night allowance, which supervisors allocate by roster."""
    rng = random.Random(29)
    out = []
    for r in staff("Hartwell UK"):
        man = r["gender"] == "M"
        step = rng.randint(0, 4)
        h = UK_BASE[r["grade"]] * (1 + 0.025 * step)
        trade = (r["job_family"] in TRADES
                 or r["job_family"] == "Field Service Technician")
        if trade and r["grade"] in ("G4", "G5"):
            h += 2.10 if rng.random() < (0.45 if man
                                         else 0.12) else 0
        field = r["worker_type"] == "field"
        if field and rng.random() < (0.35 if man else 0.15):
            h += 1.85
        part = float(r["fte"]) < 1
        bonus = 0.0
        if field and not part and rng.random() < 0.9:
            bonus = rng.choice([450, 600, 750]
                               if man else [450, 450, 600])
        elif not field and rng.random() < 0.5:
            bonus = rng.choice([500, 900, 1400])
        out.append(dict(sex=r["gender"], grade=r["grade"],
                        step=step, hourly=round(h, 2),
                        bonus=bonus * (float(r["fte"])
                                       if not field else 1)))
    return out


def nl_pay() -> list[dict]:
    """Collective-agreement scale with yearly steps. Women in
    G4 joined in the 2025 recruitment drive (lower steps); in
    G5 a personal allowance granted at hire went mostly to
    men."""
    rng = random.Random(2930)
    out = []
    for r in staff("Hartwell Netherlands"):
        man = r["gender"] == "M"
        top = 9 if man or r["grade"] != "G4" else 3
        step = rng.randint(0, top)
        h = NL_BASE[r["grade"]] * (1.03 ** step)
        allow = (r["grade"] == "G5" and rng.random()
                 < (0.50 if man else 0.08))
        h *= 1.14 if allow else 1
        out.append(dict(sex=r["gender"], grade=r["grade"],
                        step=step, hourly=round(h, 2),
                        allowance=allow, bonus=0.0))
    return out


def gap(m: float, f: float) -> float:
    return round(100 * (m - f) / m, 1) + 0.0 if m else 0.0


def six(rows: list[dict]) -> list[str]:
    m = [r for r in rows if r["sex"] == "M"]
    f = [r for r in rows if r["sex"] == "F"]
    hm, hf = [r["hourly"] for r in m], [r["hourly"] for r in f]
    bm = [r["bonus"] for r in m if r["bonus"]]
    bf = [r["bonus"] for r in f if r["bonus"]]
    out = [
        f"mean hourly gap      {gap(mean(hm), mean(hf)):>5}%",
        f"median hourly gap    "
        f"{gap(median(hm), median(hf)):>5}%",
        f"mean bonus gap       {gap(mean(bm), mean(bf)):>5}%",
        f"median bonus gap     "
        f"{gap(median(bm), median(bf)):>5}%",
        f"received a bonus     men {100*len(bm)/len(m):.1f}%,"
        f" women {100*len(bf)/len(f):.1f}%"]
    both = sorted(m + f, key=lambda r: r["hourly"])
    q = len(both) // 4
    for i, name in enumerate(["lower", "lower middle",
                              "upper middle", "upper"]):
        part = both[i * q:(i + 1) * q if i < 3 else None]
        w = sum(r["sex"] == "F" for r in part)
        out.append(f"{name:<14} quartile women "
                   f"{100 * w / len(part):.1f}%")
    return out


def within(rows: list[dict], grade: str) -> float:
    """Gap inside the same grade and seniority step, cells
    with at least 5 women and 5 men, weighted by women."""
    num = den = 0.0
    for s in range(10):
        c = [r for r in rows if r["grade"] == grade
             and r["step"] == s]
        m = [r["hourly"] for r in c if r["sex"] == "M"]
        f = [r["hourly"] for r in c if r["sex"] == "F"]
        if len(m) >= 5 and len(f) >= 5:
            num += len(f) * gap(mean(m), mean(f))
            den += len(f)
    return round(num / den, 1) if den else float("nan")


def categories(rows: list[dict]) -> list[tuple]:
    out = []
    for g in sorted({r["grade"] for r in rows}):
        c = [r for r in rows if r["grade"] == g]
        m = [r["hourly"] for r in c if r["sex"] == "M"]
        f = [r["hourly"] for r in c if r["sex"] == "F"]
        out.append((g, len(f), len(m), gap(mean(m), mean(f)),
                    gap(median(m), median(f)), within(rows, g)))
    return out


def table(rec, rows, title):
    rec.print(title)
    rec.print("grade women  men  mean  median  same step  flag")
    for g, nf, nm, a, b, w in categories(rows):
        flag = "5%+ " if max(a, w) >= 5 else ""
        flag += "unexplained" if w >= 5 else ""
        rec.print(f"{g:<5} {nf:>5} {nm:>4} {a:>5}% {b:>6}% "
                  f"{w:>8}%  {flag}".rstrip())
        rec.note(lane=title, grade=g, women=nf, men=nm,
                 mean=a, median=b, within=w)


def main() -> None:
    rec = RunRecorder("ch29", "paygap")
    uk = uk_pay()
    other = sum(r["sex"] not in ("F", "M") for r in uk)
    rec.print("Hartwell UK, snapshot April 5, 2027 "
              f"(women and men; {other} other or undisclosed"
              " not in the measures)")
    for line in six([r for r in uk if r["sex"] in "FM"]):
        rec.print("  " + line)
    table(rec, uk, "Hartwell UK by grade")
    nl = nl_pay()
    other = sum(r["sex"] not in ("F", "M") for r in nl)
    table(rec, nl, "Hartwell Netherlands by category"
          f" ({other} other or undisclosed not compared)")
    g5 = [r for r in nl if r["grade"] == "G5"]
    for sex in ("M", "F"):
        p = [r for r in g5 if r["sex"] == sex]
        a = sum(r["allowance"] for r in p)
        rec.print(f"  G5 personal allowance: {sex} {a} of "
                  f"{len(p)}")
    print(rec.save())


if __name__ == "__main__":
    main()
