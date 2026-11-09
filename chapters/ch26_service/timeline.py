"""Time to human, measured three ways (Chapter 26).

Book section: "Where the clock starts". A seeded, synthetic
month of AskHartwell conversations that needed a person, for
Hartwell's US, Canadian and UK employees, in two months:

  2027-09  before HS-01: the agent decides when to hand off,
           every hand-off goes to Quayfen tier 1 first, and
           the contract's clock is ticket to first response
           (an automatic acknowledgment counts)
  2028-01  after HS-01: the route rule and reader hand off at
           the first message, each lane has its own queue,
           and the clock is the employee's

Each conversation records four times: the first message
that asked for a person (or that a person had to take), the
ticket, the first response of any kind, and a named person's
first reply. Three clocks are computed from them:

  contract  ticket -> first response (SOW No. 7 report)
  ticket    ticket -> named person's first reply
  employee  first ask -> named person's first reply (HS-01)

The generator's parameters are written below, so a reader
can see what drives each number. No real person or ticket.

Run: HRAI_MODEL=no-model python -m chapters.ch26_service.timeline
"""
from __future__ import annotations

import random
import statistics as st

from hrai.llm import RunRecorder

LANES = ["care", "pay", "conduct", "leave", "adviser"]
# share of person-needed conversations by lane (both months)
MIX = {"care": 0.06, "pay": 0.17, "conduct": 0.04,
       "leave": 0.13, "adviser": 0.60}
TARGET = {"care": 10, "pay": 10, "conduct": 15, "leave": 15,
          "adviser": 15}
PERIODS = {
    "2027-09": {
        "n": 3120,
        # chance the agent answers instead of handing off, per
        # employee message, and minutes the employee spends
        # before asking again
        "deflect": {"care": 0.45, "pay": 0.55, "conduct": 0.40,
                    "leave": 0.60, "adviser": 0.30},
        "retry_min": (2, 7),
        # every lane queues at Quayfen first; sensitive lanes
        # are then passed to Denver or the country team
        "queue_min": {"care": (4, 22), "pay": (3, 20),
                      "conduct": (4, 22), "leave": (5, 26),
                      "adviser": (3, 18)},
        "transfer": {"care": (8, 40), "conduct": (8, 40),
                     "leave": (6, 30)},
        "auto_ack": True,
    },
    "2028-01": {
        "n": 3305,
        "deflect": {"care": 0.0, "pay": 0.03, "conduct": 0.0,
                    "leave": 0.04, "adviser": 0.05},
        "retry_min": (2, 7),
        "queue_min": {"care": (1, 12), "pay": (2, 15),
                      "conduct": (2, 18), "leave": (3, 30),
                      "adviser": (2, 24)},
        "transfer": {},
        "auto_ack": False,
    },
}


def tri(rng: random.Random, lo: float, hi: float) -> float:
    """Skewed toward the low end, with a tail toward hi."""
    return rng.triangular(lo, hi, lo + (hi - lo) * 0.2)


def month(period: str, seed: int = 26) -> list[dict]:
    p, rng = PERIODS[period], random.Random(f"{seed}{period}")
    rows = []
    for i in range(p["n"]):
        lane = rng.choices(LANES, [MIX[k] for k in LANES])[0]
        t = 0.0                       # first ask, in minutes
        tries = 0
        while tries < 4 and rng.random() < p["deflect"][lane]:
            tries += 1
            t += rng.uniform(*p["retry_min"])
        ticket = t + rng.uniform(0.2, 1.0)
        reply = ticket + tri(rng, *p["queue_min"][lane])
        if lane in p["transfer"]:
            reply += tri(rng, *p["transfer"][lane])
        first = ticket + 0.1 if p["auto_ack"] else reply
        rows.append({"id": f"{period}-{i:05d}", "lane": lane,
                     "asks": tries + 1, "ask": 0.0,
                     "ticket": ticket, "first": first,
                     "reply": reply})
    return rows


def clocks(rows: list[dict]) -> dict:
    return {
        "contract": [r["first"] - r["ticket"] for r in rows],
        "ticket": [r["reply"] - r["ticket"] for r in rows],
        "employee": [r["reply"] - r["ask"] for r in rows]}


def p90(xs: list[float]) -> float:
    return st.quantiles(xs, n=10)[-1]


def show(rec, period: str) -> dict:
    rows = month(period)
    c = clocks(rows)
    rec.print(f"== {period}: {len(rows)} conversations that"
              " needed a person")
    rec.print("  clock      median   p90   within 15 min")
    out = {}
    for k, xs in c.items():
        w = sum(x <= 15 for x in xs) / len(xs)
        out[k] = (st.median(xs), p90(xs), w)
        rec.print(f"  {k:<9} {st.median(xs):6.1f} {p90(xs):6.1f}"
                  f"   {w:6.1%}")
    again = sum(r["asks"] > 1 for r in rows)
    rec.print(f"  asked more than once: {again}"
              f" ({again / len(rows):.1%})")
    rec.print("  lane      n     employee p90   target  met")
    for lane in LANES:
        xs = [r["reply"] - r["ask"] for r in rows
              if r["lane"] == lane]
        q = p90(xs)
        rec.print(f"  {lane:<8} {len(xs):5d} {q:9.1f}"
                  f" {TARGET[lane]:9d}  "
                  + ("yes" if q <= TARGET[lane] else "no"))
    return out


def main() -> None:
    rec = RunRecorder("ch26", "time_to_human")
    for period in PERIODS:
        show(rec, period)
    print(rec.save())


if __name__ == "__main__":
    main()
