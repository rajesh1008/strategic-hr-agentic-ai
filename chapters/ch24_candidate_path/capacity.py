"""Chapter 24: can people read 2,000 applications a month?

Book section "Screening 2,000 applications a month". A
deterministic calculator (no model): recruiter hours a month
for one volume under four screening designs. The lane shares
are Hartwell's routing line A04 v1.0 on 400 double-read
applications (Chapter 16: confirm 111, review 71, fail
closed 218). The read times are Hartwell's measured minutes
(Chapter 4: 3.88 plain, 2.94 with the evidence shown).
Constants marked ILLUSTRATIVE are planning assumptions.

Run:  HRAI_MODEL=no-model python -m chapters.ch24_candidate_path.capacity
"""
from __future__ import annotations

from hrai.llm import RunRecorder

READ = 3.88          # minutes, full read (ch04, measured)
EVIDENCE = 2.94      # minutes, read with evidence shown (ch04)
CONFIRM = 1.0        # ILLUSTRATIVE: confirm one flagged line
OPEN_SHARE = 0.10    # confirm lane: 1 in 10 opened in full
KNOCKOUT = 0.5       # ILLUSTRATIVE: confirm a rule knock-out
LANES = {"confirm": 111, "review": 71, "fail_closed": 218}
RECON = 0.015        # ILLUSTRATIVE: reconsiderations per rejection
RECON_MIN = 20.0     # ILLUSTRATIVE: minutes per reconsideration
TABLE_HOURS = 6.0    # ILLUSTRATIVE: monthly per-step table
HOURS_PER_FTE = 100  # ILLUSTRATIVE: screening hours a month


def a04_minutes(n: float) -> float:
    """Minutes for n applications through the A04 lanes."""
    tot = sum(LANES.values())
    c = n * LANES["confirm"] / tot
    r = n * LANES["review"] / tot
    f = n * LANES["fail_closed"] / tot
    return c * (CONFIRM + OPEN_SHARE * READ) + r * READ \
        + f * EVIDENCE


def designs(n: int, knock: float) -> list[tuple]:
    """(name, minutes, allowed, why) for n applications a
    month, where knock is the share a written rule removes
    (right to work, license, minimum age)."""
    rej = n * 0.55
    oversight = rej * RECON * RECON_MIN + TABLE_HOURS * 60
    return [
        ("read every one in full", n * READ + oversight,
         True, "the baseline"),
        ("model rejects, people read the rest",
         n * 0.45 * READ, False,
         "a rejection with no named person (Keep step)"),
        ("A04 lanes on every one", a04_minutes(n) + oversight,
         True, "every rejection read by a named recruiter"),
        ("rule knock-outs, then A04 lanes",
         n * knock * KNOCKOUT + a04_minutes(n * (1 - knock))
         + oversight, True, "knock-outs need their own table"),
    ]


def main(n: int = 2000, knock: float = 0.30) -> None:
    rec = RunRecorder("ch24", "capacity")
    rec.print(f"{n} applications a month; rule knock-outs "
              f"{knock:.0%}")
    rec.print(f"{'design':<37}{'hours':>6}{'FTE':>6}  allowed")
    base = None
    for name, mins, ok, why in designs(n, knock):
        h = mins / 60
        base = base or h
        rec.print(f"{name:<37}{h:>6.0f}{h / HOURS_PER_FTE:>6.2f}"
                  f"  {'yes' if ok else 'NO'}")
        rec.print(f"{'':<4}{why}; saves {1 - h / base:.0%}")
    for vol in (500, 2000, 9500):
        h = designs(vol, knock)[3][1] / 60
        rec.print(f"at {vol:>5} a month, knock-outs then lanes:"
                  f" {h:.0f} h, {h / HOURS_PER_FTE:.1f} FTE")
    rec.note(lanes=LANES, read=READ, evidence=EVIDENCE)
    print(rec.save())


if __name__ == "__main__":
    main()
