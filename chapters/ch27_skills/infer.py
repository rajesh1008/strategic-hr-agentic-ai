"""Chapter 27: two designs for inferring skills.

Book section "What the volunteers' profiles showed". v1 is
the inventory as first built: a talent-intelligence prompt
reads every document a person wrote (reports and channel
posts, with dates and times) and returns skills with levels
and confidence plus "work-style insights" for the manager.
v2 is the redesign: code passes only reports, with no times;
the model may only suggest catalog skills, each with a quote;
guard.check() refuses anything else; the employee decides.

Run:  HRAI_MODEL=claude-haiku-5-5 \\
      python -m chapters.ch27_skills.infer v1
"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from hrai.llm import RunRecorder, model

from . import guard
from .volunteers import CATALOG, VOLUNTEERS, catalog_text, render

GZIP = {"Accept-Encoding": "gzip, deflate"}
THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}

V1 = """You are a talent intelligence assistant for an
industrial facilities company. Read everything the employee
wrote and build a skills profile for their manager and the
talent team. Use the skills catalog IDs where they fit.
For each skill give a proficiency level from 1 to 5 and a
confidence from 0 to 1. Add short work-style insights and
any development flags the manager should know about.
Reply with JSON only:
{"skills": [{"skill_id": "SK-..", "level": 3,
  "confidence": 0.8, "evidence": "..."}],
 "insights": ["..."], "development_flags": ["..."]}

Skills catalog:
"""

V2 = """You suggest skills for an employee's own skills
profile. The employee will see every suggestion and decide
whether to add it; nothing is shown to anyone else unless
they accept it.
Rules:
- Suggest only skills from the catalog below, by ID.
- Suggest a skill only where a document shows this person
  doing the work themselves. If someone else did it, skip it.
- Each suggestion must quote one sentence from the documents,
  copied exactly, as evidence.
- Do not describe the person: no levels, no traits, no
  comments on hours, health, family, beliefs, leave,
  representation or relationships.
- At most 8 suggestions.
Reply with JSON only:
{"suggestions": [{"skill_id": "SK-..", "quote": "..."}]}

Skills catalog:
"""


def ask(rec: RunRecorder, design: str, p) -> dict:
    system = (V1 if design == "v1" else V2) + catalog_text()
    resp = rec.create(
        max_tokens=1500, system=system,
        messages=[{"role": "user",
                   "content": render(p, design)}],
        thinking=THINK.get(model(), {"type": "disabled"}),
        extra_headers=GZIP)
    text = "".join(b.text for b in resp.content
                   if b.type == "text")
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def main(design: str) -> None:
    rec = RunRecorder("ch27", f"infer_{design}")
    with ThreadPoolExecutor(8) as ex:
        got = list(ex.map(lambda p: ask(rec, design, p),
                          VOLUNTEERS))
    rec.note(design=design, outputs={
        p.pid: g for p, g in zip(VOLUNTEERS, got)})
    rec.print(f"== {model()}: design {design}, "
              f"{len(VOLUNTEERS)} volunteers")
    unparsed = sum(1 for g in got if not g)
    rec.print(f"replies parsed: {len(got) - unparsed} "
              f"of {len(got)}")
    rec.print("scored by chapters.ch27_skills.score")
    rec.save()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v2")
