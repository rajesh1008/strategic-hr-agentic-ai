"""Chapter 36: promises kept and open (deterministic).

Book section "Promises kept and open". Each promise the
book made about something a later chapter would show is
a row with the chapter that opened it and, if any, the
chapter that closed it. The script counts them as of
June 30, 2028 and lists what is still open, split into
open with a date ahead and open with no later reading.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch36_table.promises
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent


def load() -> list[dict]:
    return yaml.safe_load(
        (HERE / "data" / "promises.yaml").read_text())["promises"]


def split(rows: list[dict]) -> dict[str, list[dict]]:
    out = {"closed": [], "dated": [], "undated": []}
    for r in rows:
        if r["closed"] is not None:
            out["closed"].append(r)
        elif r.get("due"):
            out["dated"].append(r)
        else:
            out["undated"].append(r)
    return out


def main() -> None:
    rec = RunRecorder("ch36", "promises")
    rows = load()
    s = split(rows)
    rec.print(f"Promises made in Chapters 1-35: {len(rows)}")
    rec.print(f"  closed: {len(s['closed'])} "
              f"(in Chapter 36: "
              f"{sum(r['closed'] == 36 for r in s['closed'])})")
    rec.print(f"  open, dated after June 30, 2028: {len(s['dated'])}")
    for r in sorted(s["dated"], key=lambda r: r["due"]):
        when = r.get("due_text") or f"{r['due']:%B %-d, %Y}"
        rec.print(f"    {when:<18} ch{r['opened']:<2} "
                  f"{r['what']}")
    rec.print(f"  open, no later reading in the record: {len(s['undated'])}")
    for r in sorted(s["undated"], key=lambda r: r["opened"]):
        rec.print(f"    ch{r['opened']:<2} {r['what']}")
    rec.note(total=len(rows), **{k: len(v) for k, v in s.items()})
    rec.save()


if __name__ == "__main__":
    main()
