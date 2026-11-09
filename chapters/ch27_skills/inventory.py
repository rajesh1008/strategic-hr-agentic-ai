"""Chapter 27: inventory coverage on March 31, 2028 (no model).

Book section "Coverage that means something" and the
Scoreboard. ILLUSTRATIVE: the population is seeded and the
behavior rates below are planning assumptions, not
measurements. Coverage counts a profile only when it has at
least three confirmed entries (declared, evidenced from a
certificate or project record, or a suggestion the person
accepted); a profile with suggestions waiting does not count.

Live dates: US, CA, UK, AU and the Hyderabad center from
November 1, 2027; NL from January 10, 2028 (after the
ondernemingsraad's consent); DE not live (Betriebsrat).

Run:  HRAI_MODEL=no-model python -m chapters.ch27_skills.inventory
"""
from __future__ import annotations

import random

from hrai.llm import RunRecorder

from .population import ENTITIES, SEED, build

LIVE_WEEKS = {"US": 21, "CA": 21, "UK": 21, "AU": 21,
              "IN": 21, "NL": 11, "DE": 0}
OPT_OUT = .06          # switch suggestions off
ACCEPT = .64           # share of suggestions accepted
EVIDENCED = .9         # certificates and project roles load


def confirmed(e, weeks: int, rng: random.Random) -> int:
    if weeks == 0:
        return 0
    n = 0
    if rng.random() < EVIDENCED:
        n += rng.randint(0, 2)          # from records
    if rng.random() < min(.85, .25 + .03 * weeks):
        n += len(e.skills) // 2         # declared by the person
    return n


def main() -> None:
    rng = random.Random(SEED + 2)
    staff = build()
    rec = RunRecorder("ch27", "inventory")
    P = rec.print
    P("ILLUSTRATIVE (seeded; rates are assumptions)")
    P("entity  staff  live wks  3+ confirmed  opted out")
    tot = cov = out = 0
    sug = acc = 0
    for ent, size in ENTITIES:
        es = [e for e in staff if e.entity == ent]
        w = LIVE_WEEKS[ent]
        c = o = 0
        for e in es:
            if w and rng.random() < OPT_OUT:
                o += 1
                n = confirmed(e, w, rng)
            else:
                n = confirmed(e, w, rng)
                if w:
                    k = rng.randint(0, 4)
                    a = sum(rng.random() < ACCEPT
                            for _ in range(k))
                    sug += k
                    acc += a
                    n += a
            c += n >= 3
        tot += size
        cov += c
        out += o
        P(f"{ent:6s} {size:6,d} {w:9d} {c / size:13.1%}"
          f" {o / size:10.1%}")
        rec.note(entity=ent, staff=size, covered=c, opted=o)
    P(f"all    {tot:6,d} {'':9s} {cov / tot:13.1%}"
      f" {out / tot:10.1%}")
    P(f"suggestions {sug:,}, accepted {acc:,} "
      f"({acc / sug:.0%})")
    rec.save()


if __name__ == "__main__":
    main()
