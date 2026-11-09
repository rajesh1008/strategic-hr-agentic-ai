"""Chapter 30: the sector cases in numbers (illustrative).

Book sections "Hollis: the warnings result" and "Lakemont:
a grievance about leave". Seeded synthetic event logs; the
counts are illustrative, not measured at any real employer.

  hollis    attendance warnings and dismissals at the
            Hollis plants (synthetic), second half of 2026
            (before the Chapter 11 controls) against the
            second half of 2027 (after)
  lakemont  registered nurse attendance warnings at
            Lakemont (synthetic) recounted without absences
            coded as protected leave

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch30_relations.sectors
"""
from __future__ import annotations

import random

from hrai.llm import RunRecorder

SEED = 30


def hollis(rng: random.Random) -> list[dict]:
    plan = {"2026 H2": (188, 29, 11, 4),
            "2027 H2": (141, 6, 7, 0)}
    rows = []
    for half, (w, rw, d, rd) in plan.items():
        flags = [1] * rw + [0] * (w - rw)
        rng.shuffle(flags)
        dflags = [1] * rd + [0] * (d - rd)
        rng.shuffle(dflags)
        rows.append({"half": half, "warnings": len(flags),
                     "rescinded": sum(flags),
                     "dismissals": len(dflags),
                     "reversed": sum(dflags)})
    return rows


def lakemont(rng: random.Random) -> dict:
    nurses = []
    for n in range(14):
        points = rng.randint(6, 9)
        fml = 0
        if n < 6:
            fml = rng.randint(1, 3)
            points = max(points, 6)
        nurses.append((points, fml))
    over = [(p, f) for p, f in nurses if f]
    below = [(p, f) for p, f in over if p - f < 6]
    return {"warnings": len(nurses), "with_fml": len(over),
            "below_without": len(below)}


def main() -> None:
    rec = RunRecorder("ch30", "sectors")
    rng = random.Random(SEED)
    rec.print("== Hollis attendance (illustrative, seeded)")
    rec.print("  half     warnings rescinded  share"
              "  dismissals reversed")
    for r in hollis(rng):
        rec.print(f"  {r['half']}  {r['warnings']:>8}"
                  f" {r['rescinded']:>9} {r['rescinded'] / r['warnings']:>6.1%}"
                  f" {r['dismissals']:>11} {r['reversed']:>8}")
    lk = lakemont(rng)
    rec.print("== Lakemont RN attendance warnings (illustrative)")
    rec.print(f"  warnings {lk['warnings']}; counting FML-I"
              f" absences {lk['with_fml']}; below the 6-point"
              f" threshold without them {lk['below_without']}")
    rec.save()


if __name__ == "__main__":
    main()
