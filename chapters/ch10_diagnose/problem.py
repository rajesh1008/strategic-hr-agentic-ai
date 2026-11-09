"""Chapter 10: check a problem statement before anyone buys.

Seven fields. The check fails a statement that has an empty
field, no number for today, no number for success, an owner who
is a department or a vendor, or a tool named where the problem
should be. No model is used.

Run: HRAI_MODEL=no-model python -m chapters.ch10_diagnose.problem
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent / "data"
FIELDS = ("who", "now", "cost", "owner", "measure", "limits")
TOOLS = re.compile(r"\b(AI|agent|bot|chatbot|copilot|model|"
                   r"automate|deflect|Talentra|platform)\b", re.I)
NOT_OWNERS = {"it", "hr", "vendor", "the vendor", "everyone"}


def check(s: dict) -> list[str]:
    out = [f"{f}: empty" for f in FIELDS if not s.get(f, "").strip()]
    if not re.search(r"\d", s.get("now", "")):
        out.append("now: no number for today")
    if not re.search(r"\d", s.get("measure", "")):
        out.append("measure: no number for success")
    if s.get("owner", "").strip().lower() in NOT_OWNERS:
        out.append("owner: a department, not a named role")
    for f in ("who", "now", "cost", "measure"):
        m = TOOLS.search(s.get(f, ""))
        if m:
            out.append(f"{f}: names a tool ({m.group(0)})")
    return out


def main() -> None:
    from hrai.llm import RunRecorder
    rec = RunRecorder("ch10", "problem")
    for s in yaml.safe_load((DATA / "problems.yaml").read_text()):
        found = check(s)
        rec.print(f"{s['id']}: {'PASS' if not found else 'FAIL'}"
                  f" ({len(found)} problems)")
        for f in found:
            rec.print(f"  {f}")
        rec.note(statement=s["id"], problems=found)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
