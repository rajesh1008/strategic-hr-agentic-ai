"""Chapter 29: payroll change controls before release.

Book section "Payroll change controls". Hartwell UK runs its
own payroll in Manchester. Before the January 2028 run is
released, every line is compared with December and with the
approved change records. Five checks, all code; a held line
goes to a named person, and nothing is released by an agent.
The faults planted in the fixture are the kinds payroll
teams report; the counts are synthetic.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch29_pay.variance
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from hrai.llm import RunRecorder

BANDS = {"G3": (12.50, 16.00), "G4": (15.00, 20.50),
         "G5": (18.50, 26.50)}
CHECKS = {
    "V-1": "net up or down 15%+ with no approved change",
    "V-2": "paid after the leaving date",
    "V-3": "bank changed in 30 days and net up 10%+",
    "V-4": "hourly rate outside the grade band",
    "V-5": "change approved by the person who asked",
    "V-6": "the same allowance code twice in one run",
}
V1 = ["V-1", "V-2", "V-3", "V-4", "V-5"]
V2 = V1 + ["V-6"]


@dataclass
class Line:
    emp: str
    grade: str
    rate: float
    prev_net: float
    net: float
    change: str | None = None    # approved change record
    maker: str | None = None
    checker: str | None = None
    left: bool = False
    bank_new: bool = False
    dup: bool = False            # allowance code twice
    fault: str | None = None     # planted, for the test


def run_lines() -> list[Line]:
    rng = random.Random(2928)
    out = []
    for i in range(1, 3201):
        g = rng.choice(["G3", "G4", "G5"])
        lo, hi = BANDS[g]
        rate = round(rng.uniform(lo + 0.3, hi - 0.3), 2)
        prev = round(rate * 162.5 * 0.78, 2)
        net = round(prev * rng.uniform(0.97, 1.03), 2)
        out.append(Line(f"HW-03{i:04d}", g, rate, prev, net))
    for ln in rng.sample(out, 46):         # January pay review
        ln.net = round(ln.prev_net * 1.18, 2)
        ln.change, ln.maker, ln.checker = (
            "PCR-2801", "HR-MAN-ADV-07", "REW-MAN-02")
    pick = rng.sample([l for l in out if not l.change], 12)
    pick[0].change, pick[0].maker, pick[0].checker = (
        "PCR-2814", "REW-MAN-02", "REW-MAN-02")
    pick[0].net = round(pick[0].prev_net * 1.22, 2)
    pick[0].fault = "self-approved change"
    for ln in pick[1:4]:                   # allowance twice
        ln.net = round(ln.net + 310.00, 2)
        ln.dup, ln.fault = True, "allowance paid twice"
    pick[4].left = True                    # leaver still paid
    pick[4].fault = "leaver paid"
    pick[5].rate = round(pick[5].rate * 10, 2)   # 165.0 slip
    pick[5].fault = "rate keyed x10"
    for ln in pick[6:8]:                   # bank change + jump
        ln.bank_new = True
        ln.net = round(ln.prev_net * 1.31, 2)
        ln.fault = "new bank and a jump"
    for ln in pick[8:12]:                  # bank change only
        ln.bank_new = True
    return out


def hold(ln: Line, checks=V2) -> list[str]:
    why = []
    move = abs(ln.net - ln.prev_net) / ln.prev_net
    if move >= 0.15 and not ln.change:
        why.append("V-1")
    if ln.left:
        why.append("V-2")
    if ln.bank_new and (ln.net - ln.prev_net) / ln.prev_net \
            >= 0.10:
        why.append("V-3")
    lo, hi = BANDS[ln.grade]
    if not lo <= ln.rate <= hi:
        why.append("V-4")
    if ln.change and ln.maker == ln.checker:
        why.append("V-5")
    if ln.dup:
        why.append("V-6")
    return [w for w in why if w in checks]


def main() -> None:
    rec = RunRecorder("ch29", "variance")
    lines = run_lines()
    faults = [l for l in lines if l.fault]
    rec.print("Hartwell UK payroll, January 2028, before "
              "release")
    rec.print(f"lines {len(lines)}; approved changes "
              f"{sum(1 for l in lines if l.change)}; planted "
              f"faults {len(faults)}")
    for name, checks in (("checks v1", V1), ("checks v2", V2)):
        held = {l.emp: hold(l, checks) for l in lines
                if hold(l, checks)}
        found = sum(l.emp in held for l in faults)
        rec.print(f"{name}: held {len(held)}, faults found "
                  f"{found} of {len(faults)}, false holds "
                  f"{len(held) - found}")
        for l in faults:
            if l.emp not in held:
                rec.print(f"  missed {l.emp} {l.fault}")
        rec.note(version=name, held=held, found=found)
    for cid, text in CHECKS.items():
        n = sum(cid in hold(l) for l in lines)
        rec.print(f"  {cid} {text}: {n}")
    rec.print("held lines to the UK payroll manager; V-3 lines"
              " also to payroll operations for a callback")
    print(rec.save())


if __name__ == "__main__":
    main()
