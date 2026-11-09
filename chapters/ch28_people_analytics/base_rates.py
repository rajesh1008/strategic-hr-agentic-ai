"""Chapter 28: what "95% accuracy" means at a 3.8% base rate.

Book section "Base rates and the 95% claim". The suite
vendor's retention-risk add-on was offered to Hartwell in
November 2027 with the line "predicts employee attrition with
95% accuracy". This run reads that kind of claim against the
13-week shadow quarter of Chapter 22 (US salaried, July 12 to
October 8, 2027; chapters/ch22_shadow_gates/shadow.py), where
228 of 6,000 people resigned.

For each rule it prints what a manager would need to know:
  accuracy   share of all 6,000 called right
  flagged    how many names reach managers
  precision  of the flagged, the share who resigned
  recall     of those who resigned, the share flagged
  lift       precision over the base rate
The rules: flag nobody; the HR partners' watch list; and the
attrition model (v1 as built, v2 the diagnostic) flagging the
top 1%, 2%, 5%, 10% and 20%. Also the area under the ROC
curve (AUC), the other number vendors quote.

Then the roles that matter: Chapter 2's US project directors
(22 incumbents, 16% leave a year), where no prediction can be
checked in any useful time. Synthetic data; no model API.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch28_people_analytics.base_rates
"""
from __future__ import annotations

import math

import numpy as np

from hrai.llm import RunRecorder
from chapters.ch22_shadow_gates.model import fit
from chapters.ch22_shadow_gates.shadow import simulate

SHARES = (0.01, 0.02, 0.05, 0.10, 0.20)
PD_US = {"incumbents": 22, "annual_exit": 0.16}   # Chapter 2


def metrics(flag: np.ndarray, y: np.ndarray) -> dict:
    tp = int((flag & y).sum())
    fp = int((flag & ~y).sum())
    fn = int((~flag & y).sum())
    tn = int((~flag & ~y).sum())
    n = len(y)
    f = tp + fp
    prec = tp / f if f else 0.0
    return {"acc": (tp + tn) / n, "flagged": f, "tp": tp,
            "prec": prec, "recall": tp / (tp + fn),
            "lift": prec / (y.mean()) if f else None}


def auc(score: np.ndarray, y: np.ndarray) -> float:
    """Chance a random resigner scores above a random stayer
    (ties count half)."""
    y = np.asarray(y, bool)
    _, inv, cnt = np.unique(score, return_inverse=True,
                            return_counts=True)
    top = np.cumsum(cnt)               # average rank per value
    ranks = (top - (cnt - 1) / 2)[inv]
    pos = y.sum()
    neg = len(y) - pos
    return float((ranks[y].sum() - pos * (pos + 1) / 2)
                 / (pos * neg))


def line(rec, name: str, m: dict) -> None:
    rec.print(f"{name:<15} {m['acc']:>6.1%} {m['flagged']:>5}"
              f" {m['prec']:>6.1%} {m['recall']:>6.1%}"
              + (f" {m['lift']:>5.1f}" if m["lift"] is not None
                 else "     -"))


def main() -> None:
    rec = RunRecorder("ch28", "base_rates")
    rows = [r for r in simulate() if r.p.lane == "US"]
    y = np.array([r.outcome == "resigned" for r in rows])
    ps = [r.p for r in rows]
    rec.print("US salaried, 13 weeks from July 12, 2027"
              " (synthetic)")
    rec.print(f"people {len(y)}, resigned {int(y.sum())}"
              f" (base rate {y.mean():.1%})")
    rec.print("rule            accur.  flags  prec. recall  lift")
    res = {"nobody": metrics(np.zeros(len(y), bool), y)}
    line(rec, "flag nobody", res["nobody"])
    w = np.array([r.watch for r in rows])
    res["watch"] = metrics(w, y)
    line(rec, "watch list", res["watch"])
    aucs = {}
    for v in ("v1", "v2"):
        s = fit(v, "US").score(ps)
        aucs[v] = auc(s, y)
        for share in SHARES:
            m = metrics(s >= np.quantile(s, 1 - share), y)
            res[f"{v}_{share}"] = m
            line(rec, f"{v} top {share:.0%}", m)
    rec.print(f"AUC (resignation): v1 {aucs['v1']:.2f},"
              f" v2 {aucs['v2']:.2f}")
    best = max((k for k in res), key=lambda k: res[k]["acc"])
    rec.print(f"highest accuracy: {best.replace('nobody', 'flag nobody')}"
              f" ({res[best]['acc']:.1%})")
    m = res["v2_0.1"]
    rec.print(f"v2 top 10%: of every 10 names, {10 * m['prec']:.1f}"
              " resign;")
    rec.print(f"  {m['flagged'] - m['tp']} of {m['flagged']} flags"
              " are people who did not resign")
    rec.print("=== roles that matter: US project director"
              " (Chapter 2)")
    q = PD_US["incumbents"] * PD_US["annual_exit"] / 4
    rec.print(f"incumbents {PD_US['incumbents']}, expected exits"
              f" a quarter {q:.2f}")
    rec.print(f"quarters to observe 30 exits: {math.ceil(30 / q)}"
              f" ({30 / q / 4:.1f} years)")
    rec.note(results=res, auc=aucs, base=float(y.mean()),
             pd_quarters=math.ceil(30 / q))
    print(rec.save())


if __name__ == "__main__":
    main()
