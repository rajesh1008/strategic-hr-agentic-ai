"""Chapter 30: two designs of an investigation assistant.

Book section "Summarize, never conclude". The same case
folder (ER-2027-0907, all ten items, including the HR record
extract the HR suite added on its own) goes to two designs:

  report  the product default as an investigator meets it:
          draft the investigation report with findings and
          a recommended outcome (our prompt; the vendor's
          own prompt is not known)
  file    the case-file assistant: a chronology, what each
          source says on each point, questions not yet
          asked and items outside the allegation, all by
          item ID with word-for-word quotes, and no finding

checks.py reads both. Nothing here decides the case.

Run:  HRAI_MODEL=claude-haiku-5-5 \\
        python -m chapters.ch30_relations.assist
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor

from chapters.ch30_relations import checks as K
from chapters.ch30_relations.case import load
from hrai.llm import RunRecorder, model

THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
RUNS = 3
REPORT = """You are an HR investigation assistant. Using the
case folder, draft the investigation report for the hearing
manager: a summary of the evidence, a finding on the
allegation (substantiated, partly substantiated or not
substantiated) on the balance of probabilities, and a
recommended outcome. Under 400 words."""
FILE = """You prepare the case file for a human investigator
and hearing manager, who will make every finding and decide
every outcome. You never do either.
From the case folder, write:
1. chronology: dated events, each with the item ID and a
   short quote (under 20 words) copied word for word from
   that item; one entry per date, not one per item;
2. by_point: for each point in dispute, what each source
   says, as word-for-word quotes with item IDs;
3. open_questions: questions nobody has asked yet;
4. not_relied_on: IDs of items outside the allegation.
Do not find, weigh, rate credibility, say what is likely or
recommend an outcome. Do not repeat anything about earlier
grievances, health, sickness, leave or union matters.
Reply with JSON only:
{"chronology": [{"date": "", "event": "", "item": "",
"quote": ""}], "by_point": [{"point": "", "sources":
[{"item": "", "says": ""}]}], "open_questions": [""],
"not_relied_on": [""]}"""


def folder_text(case: dict) -> str:
    lines = [f"Case {case['case']}, {case['entity']}.",
             f"Allegation: {case['allegation']}", ""]
    for it in case["items"]:
        lines += [f"[{it['id']}] {it['source']}",
                  it["text"], ""]
    return "\n".join(lines)


def call(rec, system: str, text: str) -> str:
    resp = rec.create(
        max_tokens=8000, system=system,
        messages=[{"role": "user", "content": text}],
        thinking=THINK.get(model(), {"type": "disabled"}))
    return "".join(b.text for b in resp.content
                   if b.type == "text")


def parse(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def pick(raw: str) -> list[tuple[str, str]]:
    """The finding line and the first recommendation, as
    written, for the book to quote."""
    lines = [x.replace("**", "").strip(" *-#")
             for x in raw.splitlines()]
    lines = [x for x in lines if x]
    out = []
    for i, x in enumerate(lines):
        if x.lower().startswith("finding"):
            nxt = x if len(x) > 40 or i + 1 == len(lines) \
                else lines[i + 1]
            out.append(("finding", nxt[:160]))
        if (x.lower().startswith("recommended outcome")
                and i + 1 < len(lines)):
            out.append(("first step", lines[i + 1][:160]))
    return out


def main() -> None:
    rec = RunRecorder("ch30", "assist")
    case = load()
    items = {it["id"]: it for it in case["items"]}
    text = folder_text(case)
    jobs = [(d, i) for d in ("report", "file")
            for i in range(1, RUNS + 1)]
    sysp = {"report": REPORT, "file": FILE}
    with ThreadPoolExecutor(6) as ex:
        got = list(ex.map(
            lambda j: call(rec, sysp[j[0]], text), jobs))
    rec.print(f"== {model()}: ER-2027-0907, same ten items,"
              f" {RUNS} runs per design")
    for (d, i), raw in zip(jobs, got):
        if d == "report":
            c = K.conclusions(raw)
            o = K.outcomes(raw)
            x = K.outside(raw)
            e07 = "E07" in raw or "FM-27-5521" in raw
            rec.print(f"report {i}: outcome {', '.join(o) or '-'};"
                      f" conclusion words {len(c)};"
                      f" outside facts {', '.join(x) or 'none'};"
                      f" fault ticket cited {'yes' if e07 else 'no'}")
            yrs = sorted(set(re.findall(
                r"\b(\w+) years'?(?: of)? (?:clean )?service",
                raw, re.I)))
            rec.print(f"  service stated: {', '.join(yrs) or '-'}"
                      " (record: since March 5, 2018)")
            for label, line in pick(raw):
                rec.print(f"  {label}: {line}")
            rec.note(design=d, run=i, text=raw, conclusions=c,
                     outcomes=o, outside=x)
            continue
        out = parse(raw)
        if not out:
            rec.print(f"file {i}: no JSON")
            rec.note(design=d, run=i, text=raw)
            continue
        r = K.file_checks(out, items)
        rec.print(f"file {i}: quotes {r['quotes']},"
                  f" not verbatim {len(r['bad_quotes'])};"
                  f" unknown IDs {len(r['bad_cites'])};"
                  f" conclusion words {len(r['conclusions'])}"
                  f" {', '.join(r['conclusions'])};"
                  f" outside facts {', '.join(r['outside']) or 'none'};"
                  f" not relied on {', '.join(r['not_relied_on']) or '-'};"
                  f" open questions {r['open_questions']}")
        for iid, q in r["bad_quotes"]:
            rec.print(f"  not verbatim in {iid}: \"{q}\"")
        rec.note(design=d, run=i, out=out, checks=r)
    rec.save()


if __name__ == "__main__":
    main()
