"""Two sector models for the service chapter (synthetic).

Book sections: "Quayfen: what the contract counts" and
"Ashby & Lowe: one inbox, one person".

1. Quayfen tier 1. When the agent answers the easy contacts,
   fewer contacts reach the people, but each one is harder
   and longer. Seats follow workload and the service target,
   not contacts. Erlang C gives the people needed in the peak
   hour for a target such as "80% answered in 60 seconds"
   or "90% get a named person within 10 minutes".
2. Ashby & Lowe. Every hand-off goes to one named person.
   Replay two weeks in which she is on leave, with and
   without a named deputy.

Run: HRAI_MODEL=no-model python -m chapters.ch26_service.sectors
"""
from __future__ import annotations

import math
import random

from hrai.llm import RunRecorder


def erlang_c(n: int, a: float) -> float:
    """Probability that a contact waits, n people, a erlangs
    (Erlang B by recursion, then C; safe for large n)."""
    if n <= a:
        return 1.0
    b = 1.0
    for k in range(1, n + 1):
        b = a * b / (k + a * b)
    return n * b / (n - a * (1 - b))


def people_for(rate_h: float, aht_min: float, target_s: float,
               share: float) -> int:
    """Fewest people so that `share` of contacts start within
    target_s seconds, at rate_h contacts an hour."""
    a = rate_h * aht_min / 60
    n = max(1, math.ceil(a))
    while True:
        wait = erlang_c(n, a) * math.exp(
            -(n - a) * target_s / (aht_min * 60))
        if 1 - wait >= share:
            return n
        n += 1


# Share of a day's contacts in each of the 16 open hours,
# 06:00 to 22:00 Eastern, North America and the UK together.
PROFILE = [2, 4, 7, 9, 10, 9, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2]
DAYS = 21.7        # working days a month
PAID = 173.0       # paid hours per seat a month
SHRINK = 0.30      # leave, training, coaching, breaks


def seats(name, contacts, aht, target_s, share, rec):
    day = contacts / DAYS
    staffed = sum(people_for(day * w / sum(PROFILE), aht,
                             target_s, share)
                  for w in PROFILE)
    hours = contacts * aht / 60
    s = math.ceil(staffed * DAYS / (PAID * (1 - SHRINK)))
    rec.print(f"  {name:<32} {contacts:>8,} {aht:>5.1f}"
              f" {hours:>7,.0f} {s:>6}")
    return s


def quayfen(rec) -> None:
    rec.print("== Quayfen tier 1 on the Hartwell contract"
              " (synthetic, one month)")
    rec.print(f"  {'case':<32} {'contacts':>8} {'AHT':>5}"
              f" {'hours':>7} {'seats':>6}")
    old, new = 184_200, 146_100
    a = seats("Sep 2027, 80% in 60 s", old, 13.5, 60, 0.80,
              rec)
    seats("Sep 2027, 90% named in 10 min", old, 13.5, 600,
          0.90, rec)
    b = seats("2028 plan, 80% in 60 s", new, 16.2, 60, 0.80,
              rec)
    c = seats("2028 plan, 90% named in 10 min", new, 16.2,
              600, 0.90, rec)
    rec.print(f"  contacts fall {100 * (1 - new / old):.1f}%;"
              f" seats fall {100 * (1 - b / a):.1f}% on the old"
              f" target, {100 * (1 - c / a):.1f}% on the new one")


def ashby(rec) -> None:
    rng = random.Random(2610)
    days = 10                       # two working weeks
    arrivals = [rng.randint(3, 9) for _ in range(days)]
    rec.print("== Ashby & Lowe: 410 staff, every hand-off to"
              " Rachel Okafor (synthetic)")
    rec.print(f"  hand-offs in two weeks of her leave:"
              f" {sum(arrivals)}")
    for label, deputy in (("no deputy", False),
                          ("named deputy", True)):
        waits = []
        for d, k in enumerate(arrivals):
            for _ in range(k):
                if deputy:
                    waits.append(rng.uniform(0.2, 4.0))
                else:   # waits until she is back on day 11
                    waits.append((days - d) * 8.0
                                 + rng.uniform(0, 2))
        waits.sort()
        p90 = waits[int(0.9 * len(waits))]
        rec.print(f"  {label:<13} median {waits[len(waits) // 2]:>5.1f}"
                  f" working hours, p90 {p90:>5.1f}")


def main() -> None:
    rec = RunRecorder("ch26", "sectors")
    quayfen(rec)
    ashby(rec)
    print(rec.save())


if __name__ == "__main__":
    main()
