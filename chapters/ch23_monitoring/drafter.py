"""A model drafts the incident notices; code checks them.

Book section: "Telling people". The drafter gets only the
facts file. It writes the notice to the 37 employees and the
one-paragraph summary for the regulator pack (section RP-1).
Code then holds any draft that uses a number not in the facts,
promises something the facts do not, or leaves out what the
employee needs. A held draft goes to Megan Hale's team; a
passed draft still needs a person's sign-off. The model never
sends anything.

Run: python -m chapters.ch23_monitoring.drafter
(needs ANTHROPIC_API_KEY; writes runs/ch23/drafter/)
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from hrai.llm import RunRecorder, model

DATA = Path(__file__).resolve().parent / "data"
GZIP = {"Accept-Encoding": "gzip, deflate"}
SYSTEM = """You draft incident communications for Hartwell's
HR shared-services team. Use only the facts given. Write two
parts, each under its heading:
NOTICE: a plain notice to each affected employee, under 150
words, from the HR Shared Services team.
SUMMARY: one paragraph, under 120 words, for the incident
record a regulator or auditor may read.
A person will check and send them; you send nothing."""
PROMISES = ["will never", "guarantee", "no impact",
            "fully resolved", "won't happen again",
            "will not happen again", "no risk"]
NEEDS = {"pay date": r"November 19|Friday",
         "nothing to do": r"(need|have) to do nothing|"
                          r"no action|nothing (you need|to do)"
                          r"|do not need to",
         "where to ask": r"AskHartwell|service line|adviser"}


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?::\d+)?", text))


def check(draft: str, facts: str) -> list[str]:
    allowed = numbers(facts)
    problems = [f"number not in facts: {n}"
                for n in sorted(numbers(draft) - allowed)]
    low = draft.lower()
    problems += [f"promise: '{p}'" for p in PROMISES if p in low]
    notice = draft.split("SUMMARY")[0]
    problems += [f"notice lacks {k}" for k, rx in NEEDS.items()
                 if not re.search(rx, notice, re.I)]
    return problems


def main(n: int = 3) -> None:
    facts = "\n".join("- " + f for f in yaml.safe_load(
        (DATA / "inc-2027-031-facts.yaml").read_text())["facts"])
    rec = RunRecorder("ch23", "drafter")
    held = 0
    for k in range(1, n + 1):
        resp = rec.create(max_tokens=1200, system=SYSTEM,
                          **({"thinking": {"type": "between_tools"}}
                             if "sonnet" in model() else {}),
                          messages=[{"role": "user", "content":
                                     "Facts:\n" + facts}],
                          extra_headers=GZIP)
        draft = "".join(b.text for b in resp.content
                        if b.type == "text")
        probs = check(draft, facts)
        held += bool(probs)
        rec.print(f"== draft {k} on {model()}: "
                  + ("HELD" if probs else "passed to a person"))
        for p in probs:
            rec.print(f"  {p}")
        for line in draft.strip().splitlines():
            rec.print(f"  > {line}")
    rec.print(f"held {held} of {n}")
    print(rec.save())


if __name__ == "__main__":
    main()
