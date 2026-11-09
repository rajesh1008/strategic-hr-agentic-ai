"""Chapter 30: drafting the outcome letter from the record.

Book section "Exits and outcome letters". The model gets
the signed case decision record and nothing else, and drafts
the letter to the employee. Code checks the draft against
the record before anyone reads it:

  L1  every date and number in the letter is in the record
  L2  the appeal route (name and window) is stated
  L3  no reason appears that the record does not give
      (checked as words of admission or intent)

Run:  HRAI_MODEL=claude-haiku-5-5 \\
        python -m chapters.ch30_relations.letter
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

import yaml

from chapters.ch30_relations.case import DATA
from hrai.llm import RunRecorder, model

THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
RUNS = 3
ASK = """Draft the outcome letter to the employee from this
signed decision record. Use only what the record says. State
the outcome, the reasons as the decider gave them and the
appeal route. Plain English, under 350 words."""
NUM = re.compile(r"\b\d[\d,.:]*\b")
ADDED = re.compile(r"\b(admit\w*|accepted that|conceded|"
                   r"deliberate\w*|reckless\w*|negligen\w*|"
                   r"careless\w*|dishonest\w*)\b", re.I)


def nums(text: str) -> set[str]:
    return {n.rstrip(".,:").replace(",", "").lstrip("0") or "0"
            for n in NUM.findall(text)}


def check(letter: str, record: dict) -> dict:
    src = yaml.safe_dump(record, sort_keys=False)
    extra = sorted(nums(letter) - nums(src))
    a = record["appeal"]
    return {"L1": extra,
            "L2": a["name"] in letter
                  and str(a["window_days"]) in letter,
            "L3": sorted({m.group(0).lower()
                          for m in ADDED.finditer(letter)})}


def main() -> None:
    rec = RunRecorder("ch30", "letter")
    doc = yaml.safe_load((DATA / "records.yaml").read_text())
    r = next(x for x in doc["records"]
             if x["id"] == "AL-2027-11 v1")
    keep = {k: r[k] for k in ("id", "employer", "decider",
            "allegation", "put_on", "outcome", "reasons",
            "mitigation", "appeal", "decided_on")}
    text = yaml.safe_dump(keep, sort_keys=False)

    def one(_):
        resp = rec.create(
            max_tokens=1200, system=ASK,
            messages=[{"role": "user", "content": text}],
            thinking=THINK.get(model(), {"type": "disabled"}))
        return "".join(b.text for b in resp.content
                       if b.type == "text")

    with ThreadPoolExecutor(RUNS) as ex:
        got = list(ex.map(one, range(RUNS)))
    rec.print(f"== {model()}: letter from {r['id']}, {RUNS} drafts")
    for i, g in enumerate(got, 1):
        c = check(g, keep)
        rec.print(f"draft {i}: numbers not in record "
                  f"{', '.join(c['L1']) or 'none'};"
                  f" appeal route {'stated' if c['L2'] else 'MISSING'};"
                  f" added reasons {', '.join(c['L3']) or 'none'}")
        rec.note(run=i, text=g, checks=c)
    rec.save()


if __name__ == "__main__":
    main()
