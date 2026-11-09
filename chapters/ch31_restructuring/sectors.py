"""Chapter 31: the sector cases (all synthetic).

Book sections "Selecting for retraining, not only for exit"
(Hartwell Energy Services), "Cobbleford's oversight hours"
and "Hyderabad: a transition with no retrenchment".
"""
from __future__ import annotations

import random

from chapters.ch07_adverse_impact.impact import render, table

HOURS_FTE = 1720   # chapter 2: 103,200 hours = 60.0 FTE


def crew(n: int = 64, seed: int = 3131) -> list[dict]:
    """Plant technicians at a client gas plant in Texas."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        age = rng.randint(24, 62)
        agility = rng.gauss(70 - (age - 40) * 0.6, 9)
        out.append({"id": f"HES-31{i:03d}", "age": age,
                    "band": "40+" if age >= 40 else "under 40",
                    "agility": agility,
                    "lottery": rng.random()})
    return out


def retrain_v1(c: list[dict], places: int) -> set[str]:
    """Manager's ranking: years to 65 and a vendor
    'learning agility' score, half each."""
    key = lambda p: 0.5 * (65 - p["age"]) / 41 + \
        0.5 * p["agility"] / 100
    top = sorted(c, key=key, reverse=True)[:places]
    return {p["id"] for p in top}


def retrain_v2(c: list[dict], places: int) -> set[str]:
    """Everyone eligible; a lottery sets the cohort order.
    The second cohort follows six months later."""
    first = sorted(c, key=lambda p: p["lottery"])[:places]
    return {p["id"] for p in first}


def energy(rec) -> None:
    c, places = crew(), 40
    rec.print("Hartwell Energy Services plant crew (synthetic):"
              f" {len(c)}")
    rec.print(f"substation retraining places, cohort 1: "
              f"{places}")
    for name, fn in (("v1 ranking", retrain_v1),
                     ("v2 lottery, everyone eligible",
                      retrain_v2)):
        got = fn(c, places)
        rows, miss = table(c, lambda p: p["band"],
                           lambda p: p["id"] in got)
        rec.print("")
        for line in render(rows, f"cohort 1 place, {name}",
                           miss):
            rec.print(line)
    rec.print("")
    rec.print(f"v2 offered a place in cohort 1 or 2: "
              f"{len(c)} of {len(c)}")


def cobbleford(rec) -> None:
    moved, review = 22, 0.15
    keep = round(moved * review)
    rec.print("Cobbleford Edinburgh HR operations (synthetic)")
    rec.print(f"roles' worth of work moving to Manila: {moved}")
    rec.print(f"review of Manila output kept in Edinburgh: "
              f"{moved * review:.1f} roles -> {keep}")
    rec.print(f"proposed Edinburgh redundancies: "
              f"{moved - keep} (s.188 threshold 20)")


def hyderabad(rec) -> None:
    staff, share, review, attr = 260, 0.20, 0.15, 0.24
    absorbed = staff * share
    kept = absorbed * review
    leavers = staff * attr * 1.5
    platform = 15200 / HOURS_FTE
    rec.print("Hyderabad HR operations (synthetic)")
    rec.print(f"staff {staff}; work absorbed {absorbed:.1f} "
              f"roles' worth")
    rec.print(f"review hours kept {kept:.1f}; net "
              f"{absorbed - kept:.1f}")
    rec.print(f"expected leavers in 6 quarters at {attr:.0%}: "
              f"{leavers:.0f}")
    rec.print(f"agent-platform operations (ch02): "
              f"{platform:.1f} FTE")
    rec.print(f"retrenchments needed: "
              f"{max(0, round(absorbed - kept - leavers))}")


def main() -> None:
    from hrai.llm import RunRecorder
    rec = RunRecorder("ch31", "sectors")
    energy(rec)
    rec.print("")
    cobbleford(rec)
    rec.print("")
    hyderabad(rec)
    print(rec.save())


if __name__ == "__main__":
    main()
