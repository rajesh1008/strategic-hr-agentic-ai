"""Chapter 10: reading a ticket export.

Step 1 compares the desk's own drop-down category with the
taxonomy. Step 2 draws a random sample of 600 tickets, which two
advisers labeled with the taxonomy, and estimates the share of
each route with a 95% interval. No model is used.

Run: HRAI_MODEL=no-model python -m chapters.ch10_diagnose.export
"""
from __future__ import annotations

import csv
import gzip
import math
import random
from collections import Counter
from pathlib import Path

from .taxonomy import ROUTES, TAX, gold

DATA = Path(__file__).resolve().parent / "data"
SAMPLE_SEED, SAMPLE_N = 2027, 600


def load() -> list[dict]:
    with gzip.open(DATA / "tickets.csv.gz", "rt") as f:
        return list(csv.DictReader(f))


def sample(rows: list[dict]) -> list[dict]:
    return random.Random(SAMPLE_SEED).sample(rows, SAMPLE_N)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def main() -> None:
    from hrai.llm import RunRecorder
    rec = RunRecorder("ch10", "export")
    p = rec.print
    rows = load()
    p(f"Ticket export, Q4 2026: {len(rows):,} tickets")
    p("The desk's own category (top five):")
    for k, v in Counter(r["system_category"] for r in
                        rows).most_common(5):
        p(f"  {k:<16}{v:>6,}  {100 * v / len(rows):4.1f}%")
    s = sample(rows)
    g = Counter(gold(r["label"], int(r["sensitive"])) for r in s)
    p(f"Random sample labeled with the taxonomy: {len(s)}")
    for rt in ROUTES:
        lo, hi = wilson(g[rt], len(s))
        p(f"  {rt:<7}{g[rt]:>4}  {100 * g[rt] / len(s):4.1f}%  "
          f"(95% interval {100 * lo:.1f} to {100 * hi:.1f})")
    gi = [r for r in s if r["system_category"] == "General inquiry"]
    gg = Counter(gold(r["label"], int(r["sensitive"])) for r in gi)
    p(f"Sample tickets the desk filed as General inquiry: {len(gi)}")
    p("  " + ", ".join(f"{rt} {gg[rt]}" for rt in ROUTES))
    sens = [r for r in s if r["sensitive"] == "1"]
    hid = Counter(r["system_category"] for r in sens)
    p(f"Disclosures inside routine tickets: {len(sens)}")
    p("  filed as " + ", ".join(
        f"{k} {v}" for k, v in hid.most_common(3)) + ", other "
      + str(sum(v for _, v in hid.most_common()[3:])))
    top = Counter(r["label"] for r in s).most_common(8)
    p("Largest categories in the sample:")
    for k, v in top:
        p(f"  {k:<9}{v:>4}  {TAX[k]['route']:<7}{TAX[k]['name']}")
    hes = [r for r in rows if r["division"] == "HES"
           and r["country"] == "CA"]
    pe = [r for r in s if r["label"] == "PAY-ERR"]
    pa = sum(r["division"] == "HES" and r["country"] == "CA"
             for r in pe)
    p(f"Hartwell Energy Services, Alberta: {len(hes):,} tickets "
      f"({100 * len(hes) / len(rows):.1f}%)")
    p(f"  in the sample: {pa} of {len(pe)} pay-error tickets")
    rec.note(sample_ids=[r["ticket_id"] for r in s],
             routes=dict(g), general_inquiry=dict(gg))
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
