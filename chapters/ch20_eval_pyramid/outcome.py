"""Level 4: outcome measures, computed from a conversation log.

Book section: "Level 4: outcomes, not containment". The
measures are the ones PS-01 (Chapter 10) names, plus the two
that only show up days later: a repeat contact on the same
request and a reversal. The log here is SYNTHETIC and
ILLUSTRATIVE: eight weeks drawn by a seeded generator from the
rates in RATES, which are planning assumptions, not Hartwell
measurements. The code that scores the log is the part to
reuse; point it at a real export with the same columns.

Run: HRAI_MODEL=no-model python -m \\
     chapters.ch20_eval_pyramid.outcome
"""
from __future__ import annotations

import random
from statistics import median, quantiles

from hrai.llm import RunRecorder

SEED, WEEKS, PER_WEEK = 2027, 8, 300

# Illustrative rates for what happens after a conversation.
RATES = {
    "kind": {"address": 0.55, "bank": 0.25, "status": 0.20},
    "address": {"done": 0.86, "denied": 0.05,
                "future_written_now": 0.03,
                "needs_person": 0.04, "mismatch": 0.02},
    "bank": {"done": 0.80, "expired_unseen": 0.06,
             "needs_person": 0.06, "denied": 0.08},
    "status": {"answered": 0.70, "said_not_found": 0.18,
               "needs_person": 0.12},
    "thumbs_up": {"ok": 0.78, "not_ok": 0.61},
    "human_minutes": (4, 9, 95),  # low, mode, high
    "nothing": 0.07,     # left with no answer and no ticket
    "repeat_if_ok": 0.04,
}


def draw(rng: random.Random, table: dict) -> str:
    r, acc = rng.random(), 0.0
    for k, p in table.items():
        acc += p
        if r < acc:
            return k
    return k


def generate(seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    log = []
    for i in range(WEEKS * PER_WEEK):
        kind = draw(rng, RATES["kind"])
        end = draw(rng, RATES[kind])
        row = {"id": f"C{i:05d}", "week": i // PER_WEEK + 1,
               "kind": kind, "end": end, "human_min": None,
               "nothing": rng.random() < RATES["nothing"]}
        if row["nothing"]:
            row["end"] = "nothing"
        if end in ("needs_person", "mismatch") \
                and not row["nothing"]:
            row["human_min"] = rng.triangular(
                *RATES["human_minutes"][::2],
                RATES["human_minutes"][1])
        # Days later: did the employee come back, was it undone?
        bad = row["end"] in ("future_written_now",
                             "expired_unseen",
                             "said_not_found", "nothing")
        row["repeat_7d"] = bad or (
            rng.random() < RATES["repeat_if_ok"])
        row["reversed_30d"] = row["end"] == "future_written_now"
        row["thumbs_up"] = rng.random() < RATES["thumbs_up"][
            "not_ok" if bad else "ok"]
        log.append(row)
    return log


def contained(r: dict) -> bool:
    """The vendor's measure: no human touched it."""
    return r["human_min"] is None and not r["nothing"]


def resolved(r: dict) -> bool:
    """Ours: the need was met and stayed met."""
    good = r["end"] in ("done", "denied", "answered")
    return good and not r["repeat_7d"] and not r["reversed_30d"]


def pct(n: int, d: int) -> str:
    return f"{n:,} of {d:,} ({100 * n / d:.1f}%)"


def main() -> None:
    rec = RunRecorder("ch20", "outcome")
    log = generate()
    n = len(log)
    c = [r for r in log if contained(r)]
    res = [r for r in log if resolved(r)]
    hum = sorted(r["human_min"] for r in log if r["human_min"])
    rec.print(f"Outcome log: {n:,} conversations, {WEEKS} weeks"
              f" (SYNTHETIC, seed {SEED})")
    rec.print(f"  contained (no human)        {pct(len(c), n)}")
    rec.print(f"  resolved, stayed resolved   "
              f"{pct(len(res), n)}")
    nothing = sum(r["nothing"] for r in log)
    rec.print(f"  ended in nothing (PS-01)    "
              f"{pct(nothing, n)}")
    p90 = quantiles(hum, n=10)[-1]
    rec.print(f"  time to human, minutes      median "
              f"{median(hum):.0f}, p90 {p90:.0f}"
              f" (n={len(hum)})")
    gap = [r for r in c if not resolved(r)]
    rec.print(f"Contained but not resolved: {len(gap):,}")
    causes = {}
    for r in gap:
        causes[r["end"]] = causes.get(r["end"], 0) + 1
    for k, v in sorted(causes.items(), key=lambda x: -x[1]):
        rec.print(f"  {k:<20} {v:>4}")
    up = lambda rows: sum(r["thumbs_up"] for r in rows)
    rec.print("Thumbs up (what employees felt):")
    rec.print(f"  resolved                    "
              f"{pct(up(res), len(res))}")
    rec.print(f"  contained, not resolved     "
              f"{pct(up(gap), len(gap))}")
    for w in range(1, WEEKS + 1):
        wk = [r for r in log if r["week"] == w]
        rec.note(week=w, n=len(wk),
                 contained=sum(map(contained, wk)),
                 resolved=sum(map(resolved, wk)),
                 nothing=sum(r["nothing"] for r in wk))
    print(rec.save())


if __name__ == "__main__":
    main()
