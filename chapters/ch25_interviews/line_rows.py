"""Chapter 25: interview steps on the Automate/Keep Line.

Book section "What a note-taking agent may write". Places the
interview rows with Chapter 11's place() and checks that
Hartwell's set mode is at or below the ceiling. A row that
infers anything on the prohibited list is not placed at all.

Run:  python -m chapters.ch25_interviews.line_rows
"""
from __future__ import annotations

from pathlib import Path

import yaml

from chapters.ch11_automate_keep.line import (
    allowed, answers, place)
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"


def main() -> None:
    rec = RunRecorder("ch25", "line_rows")
    rows = yaml.safe_load(
        (HERE / "line_rows.yaml").read_text())["rows"]
    rec.print("== interview rows on the Line (FT-SI v1)")
    for r in rows:
        if r.get("infers"):
            rec.print(f"{r['id']} REMOVED  prohibited inference"
                      f" {','.join(r['infers'])}")
            rec.print(f"     {r['step']}")
            rec.note(row=r["id"], removed=True)
            continue
        p = place(r["kind"], answers(r["answers"]))
        ok = allowed(p.mode, r["set"])
        rec.print(f"{r['id']} {p.side:8s} ceiling {p.mode:17s}"
                  f" set {r['set']:9s} {'ok' if ok else 'ABOVE'}")
        rec.print(f"     {r['step']}")
        rec.note(row=r["id"], side=p.side, ceiling=p.mode,
                 set=r["set"], ok=ok)
    rec.save()


if __name__ == "__main__":
    main()
