"""Build the synthetic records for Chapter 4 (seeded, so every reader gets the same file).

  data/screening-test.json   Hartwell's offline test of Takefen's ranking: 40 closed
                             field-technician and customer-service requisitions, every
                             application screened once by a recruiter, half of each pool
                             with the Takefen ranking view and half without (synthetic)
  data/askhr-queue.json      Hyderabad capability center tier-1 HR tickets, eight weeks,
                             with and without the vendor's deflection agent (synthetic)

All people and records are synthetic. No real applicant or employee is represented.
Run:  python -m chapters.ch04_claim_ledger.make_data
"""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 4


def screening(rng: random.Random) -> dict:
    reqs, apps = [], []
    families = ["field technician"] * 26 + ["customer service"] * 14
    for r, fam in enumerate(families, start=1):
        rid = f"HW-REQ-26{r:03d}"
        state = rng.choice(["CO", "IL", "TX", "OH", "AZ"])
        n = rng.randint(55, 110)
        reqs.append({"requisition": rid, "family": fam, "state": state, "applications": n})
        for k in range(n):
            older = rng.random() < 0.31                 # applicant self-identified 40 or over
            fit = rng.gauss(0, 1)
            # Takefen's score weights "years since latest certification", a proxy that
            # runs against longer careers (synthetic mechanism for the chapter)
            score = fit + rng.gauss(0, 0.8) - (0.42 if older else 0.0)
            arm = "takefen" if k % 2 else "control"
            base = rng.lognormvariate(1.25, 0.45)       # minutes, about 3.8 on average
            apps.append({"application": f"{rid}-{k:03d}", "requisition": rid, "arm": arm,
                         "age_band": "40+" if older else "under 40", "score": round(score, 3),
                         "base_minutes": round(base, 2)})
    # rank bands inside each requisition, from the vendor score
    by_req: dict[str, list[dict]] = {}
    for a in apps:
        by_req.setdefault(a["requisition"], []).append(a)
    for pool in by_req.values():
        pool.sort(key=lambda a: -a["score"])
        n = len(pool)
        for i, a in enumerate(pool):
            a["band"] = "top" if i < 0.3 * n else ("middle" if i < 0.55 * n else "bottom")
    for a in apps:
        b = a.pop("base_minutes")
        if a["arm"] == "control":
            m = b
        elif a["band"] == "top":        # read the summary, then check it against the resume
            m = b * 0.64 + rng.uniform(0.25, 0.6)
        elif a["band"] == "middle":
            m = b * 0.75 + rng.uniform(0.1, 0.3)
        else:                           # a recruiter still decides every rejection
            m = b * 0.74 + rng.uniform(0.05, 0.25)
        a["minutes"] = round(m, 2)
        a["score"] = round(a["score"], 2)
    return {"_synthetic": True, "organization": "Hartwell Group (synthetic)",
            "test": "Takefen ranking view vs plain view, same recruiters, closed requisitions",
            "period": "requisitions closed April-June 2026; replay run August 2026",
            "requisitions": reqs, "applications": apps}


def queue(rng: random.Random) -> dict:
    cats = [("payslip query", 0.30), ("leave balance", 0.22), ("tax declaration", 0.14),
            ("reimbursement status", 0.12), ("letter request", 0.10), ("other", 0.12)]
    tickets = []
    for w in range(1, 9):
        for i in range(rng.randint(610, 680)):
            cat = rng.choices([c for c, _ in cats], weights=[p for _, p in cats])[0]
            arm = "agent" if i % 2 else "control"
            bot_closed = arm == "agent" and rng.random() < {"payslip query": 0.50, "leave balance": 0.62,
                                                            "tax declaration": 0.30, "reimbursement status": 0.55,
                                                            "letter request": 0.44, "other": 0.12}[cat]
            recontact = bot_closed and rng.random() < (0.42 if cat in ("payslip query", "tax declaration") else 0.22)
            tickets.append({"ticket": f"HYD-{w}-{i:04d}", "week": w, "category": cat, "arm": arm,
                            "bot_closed": bot_closed, "recontact_7d": recontact})
    return {"_synthetic": True, "organization": "Hartwell capability center, Hyderabad (synthetic)",
            "period": "eight weeks, tier-1 HR queue, alternate tickets routed to the agent",
            "tickets": tickets}


def main() -> None:
    rng = random.Random(SEED)
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data/screening-test.json").write_text(json.dumps(screening(rng), indent=0) + "\n")
    (HERE / "data/askhr-queue.json").write_text(json.dumps(queue(rng), indent=0) + "\n")
    print("wrote data/screening-test.json and data/askhr-queue.json")


if __name__ == "__main__":
    main()
