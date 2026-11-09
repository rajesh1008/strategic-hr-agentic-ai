"""The retention schedule, checked copy by copy (no model).

Book section: "Retention: every copy, not just the source".
Agents make copies: evaluation sets, debug snapshots,
caches, index replicas. Four checks per class:
  R1 no copy outlives its source, unless it is derived data
     with no raw content and its own entry
  R2 deleting the source deletes the copy
  R3 every hold names who set it and when it is reviewed
  R4 NEVER-class fields are absent from every copy that is
     not redacted
All values synthetic.

Run: HRAI_MODEL=no-model python -m \\
         chapters.ch18_boundaries.retention
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"
RAW = {"prompt", "answer", "tool_results", "resume_text"}


def check(c: dict, never: set[str]) -> list[str]:
    out = []
    for h in c["holds"]:
        if not (h["set_by"] and h["review"]):
            out.append(f"R3 hold {h['case']} has no named"
                       " owner or review date")
    for k in c["copies"]:
        s = k["store"]
        derived = (k.get("derived")
                   and not RAW & set(k["fields"]))
        if k["days"] > c["days"] and not derived:
            out.append(f"R1 {s} kept {k['days']} days,"
                       f" source {c['days']}")
        if not k["propagates"] and not k.get("derived"):
            out.append(f"R2 {s} survives source deletion")
        raw = RAW & set(k["fields"])
        if (raw or never & set(k["fields"])) \
                and not k["redacted"] and k["days"] > 7:
            out.append(f"R4 {s} holds unredacted content")
    return out


def main(month: str = "") -> None:
    sfx = f"_{month}" if month else ""
    rec = RunRecorder("ch18", "retention" + sfx)
    cfg = yaml.safe_load(
        (DATA / f"retention{sfx}.yaml").read_text())
    never, total = set(cfg["never"]), 0
    for c in cfg["classes"]:
        gaps = check(c, never)
        total += len(gaps)
        rec.note(cls=c["id"], gaps=gaps)
        rec.print(f"{c['id']:<8} {c['data']}: "
                  + ("ok" if not gaps else f"{len(gaps)} gaps"))
        for g in gaps:
            rec.print(f"  {g}")
    rec.print(f"Gaps: {total}")
    print(rec.save())


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:2])
