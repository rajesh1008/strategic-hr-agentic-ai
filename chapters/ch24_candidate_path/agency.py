"""Chapter 24: Crossfield Staffing's supply checks (no model).

Book section "When the employer is an agency". Two checks a
staffing agency runs before a person is put forward, and one
on what a client asks for:
  reg19   UK (Birmingham): no introduction or supply until the
          agency holds confirmation of identity and of the
          qualifications the hirer or the law requires
  awr     UK: weeks in the same role with the same hirer,
          counted toward the 12-week qualifying period
  orders  US (Chicago): a client order that asks the agency
          to prefer or exclude people on a Title VII ground
          is held for a person; the agency may not refer on
          that basis

Records synthetic. Not legal advice.

Run:  HRAI_MODEL=no-model python -m chapters.ch24_candidate_path.agency
"""
from __future__ import annotations

import re
from datetime import date

from hrai.llm import RunRecorder

# (worker, hirer, role, identity confirmed, quals confirmed,
#  supplied on, assignment weeks so far)
SUPPLY = [
    ("W-201", "Hartwell UK", "site cleaner", date(2028, 1, 4),
     date(2028, 1, 4), date(2028, 1, 10), 11),
    ("W-202", "Hartwell UK", "site cleaner", date(2028, 1, 5),
     None, date(2028, 1, 10), 11),
    ("W-203", "Hartwell UK", "FM electrician", date(2028, 1, 6),
     date(2028, 1, 12), date(2028, 1, 10), 9),
    ("W-204", "Hartwell UK", "porter", date(2028, 1, 3),
     date(2028, 1, 3), date(2028, 1, 10), 12),
    ("W-205", "Hartwell UK", "porter", date(2028, 1, 3),
     date(2028, 1, 3), date(2028, 1, 10), 13),
    ("W-206", "Midlands Arena", "steward", date(2028, 2, 1),
     date(2028, 2, 1), date(2028, 2, 3), 4),
    ("W-207", "Midlands Arena", "steward", None,
     date(2028, 2, 1), date(2028, 2, 3), 4),
    ("W-208", "Hartwell UK", "FM electrician", date(2028, 1, 6),
     date(2028, 1, 7), date(2028, 1, 10), 10),
]
AWR_WEEKS = 12
WARN_AT = 10

ORDERS = [
    ("O-3101", "Need 12 pickers for nights, forklift ticket "
     "preferred."),
    ("O-3102", "Six warehouse staff. Prefer young guys, it's "
     "heavy work."),
    ("O-3103", "Event crew x20, must speak clear English with "
     "no heavy accent."),
    ("O-3104", "Two CNAs, current state certification."),
    ("O-3105", "Front desk temp, female preferred, guests "
     "like that."),
    ("O-3106", "Packers for Sunday shifts only."),
    ("O-3107", "Security officers, US citizens only."),
    ("O-3108", "Cleaners, 3 nights a week."),
]
GROUNDS = {
    "sex": r"\b(female|male|women|men|guys|girls|lads)\b",
    "national origin": r"\b(accent\w*|native speaker)\b",
    "citizenship (verify)": r"\bcitizens? only\b",
    "religion": r"\b(christian|muslim|jewish|church)\b",
    "age (ADEA, not Title VII)": r"\b(young|under \d\d|"
                                 r"recent grads?)\b",
}


def reg19(row) -> str | None:
    _, _, _, ident, quals, supplied, _ = row
    if ident is None or ident > supplied:
        return "identity unconfirmed"
    if quals is None or quals > supplied:
        return "quals unconfirmed"
    return None


def awr(row) -> str | None:
    weeks = row[6]
    if weeks >= AWR_WEEKS:
        return f"week {weeks}, equal terms due"
    if weeks >= WARN_AT:
        return f"week {weeks}, {AWR_WEEKS - weeks} to go"
    return None


def order_flags(text: str) -> list[str]:
    return [g for g, pat in GROUNDS.items()
            if re.search(pat, text, re.I)]


def main() -> None:
    rec = RunRecorder("ch24", "agency")
    rec.print(f"Crossfield UK supply records: {len(SUPPLY)}")
    held = 0
    for row in SUPPLY:
        a, b = reg19(row), awr(row)
        held += a is not None
        rec.print(f"{row[0]} {row[2]:<15}"
                  f"{'HOLD ' + a if a else 'reg 19 ok'}"
                  f"{'; AWR ' + b if b else ''}")
    rec.print(f"supplies held for reg 19: {held} of {len(SUPPLY)}")
    rec.print()
    rec.print(f"Crossfield US client orders: {len(ORDERS)}")
    hold = 0
    for oid, text in ORDERS:
        f = order_flags(text)
        hold += bool(f)
        rec.print(f"{oid} {'HOLD: ' + ', '.join(f) if f else 'ok'}")
    rec.print(f"orders held for a person: {hold} of {len(ORDERS)}")
    rec.note(supply=[r[0] for r in SUPPLY],
             orders=[o[0] for o in ORDERS])
    print(rec.save())


if __name__ == "__main__":
    main()
