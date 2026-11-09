"""Chapter 32: the case-file intake check for WA-9 (no model).

Book section "Settling the monitoring clause". Clause WA-9
says nothing from the skills inventory may be used in a
performance or conduct case. The system half of that promise
is this check, run when an item is added to a case file. It
refuses anything the inventory produced, holds anything
whose origin it cannot see, and accepts original records,
which stay usable even when the inventory holds a copy.

Run:  HRAI_MODEL=no-model python -m chapters.ch32_voice.intake
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"
INVENTORY = {"skills_inventory", "talent.search",
             "mobility.match", "learning.recommend"}
RECORDS = {"certificate_register", "sap_pm", "hr_file",
           "time_system_contract"}


def verdict(item: dict) -> tuple[str, str]:
    src = item["source"]
    if src in INVENTORY:
        return "REFUSE", "made by the inventory (WA-9)"
    if src in RECORDS:
        return "ACCEPT", f"original record ({src})"
    if item["says_inventory"]:
        return "HOLD", "cites the inventory; ask for the record"
    return "HOLD", "origin unknown; ask where it came from"


def main() -> None:
    case = yaml.safe_load(
        (HERE / "intake_case.yaml").read_text())
    rec = RunRecorder("ch32", "intake")
    rec.print(f"Case {case['case']}")
    for it in case["items"]:
        v, why = verdict(it)
        rec.print(f"{it['id']}  {v:6s}  {why}")
        rec.note(item=it["id"], verdict=v)
    rec.save()


if __name__ == "__main__":
    main()
