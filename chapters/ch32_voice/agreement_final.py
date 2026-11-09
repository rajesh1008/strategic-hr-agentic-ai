"""Chapter 32: the signed works agreement as checks (no model).

Book section "Settling the monitoring clause". Chapter 27
wrote eight draft clauses as code. The agreement Hartwell
Germany and the Betriebsrat signed on May 18, 2028 keeps six
of them as drafted, rewrites WA-5 and WA-7, and adds WA-9
and WA-10. Two checks owned by other people run beside it:
Nathan Cole's (an accepted entry can always be traced) and
group counsel's (the counts a discrimination defense needs).
A design passes only if it passes all twelve.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch32_voice.agreement_final
"""
from __future__ import annotations

from pathlib import Path

import yaml

from chapters.ch27_skills import agreement as draft
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"
KEPT = {cid: ok for cid, _, ok in draft.CLAUSES}
TRAIL_DAYS = 2555  # 84 months, every controlled action


def derive(d: dict) -> dict:
    """Fill keys a Chapter 27 design does not have."""
    d = dict(d)
    log = d["decision_log_days"]
    d.setdefault("reader_consent", {})
    d.setdefault("accept_record", "trail")
    d.setdefault("accept_log_days", log)
    d.setdefault("reject_log_days", log)
    d.setdefault("group_counts_days", None)
    d.setdefault("group_counts_min_cell", None)
    d.setdefault("case_intake_blocks", False)
    d.setdefault("change_needs_consent", False)
    return d


def _traceable(d: dict) -> bool:
    if d["accept_record"] == "profile":
        return d["accept_log_days"] is None
    days = d["accept_log_days"]
    return days is not None and days >= TRAIL_DAYS


SIGNED = [
 ("WA-1", "listed sources only", KEPT["WA-1"]),
 ("WA-2", "no times or activity data", KEPT["WA-2"]),
 ("WA-3", "the person sees it first", KEPT["WA-3"]),
 ("WA-4", "no model level or score", KEPT["WA-4"]),
 ("WA-5", "only consented readers, none for "
          "performance or conduct",
  lambda d: not set(d["readers"]) & draft.NO_READ
  and all(r in d["reader_consent"] for r in d["readers"])),
 ("WA-6", "can be switched off", KEPT["WA-6"]),
 ("WA-7", "rejections 90 days, then counts; "
          "accepts live with the entry",
  lambda d: d["reject_log_days"] is not None
  and d["reject_log_days"] <= 90
  and d["accept_record"] == "profile"),
 ("WA-8", "council reads the access log", KEPT["WA-8"]),
 ("WA-9", "no inventory data in a performance "
          "or conduct case file",
  lambda d: d["case_intake_blocks"]),
 ("WA-10", "new source or reader needs consent",
  lambda d: d["change_needs_consent"]),
 ("TRL-A", "every accepted entry can be traced",
  _traceable),
 ("DEF-1", "group counts kept 84 months, cells "
           "under 10 hidden",
  lambda d: (d["group_counts_days"] or 0) >= TRAIL_DAYS
  and d["group_counts_min_cell"] == 10),
]


def designs() -> dict:
    old = yaml.safe_load(
        (draft.HERE / "designs.yaml").read_text())
    new = yaml.safe_load(
        (HERE / "design_v2_2.yaml").read_text())
    both = {k: old[k] for k in ("v2", "v2.1")} | new
    return {k: derive(v) for k, v in both.items()}


def main() -> None:
    ds = designs()
    rec = RunRecorder("ch32", "agreement_final")
    rec.print("check   " + "  ".join(f"{k:5s}" for k in ds))
    for cid, text, ok in SIGNED:
        row = ["pass " if ok(d) else "FAIL "
               for d in ds.values()]
        rec.print(f"{cid:6s}  " + "  ".join(row)
                  + f"  {text}")
    for k, d in ds.items():
        n = sum(bool(ok(d)) for _, _, ok in SIGNED)
        rec.print(f"{k}: {n} of {len(SIGNED)}")
        rec.note(design=k, passed=n)
    rec.save()


if __name__ == "__main__":
    main()
