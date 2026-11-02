"""Chapter 2 live example: the model drafts, the code checks.

The model gets the calculator's printed output and the CFO's
question. Deterministic code then checks the draft: every
number must come from the calculator, and no heads language.
Run (needs ANTHROPIC_API_KEY):
  python -m chapters.ch02_strategic_hr.cfo_note
"""
from __future__ import annotations

import textwrap

from hrai.llm import REPO, RunRecorder

from . import econ, numbers, workforce_economics

QUESTION = (
    "From the CFO: I need HR's AI case in cost per head. "
    "How many heads does this take out, and when?")

SYSTEM = (
    "You draft short notes from Hartwell's HR function to its "
    "CFO. Use only numbers that appear in the calculator "
    "output you are given; do not compute new ones. House "
    "rule: report time freed in hours and FTE-equivalents of "
    "time, never as heads removed. Say which figures are "
    "claims not yet measured. Plain prose, under 170 words, "
    "no headings, no bullet points.")


def calculator_text() -> str:
    """The calculator's report, exactly as it prints."""
    lines: list[str] = []
    workforce_economics.report(lines.append)
    return "\n".join(lines)


def main() -> None:
    calc = calculator_text()
    rec = RunRecorder("ch02", "cfo_note")
    resp = rec.create(
        max_tokens=600, system=SYSTEM,
        messages=[{"role": "user", "content":
                   f"{QUESTION}\n\nCalculator output:\n"
                   + calc}])
    note = "".join(b.text for b in resp.content
                   if b.type == "text").strip()
    for para in note.split("\n"):
        for line in textwrap.wrap(para, 60) or [""]:
            rec.print(line)
    rec.print("")
    extra = numbers.unsourced(note, calc)
    heads = econ.refuse_heads(note)
    rec.print(f"CHECK unsourced numbers: {extra or '-'}")
    rec.print(f"CHECK heads language: {heads or '-'}")
    verdict = "HOLD for edit" if extra or heads else "PASS"
    rec.print(f"CHECK verdict: {verdict}")
    rec.note(unsourced=extra, heads=heads, verdict=verdict,
             usage=resp.usage.model_dump())
    path = rec.save()
    print("run record:", path.relative_to(REPO))


if __name__ == "__main__":
    main()
