"""Chapter 1: what the three incidents did, counted from fixtures.

Book sections: "The weekend the software decided", "Ashby & Lowe:
the switch nobody read" and "Brightwater: the chatbot that
canceled". Deterministic counts over synthetic fixtures; no model.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch01_moved_too_fast.incidents
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

from hrai.llm import RunRecorder

REPO = Path(__file__).resolve().parents[2]
FIX = REPO / "fixtures"


def _csv(path: Path) -> list[dict]:
    lines = [ln for ln in path.read_text().splitlines()
             if not ln.startswith("#")]
    return list(csv.DictReader(lines))


def hartwell(p) -> dict:
    rows = _csv(FIX / "hartwell/field-tech-applicants.csv")
    by = Counter(r["status_fri"] for r in rows)
    inv = Counter(r["status_fri"] for r in rows
                  if r["recruiter_invited"] == "Y")
    gap = {s: sum(int(r["employment_gap_months"]) > 6
                  for r in rows if r["status_fri"] == s)
           for s in ("applied", "not_progressed")}
    p("HARTWELL  Smart Shortlist, two requisitions")
    p(f"  applicants on the requisitions    {len(rows):>5}")
    p(f"  kept by the ranking (top half)    {by['applied']:>5}")
    p(f"  moved to not_progressed           "
      f"{by['not_progressed']:>5}")
    p(f"  arrived after the batch           "
      f"{by['not_yet_applied']:>5}")
    p(f"  later invited by recruiters       "
      f"{sum(inv.values()):>5}")
    p(f"    of them from the moved half     "
      f"{inv['not_progressed']:>5}")
    p(f"  gap over six months, kept half    "
      f"{gap['applied']:>5}")
    p(f"  gap over six months, moved half   "
      f"{gap['not_progressed']:>5}")
    return {"status": dict(by), "invited": dict(inv), "gap": gap}


def ashby_lowe(p) -> dict:
    d = json.loads(
        (FIX / "sectors/ashby-lowe/auto-screen-warehouse.json")
        .read_text())
    apps = d["applicants"]
    dec = [a for a in apps if a["auto_declined"]]
    cert = [a for a in dec if a["forklift_certificate"]]
    word = [a for a in cert
            if a["certificate_written_as"] == "FLT"]
    p("ASHBY & LOWE  bundled auto-screen, one requisition")
    p(f"  applicants                        {len(apps):>5}")
    p(f"  declined automatically            {len(dec):>5}")
    p(f"  declined while holding a license  {len(cert):>5}")
    p(f"    because they wrote 'FLT'        {len(word):>5}")
    p(f"    for under a year in a warehouse "
      f"{len(cert) - len(word):>5}")
    return {"applicants": len(apps), "declined": len(dec),
            "declined_certified": len(cert),
            "declined_for_wording": len(word)}


def brightwater(p) -> dict:
    d = json.loads(
        (FIX / "sectors/brightwater/ohio-chatbot-bookings.json")
        .read_text())
    b = d["bookings"]
    can = [x for x in b if x["cancelled_by_bot"]]
    lost = [x for x in can if x["rebooked"] == "not rebooked"]
    silent = [x for x in can if x["candidate_told"] == "none"]
    both = [x for x in lost if x["candidate_told"] == "none"]
    p("BRIGHTWATER  plant chatbot, one week at OH-2")
    p(f"  interviews booked by the chatbot  {len(b):>5}")
    p(f"  canceled by the chatbot           {len(can):>5}")
    p(f"  canceled and never rebooked       {len(lost):>5}")
    p(f"  canceled, candidate not told      {len(silent):>5}")
    p(f"  never rebooked and never told     {len(both):>5}")
    return {"booked": len(b), "cancelled": len(can),
            "not_rebooked": len(lost), "not_told": len(silent),
            "neither": len(both)}


def main(argv: list[str]) -> None:
    rec = RunRecorder("ch01", "incidents")
    out = {"hartwell": hartwell(rec.print),
           "ashby_lowe": ashby_lowe(rec.print),
           "brightwater": brightwater(rec.print)}
    rec.note(**out)
    print("run record:", rec.save().name)


if __name__ == "__main__":
    main(sys.argv[1:])
