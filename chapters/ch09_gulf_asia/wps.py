"""Chapter 9: WPS file checks before a salary file is sent.

Compares a WPS-style salary file with the roster and the
contract wages, and routes every exception to a named role.
The checks are deterministic; no model. Releasing payment,
changing a wage and approving a deduction stay with people.

Run: HRAI_MODEL=no-model python -m \
    chapters.ch09_gulf_asia.wps
(writes runs/ch09/wps/...)
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

OWNER = {
    "MISSING": "payroll lead",
    "NOT_ON_ROSTER": "payroll lead",
    "SHORT": "payroll lead, then HR director",
    "BANNED_DEDUCTION": "HR director and welfare officer",
    "NO_ACCOUNT": "payroll lead",
    "CONTROL": "payroll lead",
    "LATE": "finance director",
}


def load_rules() -> dict:
    text = (HERE / "wps_rules.yaml").read_text()
    return yaml.safe_load(text)["AE-WPS"]


def read(name: str) -> list[dict]:
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


def check(roster, lines, control, rule, month_due: date):
    active = {r["worker_id"]: float(r["contract_aed"])
              for r in roster if r["status"] == "active"}
    paid = {ln["worker_id"]: ln for ln in lines}
    out = []
    for w in active:
        if w not in paid:
            out.append(("MISSING", w))
    for w, ln in paid.items():
        if w not in active:
            out.append(("NOT_ON_ROSTER", w))
            continue
        code = ln["deduction_code"]
        if code in rule["deductions"]["never"]:
            out.append(("BANNED_DEDUCTION", w))
        elif (float(ln["paid_aed"]) < rule["worker_min_share"]
              * active[w] and code not in
              rule["deductions"]["allowed"]):
            out.append(("SHORT", w))
        if not ln["account"]:
            out.append(("NO_ACCOUNT", w))
    total = sum(float(ln["paid_aed"]) for ln in lines)
    if (int(control["lines"]) != len(lines)
            or float(control["total_aed"]) != total):
        out.append(("CONTROL", "file"))
    days = max((date.fromisoformat(ln["paid_on"])
                - month_due).days for ln in lines)
    if days > 0:
        out.append(("LATE", f"{days} days"))
    due = sum(active.values())
    on_time = total if days <= 0 else 0.0
    return out, {"due": due, "in_file": total, "days": days,
                 "firm_share_on_time": on_time / due}


def main() -> None:
    from hrai.llm import RunRecorder
    rule = load_rules()
    roster = read("ghafline_roster_2027-01.csv")
    lines = read("ghafline_wps_2027-01.csv")
    control = dict(x.split("=") for x in (
        DATA / "ghafline_wps_2027-01.control").read_text().split())
    due = date(2027, 1, rule["due_day"])
    found, tot = check(roster, lines, control, rule, due)
    rec = RunRecorder("ch09", "wps")
    p = rec.print
    act = sum(r["status"] == "active" for r in roster)
    p("Ghafline Facilities, Dubai: December 2026 wages")
    p("(synthetic)")
    p(f"roster active {act}, file lines {len(lines)}, "
      f"due {due}")
    p("")
    p("check              count  goes to")
    for k in OWNER:
        n = sum(1 for f in found if f[0] == k)
        p(f"{k:<18} {n:>5}  {OWNER[k]}")
    p("")
    p(f"wages due AED {tot['due']:,.0f}; in file AED "
      f"{tot['in_file']:,.0f}")
    p(f"value date {tot['days']} days after the due date; "
      f"on time {tot['firm_share_on_time']:.0%} (rule "
      f"{rule['firm_min_share']:.0%})")
    step = max((d for d in rule["ladder"] if d <= tot["days"]),
               default=None)
    if step:
        p(f"ladder step reached: day {step}, "
          f"{rule['ladder'][step]}")
    nxt = min((d for d in rule["ladder"] if d > tot["days"]),
              default=None)
    if nxt:
        p(f"next step: day {nxt}, {rule['ladder'][nxt]}")
    p("file status: HELD; release is a person's decision")
    rec.note(findings=[list(f) for f in found], **tot)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
