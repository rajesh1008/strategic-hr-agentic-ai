"""Chapter 16: the screening agent states a confidence.

Book section "What the score said and what happened". The
agent reads one resume against screening guidance v1 and
says whether the applicant meets the posted requirements,
with a confidence. It holds no write tool: Line row A04 is
Keep at recommend (Chapter 11). The run records every
answer so calibrate.py can compare the confidence with the
answer a recruiter reaches under the same guidance.

Two configurations of the same model and the same words:
  fast  the pilot's setting: the answer is forced straight
        into a form (a tool call), with no room to work
  work  the model may think first, then answers in JSON

Run:  HRAI_MODEL=claude-haiku-5-5 \\
      python -m chapters.ch16_routing.screen fast
"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from hrai.llm import REPO, RunRecorder, model

from .make_data import load

HERE = Path(__file__).resolve().parent
GZIP = {"Accept-Encoding": "gzip, deflate"}
# how each model is told not to think before answering
NO_THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
SYSTEM = """You screen applications for a recruiter.
{guidance}
Read the resume and give: epa608 (true or false),
field_months (an integer), meets (true or false),
confidence and evidence (15 words or fewer).
"confidence" is your probability, from 0.00 to 1.00, that
your "meets" answer is the one a careful recruiter applying
this guidance would reach. You recommend only; a recruiter
decides."""
JSON_ONLY = """
Reply with one JSON object with those five keys."""
FORM = {
    "name": "record_screen",
    "description": "Record the answer for one application.",
    "input_schema": {
        "type": "object",
        "properties": {
            "epa608": {"type": "boolean"},
            "field_months": {"type": "integer"},
            "meets": {"type": "boolean"},
            "confidence": {"type": "number"},
            "evidence": {"type": "string"}},
        "required": ["epa608", "field_months", "meets",
                     "confidence", "evidence"]}}


def parse(text: str) -> dict | None:
    m = re.search(r"\{[^{}]*\}\s*(```)?\s*$", text, re.S) \
        or re.search(r"\{.*\}", text, re.S)
    try:
        d = json.loads(m.group(0).rstrip("`").strip()) \
            if m else None
    except json.JSONDecodeError:
        return None
    return d if isinstance(d, dict) and \
        isinstance(d.get("meets"), bool) else None


def ask(rec, system: str, app: dict, config: str
        ) -> dict | None:
    msgs = [{"role": "user", "content": app["resume"]}]
    if config == "fast":
        resp = rec.create(
            max_tokens=400, system=system, messages=msgs,
            thinking=NO_THINK.get(model(),
                                  {"type": "disabled"}),
            tools=[FORM],
            tool_choice={"type": "tool",
                         "name": "record_screen"},
            extra_headers=GZIP)
        for b in resp.content:
            if b.type == "tool_use":
                d = dict(b.input)
                ok = isinstance(d.get("meets"), bool)
                return d if ok else None
        return None
    resp = rec.create(max_tokens=3000,
                      system=system + JSON_ONLY,
                      messages=msgs, extra_headers=GZIP)
    return parse("".join(b.text for b in resp.content
                         if b.type == "text"))


def main(config: str = "fast") -> None:
    guidance = (HERE / "guidance.md").read_text().strip()
    system = SYSTEM.format(guidance=guidance)
    apps = load()
    rec = RunRecorder("ch16", f"screen_{config}")
    errors: dict[str, str] = {}

    def safe(a: dict) -> dict | None:
        try:
            return ask(rec, system, a, config)
        except Exception as e:  # recorded, routed to a person
            errors[a["candidate_id"]] = type(e).__name__
            return None

    with ThreadPoolExecutor(max_workers=6) as pool:
        outs = list(pool.map(safe, apps))
    answers = {a["candidate_id"]: o
               for a, o in zip(apps, outs)}
    bad = sum(o is None for o in outs)
    yes = sum(1 for o in outs if o and o["meets"])
    rec.print(f"screen_{config} on {model()}: {len(apps)} "
              f"applications, {bad} unreadable "
              f"({len(errors)} call errors)")
    rec.print(f"says meets: {yes}; says does not: "
              f"{len(apps) - yes - bad}")
    rec.note(guidance="v1", config=config, answers=answers,
             errors=errors)
    path = rec.save()
    print(f"saved {Path(path).relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fast")
