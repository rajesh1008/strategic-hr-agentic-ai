"""Chapter 36: one action, four tables (model).

Book section "One action, four tables". The same incident,
INC-2027-031, is explained to four readers: the board's
audit and risk committee, a regulator, the union local and
one affected employee. The model writes each note from one
fact sheet (the Chapter 23 run output and DR-23-01); code
then checks every note. Shared checks: N1 every number is
on the fact sheet; OWNER names Megan Hale; CAUSE puts the
cause in the feed's retry, not the agent; WAYBACK says the
changes were reversed; PROMISE has no guarantee. Each
reader adds one: BOARD states the missed target; REG says
who decided on notification; UNION identifies no one;
PLAIN keeps internal codes out of the employee's note and
gives the pay date.

Run:  python -m chapters.ch36_table.explain
      HRAI_MODEL=claude-sonnet-5-5 python -m \\
        chapters.ch36_table.explain
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from hrai.llm import RunRecorder, model

HERE = Path(__file__).resolve().parent
FACTS = (HERE / "data" / "facts.md").read_text()
AUD = yaml.safe_load((HERE / "data" / "audiences.yaml").read_text())
THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
SYSTEM = (
    "You write for Hartwell's HR Shared Services lead. Write a"
    " note of 120 to 180 words to {reader}. They ask: {asks}"
    " {rules} Use only the facts below; do not add numbers,"
    " dates, names or causes that are not in them. Plain text,"
    " no headings, no bullet points.\n\nFACTS\n{facts}")
NUM = re.compile(r"\d+(?:[.,:]\d+)*")
PROMISE = re.compile(r"never happen again|will not happen again|"
                     r"won't happen again|cannot happen again|"
                     r"guarantee|100%|completely eliminat", re.I)
BLAME = re.compile(r"\b(?:the agent|AskHartwell|the AI)\b[^.]{0,30}"
                   r"\b(?:caused|duplicated|sent (?:the )?dup|"
                   r"made (?:an|the) error|malfunction)", re.I)
JARGON = re.compile(r"PR-1|readback|read back|\bT1\b|matrix|"
                    r"severity|B-1116|DR-23-01|HartwellOne", re.I)


def norm(n: str) -> str:
    """37 and 37, the same; 06:05 and 6:05, the same."""
    n = n.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", n) \
        else n.rstrip(".,:")
    return n.lstrip("0") or "0"


def numbers(text: str) -> set[str]:
    return {norm(n) for n in NUM.findall(text)}


FACT_NUMS = numbers(FACTS)


def check(aud: str, note: str) -> dict[str, bool]:
    stray = {n for n in NUM.findall(note)
             if norm(n) not in FACT_NUMS}
    c = {"N1": not stray,
         "OWNER": "Megan Hale" in note,
         "CAUSE": bool(re.search(r"retr|feed|resen|sent the "
                                 r"(?:whole )?batch (?:again|twice)",
                                 note, re.I))
                  and not BLAME.search(note),
         "WAYBACK": bool(re.search(r"revers|undone|restored|"
                                   r"corrected", note, re.I)),
         "PROMISE": not PROMISE.search(note)}
    if aud == "board":
        c["BOARD"] = bool(re.search(r"miss", note, re.I))
    elif aud == "regulator":
        c["REG"] = bool(re.search(r"counsel", note, re.I)
                        and re.search(r"notif", note, re.I))
    elif aud == "union":
        c["UNION"] = not re.search(r"HW-\d|\*\*\*\*\d", note)
    else:
        c["PLAIN"] = (not JARGON.search(note)
                      and bool(re.search(r"November 19|"
                                         r"payday|Friday", note)))
    c["_stray"] = sorted(stray)
    return c


def write(rec: RunRecorder, aud: str) -> str:
    a = AUD[aud]
    kw = {"thinking": THINK[model()]} if model() in THINK else {}
    r = rec.create(max_tokens=1500, system=SYSTEM.format(
        facts=FACTS, **a), messages=[{"role": "user", "content":
        f"Write the note to {a['reader']}."}], **kw)
    return "".join(b.text for b in r.content if b.type == "text")


def main() -> None:
    rec = RunRecorder("ch36", "explain")
    total, passed = 0, 0
    for aud in AUD:
        note = write(rec, aud).strip()
        c = check(aud, note)
        stray = c.pop("_stray")
        ok = all(c.values())
        total += 1
        passed += ok
        words = len(note.split())
        rec.print(f"== {aud} ({words} words): "
                  f"{'PASS' if ok else 'FAIL'}")
        rec.print("  " + "  ".join(
            f"{k} {'ok' if v else 'FAIL'}" for k, v in c.items()))
        if stray:
            rec.print(f"  numbers not on the fact sheet: "
                      f"{', '.join(stray)}")
        for line in note.splitlines():
            if line.strip():
                rec.print(f"  | {line.strip()}")
        rec.note(audience=aud, checks=c, stray=stray, words=words,
                 passed=ok)
    rec.print(f"notes passing every check: {passed} of {total}")
    rec.save()


if __name__ == "__main__":
    main()
