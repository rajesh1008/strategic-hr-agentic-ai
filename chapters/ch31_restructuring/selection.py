"""Chapter 31: the selection-criteria check.

Book section "The selection-criteria check". Eight checks
(SC-1 to SC-8) on a selection matrix before anyone is
scored, then the impact table on the scored pool before any
result is final. The pool is synthetic (seed 31).

The checks read the matrix, not the people: a matrix can
fail before a single score exists. The impact table uses
the chapter 7 code, with "selected" meaning retained.
"""
from __future__ import annotations

import random

from chapters.ch07_adverse_impact.impact import render, table

from .model import load

CHECKS = {
    "SC-1": "every criterion reads a named record",
    "SC-2": "protected absence is excluded",
    "SC-3": "no proxy inputs (shifts, hours, age, scores)",
    "SC-4": "only live disciplinary records count",
    "SC-5": "every person has every input",
    "SC-6": "tie-break is not length of service alone",
    "SC-7": "pool and criteria consulted before scoring",
    "SC-8": "people score; an agent only retrieves",
}


def pool(n: int = 120, seed: int = 31) -> list[dict]:
    """Synthetic Leeds line operatives."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        woman = rng.random() < 0.40
        age = rng.randint(21, 63)
        pt = rng.random() < (0.30 if woman else 0.06)
        dis = rng.random() < 0.10
        ten = min(age - 18, rng.randint(0, 30))
        skills = min(6, max(0, round(rng.gauss(3, 1.3)
                                     + ten / 25)))
        view = skills / 6 * 4 + 1 + rng.gauss(0, 0.5)
        view -= 0.8 if pt else 0
        view -= 0.5 if age >= 55 else 0
        other = max(0, round(rng.gauss(6, 4)))
        prot = 0
        if dis:
            prot += rng.randint(8, 20)
        if woman and age < 42 and rng.random() < 0.15:
            prot += rng.randint(60, 140)
        if rng.random() < 0.10:
            prot += rng.randint(3, 10)
        live = 1 if rng.random() < 0.06 else 0
        old = 1 if rng.random() < min(0.5, ten / 40) else 0
        out.append({
            "id": f"BWL-31{i:03d}",
            "sex": "Female" if woman else "Male",
            "age": age,
            "age_band": ("under 40" if age < 40 else
                         "40-49" if age < 50 else "50+"),
            "hours": "part-time" if pt else "full-time",
            "disability": "declared" if dis else "none",
            "tenure": ten,
            "certified_skills": skills,
            "qualifications": rng.choice([0, 0, 1, 1, 2]),
            "supervisor_view": max(1, min(5, round(view))),
            "all_shifts": (rng.random() < 0.12) if pt
            else (rng.random() < 0.85),
            "absence_other": other,
            "absence_all": other + prot,
            "warnings_live": live,
            "warnings_all": live + old,
            "tiebreak": rng.random(),
        })
    return out


def score(p: dict, m: dict) -> float:
    s = 0.0
    for c in m["criteria"]:
        v, w = p[c["field"]], c["weight"]
        if c["field"].startswith("absence"):
            s += w * max(0.0, 1 - v / 30)
        elif c["field"].startswith("warnings"):
            s += w * max(0.0, 1 - v / 2)
        elif c["field"] == "all_shifts":
            s += w if v else 0
        elif c["field"] == "supervisor_view":
            s += w * (v - 1) / 4
        elif c["field"] == "certified_skills":
            s += w * v / 6
        elif c["field"] == "qualifications":
            s += w * v / 2
    return round(s, 1)


def select(ppl: list[dict], m: dict, k: int
           ) -> tuple[set[str], int]:
    """Lowest k scores go. Returns IDs and the number of
    people tied at the cut line (sent to the panel in v2)."""
    def key(p):
        s = score(p, m)
        if m["tie_break"][0] == "tenure":
            return (s, p["tenure"], p["tiebreak"])
        return (s, p["certified_skills"], p["tiebreak"])
    ranked = sorted(ppl, key=key)
    cut = score(ranked[k - 1], m)
    tied = sum(1 for p in ppl if score(p, m) == cut)
    return {p["id"] for p in ranked[:k]}, tied


def checks(m: dict, cfg: dict, ppl: list[dict]
           ) -> dict[str, str]:
    """SC-1 to SC-8 on one matrix: PASS, WARN or FAIL."""
    cs = m["criteria"]
    r = {}
    r["SC-1"] = ("FAIL" if any(c["source"] != "record"
                               for c in cs) else "PASS")
    r["SC-2"] = ("FAIL" if any(c.get("counts") == "all"
                               for c in cs) else "PASS")
    used = {c["field"] for c in cs}
    r["SC-3"] = ("FAIL" if used & set(cfg["proxies"])
                 else "PASS")
    r["SC-4"] = ("FAIL" if any(c.get("live_only") is False
                               for c in cs) else "PASS")
    gaps = sum(1 for p in ppl for f in used
               if p.get(f) is None)
    r["SC-5"] = "FAIL" if gaps else "PASS"
    r["SC-6"] = ("WARN" if m["tie_break"] == ["tenure"]
                 else "PASS")
    r["SC-7"] = ("PASS" if m["consulted_on"] < m["scored_on"]
                 else "FAIL")
    r["SC-8"] = ("PASS" if m["agent_mode"] in
                 ("none", "retrieve") else "FAIL")
    return r


def impact(ppl: list[dict], gone: set[str], attr: str
           ) -> list[str]:
    rows, miss = table(ppl, lambda p: p[attr],
                       lambda p: p["id"] not in gone)
    return render(rows, f"retained by {attr}", miss)


def main() -> None:
    from hrai.llm import RunRecorder
    cfg = load("matrices.yaml")
    rec = RunRecorder("ch31", "selection")
    ppl = pool(cfg["pool"]["size"])
    k = cfg["pool"]["select"]
    rec.print(f"{cfg['pool']['site']} (synthetic): pool "
              f"{len(ppl)}, roles to go {k}")
    for v in ("v1", "v2"):
        m = cfg[v]
        res = checks(m, cfg, ppl)
        rec.print("")
        items = [f"{c}:{s}" for c, s in res.items()]
        rec.print(f"matrix {v}: " + " ".join(items[:4]))
        rec.print("           " + " ".join(items[4:]))
        for c, s in res.items():
            if s != "PASS":
                rec.print(f"  {c} {s} {CHECKS[c]}")
        gone, tied = select(ppl, m, k)
        rec.print(f"  selected {len(gone)}; tied at the cut "
                  f"line {tied}")
        for attr in ("sex", "age_band", "hours",
                     "disability"):
            for line in impact(ppl, gone, attr):
                rec.print(line)
        rec.note(matrix=v, checks=res, tied=tied,
                 selected=sorted(gone))
    print(rec.save())


if __name__ == "__main__":
    main()
