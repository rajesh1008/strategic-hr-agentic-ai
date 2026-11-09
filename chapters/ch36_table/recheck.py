"""Chapter 36: the employee CAUSE check, v1.0 against v1.1.

Book section "One action, four tables". Check v1.0 failed
every employee note on CAUSE because it looked for the
words "retry", "feed" or "resent", which the PLAIN rule
keeps out of an employee's note. v1.1 also accepts the
cause in plain words: the change was sent twice, again or
more than once. It still fails a note that blames the agent
or says the bank details themselves were changed more than
once. This script reruns both versions over the notes the
recorded explain runs returned; it calls no model.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch36_table.recheck
"""
from __future__ import annotations

import json
import re

from chapters.ch36_table import explain
from hrai.llm import REPO, RunRecorder

PLAIN_CAUSE = re.compile(
    r"\bsen(?:t|d)\b[^.]{0,40}\b(?:twice|again|more than once)\b|"
    r"repeat(?:ed)? send", re.I)


def cause_v11(note: str) -> bool:
    if explain.BLAME.search(note):
        return False
    return bool(re.search(r"retr|feed|resen", note, re.I)
                or PLAIN_CAUSE.search(note))


def notes(record: dict) -> list[tuple[str, str]]:
    """(audience, note) pairs, in the order explain wrote them."""
    out = []
    for aud, call in zip(explain.AUD, record["calls"]):
        text = "".join(b.get("text", "") for b in
                       call["response"]["content"]
                       if b["type"] == "text").strip()
        out.append((aud, text))
    return out


def main() -> None:
    rec = RunRecorder("ch36", "recheck")
    files = sorted((REPO / "runs" / "ch36" / "explain").glob("*.json"))
    tally = {"1.0": 0, "1.1": 0}
    for f in files:
        r = json.loads(f.read_text())
        for aud, note in notes(r):
            if aud != "employee":
                continue
            v10 = explain.check(aud, note)["CAUSE"]
            v11 = cause_v11(note)
            tally["1.0"] += v10
            tally["1.1"] += v11
            hit = PLAIN_CAUSE.search(note)
            rec.print(f"{r['run_id']} ({r['model']}): CAUSE v1.0 "
                      f"{'ok' if v10 else 'FAIL'}, v1.1 "
                      f"{'ok' if v11 else 'FAIL'}"
                      + (f'  "{hit.group(0)}"' if hit else ""))
    n = sum(1 for f in files)
    rec.print(f"employee notes passing CAUSE: v1.0 {tally['1.0']} of "
              f"{n}, v1.1 {tally['1.1']} of {n}")
    rec.note(files=[f.name for f in files], **tally)
    rec.save()


if __name__ == "__main__":
    main()
