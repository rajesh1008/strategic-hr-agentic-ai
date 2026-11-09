"""Four sector cases as controlled actions (no model).

Book sections: "Cobbleford Bank", "Crossfield Staffing",
"Pennant Stores" and "Ghafline Facilities". Each case is a
seeded synthetic log run through deterministic checks:

- Cobbleford Bank: segregation-of-duties checks over a year
  of bank-detail changes (maker, checker, callback).
- Crossfield Staffing: one weekly cycle of timesheet
  corrections, split by whether pay has already run.
- Pennant Stores: one week of shift swaps against the
  overtime threshold where each store is.
- Ghafline Facilities: a WPS correction file run as
  controlled actions, settled by line status.

Every organization, person and number here is synthetic.
Run: python -m chapters.ch14_controlled_actions.sectors
"""
from __future__ import annotations

import random
from collections import Counter

from hrai.llm import RunRecorder


def cobbleford(rec) -> None:
    rng = random.Random(1401)
    log = []
    for i in range(1460):
        mt = rng.choices(["MNL-Q-07", "MNL-Q-09", "CHA-HR",
                          "EDI-HR"], [32, 28, 26, 14])[0]
        offshore = mt.startswith("MNL")
        ct = (mt if offshore and rng.random() < 0.38
              else rng.choice(["CHA-PAY", "EDI-PAY"]))
        maker = f"{mt}-{rng.randint(1, 30):02d}"
        checker = (maker if rng.random() < 0.006
                   else f"{ct}-{rng.randint(31, 60):02d}")
        log.append({
            "maker": maker, "mt": mt, "checker": checker,
            "ct": ct,
            "callback": rng.random() > (0.09 if offshore
                                        else 0.03),
            "secs": int(rng.expovariate(1 / 95)) + 4,
            "phone_new": rng.random() < 0.011})
    rules = {
        "SOD-1 checker is the maker":
            lambda r: r["checker"] == r["maker"],
        "SOD-2 checker in maker's team":
            lambda r: r["ct"] == r["mt"]
            and r["checker"] != r["maker"],
        "SOD-3 no callback to number on file":
            lambda r: not r["callback"],
        "SOD-4 approved in under 20 s":
            lambda r: r["secs"] < 20,
        "SOD-5 phone changed in prior 30 d":
            lambda r: r["phone_new"],
    }
    rec.print("== Cobbleford Bank: 2026 bank-detail changes")
    off = sum(1 for r in log if r["mt"].startswith("MNL"))
    rec.print(f"changes: {len(log)} (keyed at Quayfen: {off})")
    for name, f in rules.items():
        n = sum(1 for r in log if f(r))
        rec.print(f"  {name:<36} {n:>4}")
    hard = [r for r in log if r["checker"] == r["maker"]
            or (r["ct"] == r["mt"]) or not r["callback"]]
    rec.print(f"breaking SOD-1, 2 or 3: {len(hard)}")
    both = sum(1 for r in log if r["phone_new"]
               and not r["callback"])
    rec.print(f"phone changed and no callback: {both}")


def crossfield(rec) -> None:
    rng = random.Random(1402)
    paths = Counter()
    awr = 0
    for i in range(420):
        uk = rng.random() < 0.35
        after_cutoff = rng.random() < 0.22
        zero_week = uk and rng.random() < 0.04
        approver = rng.random() > 0.07
        if after_cutoff:
            paths["after pay ran: adjustment"] += 1
        elif approver:
            paths["before cutoff: edit"] += 1
        else:
            paths["held: no client approver"] += 1
        if zero_week:
            awr += 1
    rec.print("== Crossfield Staffing: one weekly cycle")
    rec.print("timesheet corrections: 420")
    for k, v in sorted(paths.items()):
        rec.print(f"  {k:<30} {v:>4}")
    rec.print(f"  UK week's only hours change     {awr:>4}"
              " (to compliance)")


OT = {"ON": 44, "OH": 40, "MI": 40}     # hours a week [VERIFY]


def pennant(rec) -> None:
    rng = random.Random(1403)
    stores = {"Toronto 014": "ON", "Ottawa 022": "ON",
              "Columbus 207": "OH", "Detroit 231": "MI"}
    res = Counter()
    vendor_ot = 0
    for i in range(240):
        st = rng.choice(list(stores))
        cap = OT[stores[st]]
        qualified = rng.random() > 0.05
        taker_hours = rng.choice([16, 24, 30, 32, 36, 38, 40])
        shift = rng.choice([4, 6, 8])
        rest_ok = rng.random() > 0.04
        over = taker_hours + shift > cap
        if not qualified:
            res["refused: not qualified"] += 1
        elif over or not rest_ok:
            res["store manager: overtime/rest"] += 1
        else:
            res["approved by rule"] += 1
        if qualified and over:
            vendor_ot += 1
    rec.print("== Pennant Stores: one week of shift swaps")
    rec.print("swap requests: 240")
    for k, v in sorted(res.items()):
        rec.print(f"  {k:<30} {v:>4}")
    rec.print(f"vendor default auto-approved into overtime:"
              f" {vendor_ot}")


def ghafline(rec) -> None:
    """A correction file: two approvers, one dispatch, then a
    status per line from the bank; nothing is sent twice."""
    rng = random.Random(1404)
    lines = [{"line": f"L{i:02d}", "emp": f"GF-{rng.randint(
        10000, 99999)}", "aed": rng.choice(
        [410, 650, 900, 1200, 1850])} for i in range(1, 32)]
    approvals = ["GF-PAY-CTRL-02", "GF-FIN-11"]
    assert len(set(approvals)) == 2       # two different people
    bank = {l["line"]: "paid" for l in lines}
    bank["L17"] = "rejected: account mismatch"
    del bank["L26"]                       # status not returned
    states = Counter(bank.get(l["line"], "unknown")
                     for l in lines)
    total = sum(l["aed"] for l in lines)
    rec.print("== Ghafline Dubai: January 2027 correction file")
    rec.print(f"correction lines: {len(lines)}, AED {total:,}")
    rec.print("approvals: " + " and ".join(approvals))
    for k, v in sorted(states.items()):
        rec.print(f"  {k:<30} {v:>4}")
    for l in lines:
        st = bank.get(l["line"])
        if st != "paid":
            act = ("query status; do not resend" if st is None
                   else "new line after the account is fixed")
            rec.print(f"  {l['line']} AED {l['aed']}: {act}")


def main() -> None:
    rec = RunRecorder("ch14", "sectors")
    for f in (cobbleford, crossfield, pennant, ghafline):
        f(rec)
    rec.save()


if __name__ == "__main__":
    main()
