"""Chapter 27: the works agreement as checks (no model).

Book section "The Betriebsrat's answer". Eight clauses of
the draft works agreement on the skills inventory, written
so that code can check a design against them. A clause the
configuration cannot show is a clause the system does not
keep.

Run:  HRAI_MODEL=no-model python -m chapters.ch27_skills.agreement
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"
SOURCES_OK = {"project_reports", "ticket_notes",
              "learning_records", "project_roles"}
NO_READ = {"ka.manager", "perf.pack"}  # supports decisions
CLAUSES = [
 ("WA-1", "listed sources only, no chat or email",
  lambda d: set(d["sources"]) <= SOURCES_OK),
 ("WA-2", "no times or activity data to the model",
  lambda d: not d["times_to_model"]),
 ("WA-3", "nobody else sees it before the person accepts",
  lambda d: d["shown_before_accept"] == ["employee"]),
 ("WA-4", "no level, score or confidence from a model",
  lambda d: d["model_sets"] == ["suggestion"]),
 ("WA-5", "no reader that supports a performance or "
          "conduct decision",
  lambda d: not set(d["readers"]) & NO_READ),
 ("WA-6", "suggestions can be switched off, no reason",
  lambda d: d["opt_out"]),
 ("WA-7", "per-person accept and reject records kept "
          "90 days at most",
  lambda d: d["decision_log_days"] is not None
  and d["decision_log_days"] <= 90),
 ("WA-8", "Betriebsrat reads the access log quarterly",
  lambda d: d["council_reads_access_log"]),
]


def main() -> None:
    designs = yaml.safe_load(
        (HERE / "designs.yaml").read_text())
    rec = RunRecorder("ch27", "agreement")
    rec.print("clause  " + "  ".join(f"{k:5s}"
                                     for k in designs))
    for cid, text, ok in CLAUSES:
        row = ["pass " if ok(d) else "FAIL "
               for d in designs.values()]
        rec.print(f"{cid}    " + "  ".join(row) + f"  {text}")
    for k, d in designs.items():
        n = sum(ok(d) for _, _, ok in CLAUSES)
        rec.print(f"{k}: {n} of {len(CLAUSES)} clauses kept")
        rec.note(design=k, kept=n)
    rec.save()


if __name__ == "__main__":
    main()
