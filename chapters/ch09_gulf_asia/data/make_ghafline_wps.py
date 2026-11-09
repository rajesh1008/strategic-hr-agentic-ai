"""Writes the SYNTHETIC Ghafline roster and January 2027 salary
file used in Chapter 9 (seeded; run once, output committed).
Problems are planted on purpose so the checks have work."""
import csv
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
rng = random.Random(9)
N = 640
roster, lines = [], []
for i in range(1, N + 1):
    wid = f"GHF-{i:05d}"
    wage = rng.choice([1500, 1600, 1800, 2000, 2200, 2600])
    roster.append({"worker_id": wid, "contract_aed": wage,
                   "status": "active"})
    lines.append({"worker_id": wid, "paid_aed": wage,
                  "deduction_code": "", "account": f"AE{i:021d}",
                  "paid_on": "2027-01-04"})
ids = [r["worker_id"] for r in roster]
pick = rng.sample(ids, 44)
gone = set(pick[:9])          # transferred in, no line yet
low = pick[9:32]              # paid short, no code
fee = pick[32:43]             # recruitment fee deducted
noacct = pick[43:44]
lines = [ln for ln in lines if ln["worker_id"] not in gone]
by = {ln["worker_id"]: ln for ln in lines}
wage = {r["worker_id"]: r["contract_aed"] for r in roster}
for w in low:
    by[w]["paid_aed"] = round(wage[w] * 0.70)
for w in fee:
    by[w]["paid_aed"] = wage[w] - 450
    by[w]["deduction_code"] = "RECRUITMENT_FEE"
for w in noacct:
    by[w]["account"] = ""
lines.append({"worker_id": "GHF-00701", "paid_aed": 1800,
              "deduction_code": "", "account": "AE" + "7" * 21,
              "paid_on": "2027-01-04"})   # left in November
roster.append({"worker_id": "GHF-00701", "contract_aed": 1800,
               "status": "left 2026-11-20"})
total = sum(ln["paid_aed"] for ln in lines) + 1200
for name, rows in (("ghafline_roster_2027-01.csv", roster),
                   ("ghafline_wps_2027-01.csv", lines)):
    with open(HERE / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
(HERE / "ghafline_wps_2027-01.control").write_text(
    f"lines={len(lines)}\ntotal_aed={total}\n"
    "salary_month=2026-12\n")
