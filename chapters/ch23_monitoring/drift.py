"""Drift monitors on the A04 screening log.

Book section: "Three kinds of drift". ILLUSTRATIVE: the log is
seeded, not a Hartwell measurement. It stands in for the
per-version action log of Chapter 21, week by week from the
day routing line A04 v1.0 was signed (June 14, 2027) to the
end of November 2027, across the October 1 Northgate cutover.

Three monitors, each with a rule written down in advance:
  input    population stability index (PSI) of field-months
           bands against June to September; 0.10 watch,
           0.25 act
  output   confirm-lane share by month; a move of more than
           10 points in a month is a routing-line trigger
           (Chapter 16), and the confirm lane closes
  fairness under-40 impact ratio by month; more than 0.05
           below the signed record's 0.71 (Chapter 21) sends
           the step back to its fairness test
No model is called; the canary answers the other question,
whether the agent's judgment moved.
"""
from __future__ import annotations

import math
import random
from datetime import date, timedelta

from hrai.llm import RunRecorder

START, CUT = date(2027, 6, 14), date(2027, 10, 1)
WEEKS = 24
BANDS = ["<12", "12-23", "24-59", "60+"]
# field-months band probabilities by age group and source
MIX = {("u40", "old"): [.14, .30, .42, .14],
       ("o40", "old"): [.08, .20, .34, .38],
       ("u40", "new"): [.28, .37, .27, .08],
       ("o40", "new"): [.10, .22, .33, .35]}
U40 = {"old": .58, "new": .68}
VOL = {"old": 130, "new": 190}  # a week
EPA, CONFIRM = .82, .61


def week_log(rng: random.Random, start: date) -> list[dict]:
    rows = []
    for d in range(7):
        day = start + timedelta(days=d)
        src = "new" if day >= CUT else "old"
        for _ in range(round(rng.gauss(VOL[src], 12) / 7)):
            age = "u40" if rng.random() < U40[src] else "o40"
            band = rng.choices(BANDS, MIX[(age, src)])[0]
            meets = band in ("24-59", "60+") and \
                rng.random() < EPA
            rows.append({"day": day, "age": age, "band": band,
                         "meets": meets, "confirm": meets and
                         rng.random() < CONFIRM})
    return rows


def psi(base: list[dict], now: list[dict]) -> float:
    out = 0.0
    for b in BANDS:
        p = max(sum(r["band"] == b for r in base) / len(base),
                1e-4)
        q = max(sum(r["band"] == b for r in now) / len(now),
                1e-4)
        out += (q - p) * math.log(q / p)
    return out


def ratio(rows: list[dict]) -> float:
    def rate(g):
        grp = [r for r in rows if r["age"] == g]
        return sum(r["meets"] for r in grp) / len(grp)
    return rate("u40") / rate("o40")


def main() -> None:
    rng = random.Random(2310)
    weeks = [week_log(rng, START + timedelta(weeks=w))
             for w in range(WEEKS)]
    log = [r for w in weeks for r in w]
    base = [r for r in log if r["day"] < CUT]
    rec = RunRecorder("ch23", "drift")
    rec.print("A04 log, ILLUSTRATIVE (seeded), "
              f"{START:%b %d} to "
              f"{START + timedelta(weeks=WEEKS, days=-1):%b %d}"
              f", {len(log)} applications")
    rec.print("-- input: PSI of field-months bands vs Jun-Sep")
    for w, rows in enumerate(weeks):
        s = START + timedelta(weeks=w)
        v = psi(base, rows)
        flag = "ACT" if v >= .25 else "watch" if v >= .10 else ""
        rec.print(f"  wk {s:%b %d}  n {len(rows):>3}  "
                  f"PSI {v:.3f} {flag}")
    rec.print("-- output and fairness by month")
    rec.print("  month  n    PSI    meets  confirm  move  u40 ratio")
    prev, fired = None, []
    for m in range(6, 12):
        rows = [r for r in log if r["day"].month == m]
        share = sum(r["confirm"] for r in rows) / len(rows)
        move = "" if prev is None else \
            f"{100 * (share - prev):+5.1f}"
        name = f"{date(2027, m, 1):%b}"
        v, ir = psi(base, rows), ratio(rows)
        if v >= .25:
            fired.append(f"{name} input PSI {v:.3f}")
        elif v >= .10:
            fired.append(f"{name} input watch {v:.3f}")
        if prev is not None and abs(share - prev) > .10:
            fired.append(f"{name} confirm-lane move")
        if ir < .71 - .05:
            fired.append(f"{name} fairness {ir:.2f}")
        rec.print(f"  {name}    {len(rows):>4} {v:.3f}"
                  f" {sum(r['meets'] for r in rows) / len(rows):6.1%}"
                  f"  {share:6.1%} {move:>6}   {ir:.2f}")
        prev = share
    rec.print("-- rules that fired: " + ("; ".join(fired)
                                       or "none"))
    print(rec.save())


if __name__ == "__main__":
    main()
