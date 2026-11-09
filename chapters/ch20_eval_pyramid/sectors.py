"""Sector cases: the pyramid outside Hartwell.

Book sections: the Lakemont, Aurelia, Fieldnote and
Cobbleford-at-Quayfen cases. Every organization and number is
SYNTHETIC and drawn with a fixed seed, so each result is
reproducible. Each case shows one way an evaluation can pass
while the thing it should catch gets through.

Run: HRAI_MODEL=no-model python -m \\
     chapters.ch20_eval_pyramid.sectors
"""
from __future__ import annotations

import random

from hrai.llm import RunRecorder

# --- Lakemont Health: a rostering agent, tested on one day ---

NURSES = [  # id, unit credential, credential expiry (day)
    ("RN-01", "ICU", 99), ("RN-02", "ICU", 3),
    ("RN-03", "ICU", 99), ("RN-04", "ICU", 5),
    ("RN-05", "MED", 99), ("RN-06", "ICU", 99),
]


def fill(open_shifts, day0, roster):
    """The vendor's agent: first credentialed nurse with ten
    hours' rest. Defect: checks the credential on the day it
    proposes, not on the day of the shift."""
    out = []
    for day, unit, start in open_shifts:
        for nid, cred, exp in NURSES:
            last = roster.get(nid)
            rested = last is None or (day * 24 + start) - last \
                >= 10
            if cred == unit and exp > day0 and rested:
                roster[nid] = day * 24 + start + 12
                out.append((day, unit, nid, exp))
                break
    return out


def lakemont(rec):
    rng = random.Random(41)
    rec.print("Lakemont: rostering agent, open ICU shifts")
    for name, horizon in (("same-day cases", 1),
                          ("seven-day cases", 7)):
        bad = total = 0
        for _ in range(200):
            shifts = [(rng.randrange(horizon), "ICU",
                       rng.choice((7, 19)))
                      for _ in range(3)]
            for day, unit, nid, exp in fill(sorted(shifts), 0,
                                            {}):
                total += 1
                bad += exp <= day
        rec.print(f"  {name:<16} {total} proposals, "
                  f"{bad} by a nurse whose credential has"
                  f" lapsed by the shift")
        rec.note(case="lakemont", set=name, total=total,
                 lapsed=bad)


# --- Aurelia Telecom: a coaching judge, agreement by group ---

GROUPS = {  # group: (calls, judge agrees with QA lead)
    "Toronto, English": (420, 0.91),
    "Toronto, French": (160, 0.76),
    "Utrecht, Dutch": (300, 0.89),
    "Utrecht, English": (120, 0.83),
}


def aurelia(rec):
    rng = random.Random(7)
    rec.print("Aurelia: coaching judge vs QA leads, by group")
    agree = n = 0
    rows = []
    for g, (calls, p) in GROUPS.items():
        a = sum(rng.random() < p for _ in range(calls))
        agree, n = agree + a, n + calls
        rows.append((g, a, calls))
    rec.print(f"  all calls            {agree}/{n} "
              f"({100 * agree / n:.1f}%)")
    for g, a, calls in rows:
        rec.print(f"  {g:<20} {a}/{calls} "
                  f"({100 * a / calls:.1f}%)")
        rec.note(case="aurelia", group=g, agree=a, n=calls)


# --- Fieldnote: offline match quality vs who gets seen ---

def fieldnote(rec):
    """Offline metric: share of the top 120 who applied for an
    internal role last year. v2 adds recent platform activity,
    which predicts applying, and which people on leave lack."""
    rng = random.Random(11)
    rec.print("Fieldnote: mobility match v1 vs v2 (offline)")
    people = []
    for i in range(1200):
        leave = i % 10 == 0          # back from leave this year
        skill = rng.random()
        recent = 0.1 if leave else rng.random()
        applied = rng.random() < 0.15 + 0.5 * recent
        people.append((leave, skill, recent, applied))
    for ver, w in (("v1", 0.0), ("v2", 0.6)):
        top = sorted(people, key=lambda p: p[1] * (1 - w)
                     + p[2] * w, reverse=True)[:120]
        hit = sum(p[3] for p in top) / len(top)
        lv = sum(p[0] for p in top) / len(top)
        rec.print(f"  {ver}: top-120 applied last year "
                  f"{100 * hit:.1f}%; back from leave "
                  f"{100 * lv:.1f}% (of staff 10.0%)")
        rec.note(case="fieldnote", version=ver, hit=hit,
                 leave_share=lv)


# --- Cobbleford at Quayfen: whose evaluation counts ---

COBBLEFORD = {  # family: (cases, chance a run fails a case)
    "maker-checker": (8, (0.0,) * 6 + (0.5, 0.9)),
    "address": (10, (0.0,) * 10),
    "bank": (8, (0.0,) * 7 + (0.3,)),
    "refuse": (6, (0.0,) * 6),
}


def cobbleford(rec):
    rng = random.Random(180)
    rec.print("Cobbleford: provider report vs client"
              " golden set")
    tickets = 4000
    fcr = sum(rng.random() < 0.93 for _ in range(tickets))
    rec.print(f"  Quayfen monthly report: first-contact "
              f"resolution {fcr}/{tickets} "
              f"({100 * fcr / tickets:.1f}%)")
    runs = allk = n = 0
    rows = []
    for fam, (k, ps) in COBBLEFORD.items():
        ok3 = 0
        for p in ps:
            res = [rng.random() >= p for _ in range(3)]
            runs += sum(res)
            ok3 += all(res)
        allk, n = allk + ok3, n + k
        rows.append((fam, ok3, k))
    rec.print(f"  Cobbleford golden set: pass@1 {runs}/{3 * n}"
              f" ({100 * runs / (3 * n):.0f}%); pass^3 "
              f"{allk}/{n}")
    for fam, ok3, k in rows:
        rec.print(f"    {fam:<14} {ok3}/{k} pass all 3 runs")
        rec.note(case="cobbleford", family=fam, pass3=ok3,
                 cases=k)


def main() -> None:
    rec = RunRecorder("ch20", "sectors")
    lakemont(rec)
    aurelia(rec)
    fieldnote(rec)
    cobbleford(rec)
    print(rec.save())


if __name__ == "__main__":
    main()
