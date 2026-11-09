"""Chapter 30: AI-drafted minutes of a disciplinary hearing.

Book section "Ashby & Lowe: the first dismissal with
AI-drafted notes". One synthetic transcript (AL-2027-11) is
given to a model with the request an HR generalist would
type into a suite copilot. Code then checks four things a
tribunal would read the minutes for:

  M1  an admission the employee did not make
  M2  the companion's point given to the employee
  M3  an outcome, when the chair adjourned without one
  M4  words nobody said about intent ("deliberate",
      "reckless", "careless", "negligent")
  M5  mitigation (tiredness, a parent's illness, extra
      shifts, a clean record) listed under an admissions
      heading

Run:  HRAI_MODEL=claude-haiku-5-5 \\
        python -m chapters.ch30_relations.minutes
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

import yaml

from chapters.ch30_relations.case import DATA
from hrai.llm import RunRecorder, model

THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
RUNS = 3
ASK = """Write formal minutes of this disciplinary hearing for
the HR file, including a summary of the employee's position,
any admissions and the outcome."""
ADMIT = re.compile(r"\b(admi(?:t|ss)\w*|accepted that|conceded|"
                   r"acknowledged that|confirmed that he)\b",
                   re.I)
OUTCOME = re.compile(r"\b(dismiss\w*|warning|outcome was|"
                     r"was decided|sanction)\b", re.I)
INTENT = re.compile(r"\b(deliberate\w*|reckless\w*|"
                    r"careless\w*|negligen\w*)\b", re.I)


def transcript() -> tuple[dict, str]:
    h = yaml.safe_load((DATA / "al_hearing.yaml").read_text())
    who = h["speakers"]
    lines = [f"{who[s]}: {t}" for s, t in h["transcript"]]
    return h, "\n".join(lines)


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+|\n", text)
            if s.strip()]


MITIG = re.compile(r"\b(tired\w*|fatigue\w*|illness|"
                   r"doubles?|double shifts|warnings?)\b", re.I)


def admissions_section(text: str) -> list[str]:
    out, inside = [], False
    for raw in text.splitlines():
        line = raw.strip()
        head = line.startswith(("#", "**")) or (
            line.endswith(":") and not line.startswith("-"))
        if head and line:
            inside = bool(re.search(r"admission|admitted",
                                    line, re.I)) and not \
                re.search(r"did not admit", line, re.I)
            continue
        if inside and line:
            out.append(line.lstrip("-*0123456789. "))
    return out


def check(text: str) -> dict:
    ss = sentences(text)
    m2 = [s for s in ss if re.search(r"booked out|day shift",
                                     s, re.I)
          and not re.search(r"companion|colleague", s, re.I)]
    m3 = [s for s in ss if OUTCOME.search(s)
          and not re.search(r"adjourn|in writing|by friday|"
                            r"no (?:decision|outcome)|not yet|"
                            r"pending|reserved|never had|will (?:consider|"
                            r"confirm|decide)", s, re.I)]
    return {"M1": [s for s in ss if ADMIT.search(s)],
            "M2": m2, "M3": m3,
            "M4": [s for s in ss if INTENT.search(s)],
            "M5": [s for s in admissions_section(text)
                   if MITIG.search(s)]}


def main() -> None:
    rec = RunRecorder("ch30", "minutes")
    h, t = transcript()
    text = f"Allegation: {h['allegation']}\n\n{t}"

    def one(_):
        resp = rec.create(
            max_tokens=1500, system=ASK,
            messages=[{"role": "user", "content": text}],
            thinking=THINK.get(model(), {"type": "disabled"}))
        return "".join(b.text for b in resp.content
                       if b.type == "text")

    with ThreadPoolExecutor(RUNS) as ex:
        got = list(ex.map(one, range(RUNS)))
    rec.print(f"== {model()}: {h['case']}, {RUNS} drafts")
    for i, g in enumerate(got, 1):
        c = check(g)
        flags = [k for k in ("M1", "M2", "M3", "M4", "M5") if c[k]]
        rec.print(f"draft {i}: {' '.join(flags) or 'none'}")
        for k in flags:
            for s in c[k]:
                rec.print(f"  {k}: {s.strip()[:150]}")
        rec.note(run=i, text=g, checks=c)
    rec.save()


if __name__ == "__main__":
    main()
