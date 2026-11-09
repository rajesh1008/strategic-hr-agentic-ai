"""Chapter 7: the sector cases (no model).

Book sections on Crossfield Staffing (a New York City bias
audit of a client's step), Cobbleford Bank (24 small slices and
one alarming ratio) and Pennant Stores (an intersection that
the single-axis tables hide).

Run:  HRAI_MODEL=no-model python -m chapters.ch07_adverse_impact.sectors
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from hrai.llm import REPO, RunRecorder

from . import impact as ai
from .make_data import load

YES = lambda k: (lambda r: r[k] == "Y")  # noqa: E731


def crossfield(rec, out) -> None:
    rows = load("crossfield-nyc.csv")
    rec.print(f"== Crossfield: client assessment, New York City,"
              f" {len(rows)} applicants")
    cut = statistics.median(int(r["score"]) for r in rows)
    for name, g in (("sex", lambda r: r["sex"]),
                    ("race/ethnicity",
                     lambda r: r["race_ethnicity"]),
                    ("sex & race/ethnicity",
                     ai.intersect("sex", "race_ethnicity"))):
        for kind, sel in (
                ("selection", YES("selected")),
                ("scoring", lambda r: int(r["score"]) > cut)):
            t, miss = ai.table(rows, g, sel, min_share=0.02)
            title = f"-- {name}, {kind} rate"
            for line in ai.render(t, title, miss):
                rec.print(line)
            out[f"crossfield|{name}|{kind}"] = [
                ai.as_dict(r) for r in t]
    rec.print(f"median score {cut:g}; minimum share 2%")
    rec.print()


def calder(rec, out) -> None:
    rows = load("calder-tellers.csv")
    rec.print(f"== Cobbleford Bank: branch-teller test, "
              f"{len(rows)} applicants, 2026")
    age = lambda r: "40+" if r["age_40_plus"] == "Y" \
        else "under 40"  # noqa: E731
    slices = []
    for q in sorted({r["quarter"] for r in rows}):
        for reg in sorted({r["region"] for r in rows}):
            s = [r for r in rows if r["quarter"] == q
                 and r["region"] == reg]
            t, _ = ai.table(s, age, YES("passed"))
            older = next(x for x in t if x.group == "40+")
            slices.append(dict(slice=f"{reg} {q}", n=len(s),
                               n_older=older.n,
                               ratio=older.ratio, p=older.p,
                               flags=older.flags))
    below = [s for s in slices if "<.8" in s["flags"]
             or "AI" in s["flags"]]
    sig = [s for s in slices if (s["p"] or 1) < ai.ALPHA]
    worst = min(slices, key=lambda s: s["ratio"])
    rec.print(f"slices: {len(slices)}; 40+ below 0.80 in "
              f"{len(below)}; significant in {len(sig)}")
    rec.print(f"worst: {worst['slice']}, n={worst['n']} "
              f"(40+ {worst['n_older']}), ratio "
              f"{worst['ratio']:.2f}, p={worst['p']:.3f} "
              f"{' '.join(worst['flags'])}")
    w = [r for r in rows if f"{r['region']} {r['quarter']}"
         == worst["slice"]]
    for s, title in ((w, f"-- {worst['slice']}"),
                     (rows, "-- all of 2026")):
        t, miss = _t(s, age)
        for line in ai.render(t, title, miss):
            rec.print(line)
    out["calder|slices"] = slices
    out["calder|pooled"] = [ai.as_dict(r)
                            for r in _t(rows, age)[0]]
    rec.print()


def _t(rows, g):
    t, miss = ai.table(rows, g, YES("passed"))
    return t, miss


def pennant(rec, out) -> None:
    rows = load("pennant-associates.csv")
    words = {"F": "women", "M": "men", "Y": "40+",
             "N": "under 40"}
    for r in rows:
        r["sx"] = words.get(r["sex"], r["sex"])
        r["ag"] = words.get(r["age_40_plus"], r["age_40_plus"])
    rec.print(f"== Pennant: work-style test, {len(rows)} "
              f"applicants (US and Canada)")
    for name, g in (("sex", lambda r: r["sx"]),
                    ("age", lambda r: r["ag"]),
                    ("sex & age", ai.intersect("sx", "ag"))):
        t, miss = ai.table(rows, g, YES("passed"))
        for line in ai.render(t, f"-- {name}", miss):
            rec.print(line)
        out[f"pennant|{name}"] = [ai.as_dict(r) for r in t]
    for c in ("US", "Canada"):
        s = [r for r in rows if r["country"] == c]
        t, miss = ai.table(s, ai.intersect("sx", "ag"),
                           YES("passed"))
        for line in ai.render(t, f"-- sex & age, {c}", miss):
            rec.print(line)
    rec.print()


def main() -> None:
    rec = RunRecorder("ch07", "sectors")
    out: dict = {}
    crossfield(rec, out)
    calder(rec, out)
    pennant(rec, out)
    path = Path(rec.save())
    side = path.with_name(path.name.split("-")[0]
                          + ".tables.json")
    side.write_text(json.dumps(out, indent=1) + "\n")
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
