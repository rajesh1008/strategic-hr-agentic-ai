"""Chapter 29: three sector cases, all deterministic.

Book section "Four more pay systems".
- Brightwater Brands, Tilburg and Lodz plants: the gap by
  category with and without the monthly attendance bonus,
  which a day of statutory care leave used to cancel.
- Cobbleford Bank & Trust: a deferred bonus statement and
  the leaver rule, computed by code (synthetic policy).
- Thorne Kessler: job postings checked against the band
  table before they go live (New York and Ontario rules as
  data; [VERIFY] in the chapter).
All synthetic.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch29_pay.sectors
"""
from __future__ import annotations

import random
from statistics import mean

from hrai.llm import RunRecorder
from .paygap import gap

PLANTS = {"Tilburg": ("EUR", 2900), "Lodz": ("PLN", 6400)}


def plant(name: str, seed: int) -> list[dict]:
    rng = random.Random(seed)
    cur, base = PLANTS[name]
    out = []
    for i in range(640 if name == "Tilburg" else 1180):
        cat = rng.choice(["operator"] * 6 + ["technician"] * 2
                         + ["team leader"])
        sex = "F" if rng.random() < 0.42 else "M"
        pay = base * {"operator": 1.0, "technician": 1.22,
                      "team leader": 1.38}[cat]
        pay *= rng.uniform(0.98, 1.02)
        care = rng.random() < (0.40 if sex == "F" else 0.08)
        bonus = 0.0
        if name == "Lodz" and cat == "operator":
            bonus = 0.0 if care else 0.20 * base
        out.append(dict(cat=cat, sex=sex, pay=pay,
                        bonus=bonus, care=care))
    return out


def plant_gaps(rec, name, rows):
    for cat in ("operator", "technician", "team leader"):
        c = [r for r in rows if r["cat"] == cat]
        f = [r["pay"] + r["bonus"] for r in c
             if r["sex"] == "F"]
        m = [r["pay"] + r["bonus"] for r in c
             if r["sex"] == "M"]
        g = gap(mean(m), mean(f))
        rec.print(f"  {name:<8} {cat:<11} women {len(f):>4} "
                  f"men {len(m):>4} gap {g:>5}%"
                  + ("  5%+" if g >= 5 else ""))


def brightwater(rec):
    rec.print("Brightwater Brands, monthly pay by category, "
              "March 2028")
    t, l = plant("Tilburg", 41), plant("Lodz", 42)
    rec.print(" with the attendance bonus as it was:")
    plant_gaps(rec, "Tilburg", t)
    plant_gaps(rec, "Lodz", l)
    for r in l:          # care leave no longer cancels it
        if r["cat"] == "operator":
            r["bonus"] = 0.20 * PLANTS["Lodz"][1]
    rec.print(" with statutory care leave counted as present:")
    plant_gaps(rec, "Lodz", l)


def deferral(rec):
    award, cash = 180_000, 0.5
    rec.print("Cobbleford Bank & Trust, 2027 bonus statement"
              " (policy CB-REM v4, synthetic)")
    rec.print(f"  award GBP {award:,}; paid March 2028 "
              f"GBP {award * cash:,.0f}")
    tr = award * (1 - cash) / 4
    for y in range(2029, 2033):
        rec.print(f"  deferred tranche March {y}: GBP {tr:,.0f}"
                  " (subject to malus)")
    rec.print("  leaves Sept 2029, good leaver: tranches "
              "2030-2032 on schedule; bad leaver: forfeit")
    rec.print("  malus or clawback: remuneration committee "
              "only; the assistant explains, never decides")


POSTINGS = [
    ("TK-NY-114", "New York, NY", "Senior Associate, Audit",
     95_000, 180_000, "Senior Associate"),
    ("TK-NY-121", "New York, NY", "Manager, Tax", 128_000,
     152_000, "Manager"),
    ("TK-NY-130", "New York, NY", "Associate, Advisory", None,
     None, "Associate"),
    ("TK-SY-019", "Sydney, NSW", "Senior Associate, Audit",
     None, None, "Senior Associate"),
    ("TK-LN-044", "London, UK", "Manager, Tax", None, None,
     "Manager"),
]
BANDS = {"Associate": (72_000, 88_000),
         "Senior Associate": (96_000, 118_000),
         "Manager": (128_000, 152_000)}


def posting_check(p) -> list[str]:
    pid, city, title, lo, hi, band = p
    b_lo, b_hi = BANDS[band]
    out = []
    if city.endswith("NY") and (lo is None or hi is None):
        out.append("NY: no minimum and maximum")
    if city.endswith("ON"):
        if lo is None:
            out.append("ON: no pay or range")
        elif hi - lo > 50_000 and hi <= 200_000:
            out.append("ON: range wider than 50,000")
    if lo is not None and (lo < b_lo or hi > b_hi):
        out.append(f"outside band {b_lo:,}-{b_hi:,}")
    return out


def thorne(rec):
    rec.print("Thorne Kessler, postings before release")
    for p in POSTINGS:
        why = posting_check(p)
        rng = "no range" if p[3] is None else \
            f"{p[3]:,}-{p[4]:,}"
        rec.print(f"  {p[0]} {p[1]:<13} {rng:<15} "
                  + ("; ".join(why) if why else "ok"))


def main() -> None:
    rec = RunRecorder("ch29", "sectors")
    brightwater(rec)
    deferral(rec)
    thorne(rec)
    print(rec.save())


if __name__ == "__main__":
    main()
