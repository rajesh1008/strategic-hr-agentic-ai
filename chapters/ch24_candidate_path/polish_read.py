"""Chapter 24: what the rewrites added (no model).

Reads the recorded polish run and counts, for each style,
the rewrites that left [bracketed] placeholders for the
candidate to fill, that name EPA 608 when the original
listed no 608 at all, and that lost a date range. Prints the
IDs so the book can show the text.

Run:  HRAI_MODEL=no-model python -m chapters.ch24_candidate_path.polish_read
"""
from __future__ import annotations

import json
import re

from hrai.llm import REPO, RunRecorder

from chapters.ch24_candidate_path import polish

RUN = "20261109T153604Z-claude-haiku-5-5.json"
HOLE = re.compile(r"\[[^\]]{3,}\]")
EPA = re.compile(r"\b(EPA|608)\b")


def main() -> None:
    rec = RunRecorder("ch24", "polish_read")
    data = json.loads((REPO / "runs" / "ch24" / "polish" /
                       RUN).read_text())
    res = data["events"][0]["results"]
    apps = {a["candidate_id"]: a for a in polish.sample()}
    rec.print(f"read ch24/polish/{RUN[:16]}: {len(res)} "
              f"applications")
    for style in polish.ASK:
        holes, invite, lost = [], [], []
        for cid, r in res.items():
            text, orig = r[style]["text"], apps[cid]["resume"]
            if HOLE.search(text):
                holes.append(cid)
            if EPA.search(text) and not EPA.search(orig):
                invite.append(cid)
            if not r[style]["dates_kept"]:
                lost.append(cid)
        rec.print(f"{style}: placeholders {len(holes)}; names 608 "
                  f"with none listed {len(invite)}; lost a date "
                  f"range {len(lost)}")
        for cid in dict.fromkeys(invite + lost):
            rec.print(f"  {cid} {res[cid]['kind']:<13} "
                      f"{'names 608' if cid in invite else ''}"
                      f"{' lost dates' if cid in lost else ''}")
    print(rec.save())


if __name__ == "__main__":
    main()
