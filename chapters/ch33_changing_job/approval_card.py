"""Chapter 33: two designs for the approval card.

Book section "Managers as approvers". The same twelve
proposals for Ruth Okonjo's crew (data/proposals.yaml),
two card designs:
  A summary  the model gets the raw proposal and writes a
             summary with a recommendation, Approve or
             Decline (roughly what card v1 did)
  B checks   code runs the site checks (checks.py); the
             model gets the results and writes a card of
             at most 50 words that names every failed check
             in its first line and makes no recommendation
             (card v2; the supervisor decides)
Graded by code, per card:
  named     every failed check appears in the card
  first     ...and in its first line (B's rule)
  rec       the card recommends a decision
  rec_bad   it recommends Approve on a flagged proposal
Three runs with the default model; one with a second.
Run:  python -m chapters.ch33_changing_job.approval_card
      (needs ANTHROPIC_API_KEY; writes runs/ch33/)
"""
from __future__ import annotations

import json
import re
import sys
import textwrap

from hrai.llm import RunRecorder, model

from .checks import checks, flagged, load

THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
SYS_A = ("You help a field supervisor at a utility services "
         "company approve proposals from an HR agent. Write a "
         "short card summarizing the proposal, then end with "
         "one line: 'Recommendation: Approve' or "
         "'Recommendation: Decline'.")
SYS_B = ("You write approval cards for a field supervisor. "
         "Code has run the site checks and gives you the "
         "results. Write at most 50 words. If any check "
         "failed, the first line must name every failed check "
         "and its detail. Then say what the proposal would do. "
         "Do not recommend approving or declining; the "
         "supervisor decides.")
KEYS = {"crew minimum": ["minimum"], "work order": ["work order"],
        "ticket": ["ticket", "certif"], "rest": ["rest"],
        "balance": ["balance"]}
REC = re.compile(r"recommend|should (be )?(approved|declined)"
                 r"|suggest (approv|declin)", re.I)


def facts(p: dict) -> str:
    return json.dumps({k: v for k, v in p.items()}, indent=1)


def ask(rec: RunRecorder, design: str, p: dict,
        as_of: str) -> str:
    if design == "A":
        sys_, user = SYS_A, "Proposal:\n" + facts(p)
    else:
        res = [{"check": n, "passed": ok, "detail": dt}
               for n, ok, dt in checks(p, as_of)]
        sys_ = SYS_B
        user = ("Proposal:\n" + facts(p) + "\nCheck results:\n"
                + json.dumps(res, indent=1))
    r = rec.create(max_tokens=400, system=sys_,
                   thinking=THINK.get(model(),
                                      {"type": "disabled"}),
                   messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in r.content
                   if b.type == "text").strip()


def grade(text: str, fails: list[str]) -> dict:
    low = text.lower()
    first = low.splitlines()[0] if low else ""
    named = all(any(k in low for k in KEYS[f]) for f in fails)
    in_first = all(any(k in first for k in KEYS[f])
                   for f in fails)
    m = re.search(r"recommendation:\s*(approve|decline)", low)
    rec_ = bool(m) or bool(REC.search(text))
    bad = bool(fails) and bool(m) and m.group(1) == "approve"
    return {"named": named, "first": in_first, "rec": rec_,
            "rec_bad": bad, "words": len(text.split())}


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    d = load()
    rec = RunRecorder("ch33", "approval_card")
    tally = {"A": [], "B": []}
    example = {}
    for run in range(runs):
        for design in ("A", "B"):
            for p in d["proposals"]:
                fails = flagged(p, d["as_of"])
                text = ask(rec, design, p, d["as_of"])
                g = grade(text, fails)
                g.update(id=p["id"], run=run, flagged=bool(fails))
                tally[design].append(g)
                rec.note(design=design, id=p["id"], run=run,
                         card=text, grade=g)
                if run == 0 and p["id"] == "P05":
                    example[design] = text
    rec.print(f"Approval card designs, model {model()}, "
              f"{runs} run(s)")
    rec.print("12 proposals per run, 5 with a failed check")
    rec.print(f"{'measure':36}{'A summary':>11}{'B checks':>11}")
    for label, fn in [
        ("flagged cards naming the failure",
         lambda g: g["flagged"] and g["named"]),
        ("flagged cards naming it in line 1",
         lambda g: g["flagged"] and g["first"]),
        ("cards recommending a decision",
         lambda g: g["rec"]),
        ("Approve recommended on a flagged",
         lambda g: g["rec_bad"])]:
        a = sum(1 for g in tally["A"] if fn(g))
        b = sum(1 for g in tally["B"] if fn(g))
        den = 5 * runs if "flagged" in label else 12 * runs
        rec.print(f"{label:36}{f'{a} of {den}':>11}"
                  f"{f'{b} of {den}':>11}")
    for design in ("A", "B"):
        w = [g["words"] for g in tally[design]]
        rec.print(f"mean words, design {design}: "
                  f"{sum(w) / len(w):.0f}")
    for design in ("A", "B"):
        rec.print(f"--- design {design}, P05, run 1 ---")
        for line in example.get(design, "").splitlines():
            for part in textwrap.wrap(line, 62):
                rec.print(part)
    print(rec.save())


if __name__ == "__main__":
    main()
