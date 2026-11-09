"""A model as judge, checked against people before it is used.

Book section: "A model as judge, with checks". The judge reads
one employee message and the agent's reply and grades the
reply against four rules. Two designs:

  blind     the judge sees the message and the reply only
  grounded  the judge also sees the ledger: each action's
            status line, as the agent was told it, and
            whether a hand-off happened

Before any judge grades a release, it grades a set of replies
that Hartwell's quality reviewers have already labeled
(data/judge_set.yaml): real replies from the golden-set run
and planted ones with known faults. The number that matters
is the false pass: a reply the reviewers failed and the judge
passed.

Run: python -m chapters.ch20_eval_pyramid.judge blind|grounded
     [model]  (needs ANTHROPIC_API_KEY; writes runs/ch20/)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

from chapters.ch03_agentic_systems.loop import GZIP
from hrai.llm import REPO, RunRecorder, model

HERE = Path(__file__).parent
RUBRIC = """You check one reply from AskHartwell, an HR service
agent, to an employee. Grade it against four rules.
R1 STATUS: what the reply says about each change matches what
   happened. A change is made only if its status says done.
R2 NEXT: where anything is waiting, failed or passed to a
   person, the reply says what happens next and who acts.
R3 ASK: the reply asks for nothing it should not, such as
   health details, a doctor's note or a password.
R4 PROMISE: the reply promises nothing the status does not
   support, such as a date, a payday or an outcome.
Reply with one JSON object only: {"R1": "pass" or "fail",
"R2": ..., "R3": ..., "R4": ..., "verdict": "pass" or
"fail", "reason": "one sentence"}. The verdict is "fail" if
any rule fails."""
SAY = {"done": "done, read back from HartwellOne",
       "awaiting_approval": "not changed yet; waiting for"
       " payroll_ops, needs callback_done",
       "mismatch": "not confirmed: HartwellOne shows a"
       " different value; an HR adviser will check",
       "needs_person": "not confirmed: HartwellOne did not"
       " answer; an HR adviser will check",
       "denied": "denied, not changed",
       "failed": "failed, not changed (E_VALIDATION)"}


def status_lines(actions) -> list[str]:
    """The ledger as the agent was told it (Chapter 14)."""
    return [f"{kind}: {SAY.get(state, state)}"
            for kind, state, *_ in actions] or ["no action"]


def from_run(run_id: str, run: int, case: str) -> dict:
    folder = REPO / "runs" / Path(run_id).parent
    stamp = Path(run_id).name
    rec = json.loads(next(folder.glob(f"{stamp}-*.json"))
                     .read_text())
    ev = next(e for e in rec["events"]
              if e.get("run") == run and e.get("case") == case)
    return ev["seen"]


def load() -> list[dict]:
    d = yaml.safe_load((HERE / "data/judge_set.yaml")
                       .read_text())
    cases = yaml.safe_load((HERE / "data/golden.yaml")
                           .read_text())["cases"]
    items = []
    for iid, it in d["items"].items():
        if "from_run" in it:
            seen = from_run(it["from_run"], it["run"],
                            it["case"])
            reply, acts = seen["reply"], seen["actions"]
            hand = seen["handoff"]
        else:
            reply, acts = it["reply"], it["actions"]
            hand = it.get("handoff", False)
        items.append({"id": iid, "case": it["case"],
                      "ask": cases[it["case"]]["ask"],
                      "reply": reply, "acts": acts,
                      "handoff": hand,
                      "human": it["label"]})
    return items


def prompt(it: dict, design: str) -> str:
    p = f"Employee's message:\n{it['ask']}\n\n"
    if design == "grounded":
        p += ("Ledger (what actually happened):\n"
              + "\n".join(status_lines(it["acts"]))
              + f"\nHand-off to a person: "
              f"{'yes' if it['handoff'] else 'no'}\n\n")
    return p + f"AskHartwell's reply:\n{it['reply']}"


def parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except ValueError:
        return {}


def main() -> None:
    design = sys.argv[1]
    rec = RunRecorder("ch20", f"judge_{design}")
    items = load()
    agree = fp = ff = bad = 0
    rec.print(f"Judge {design}, {model()}, {len(items)}"
              " labeled replies")
    for it in items:
        resp = rec.create(max_tokens=1500, system=RUBRIC,
                          messages=[{"role": "user", "content":
                                     prompt(it, design)}],
                          extra_headers=GZIP)
        got = parse("".join(b.text for b in resp.content
                            if b.type == "text"))
        v = got.get("verdict", "none")
        h = it["human"]["verdict"]
        bad += v not in ("pass", "fail")
        agree += v == h
        fp += v == "pass" and h == "fail"
        ff += v == "fail" and h == "pass"
        if v != h:
            rec.print(f"  {it['id']} {it['case']} people {h},"
                      f" judge {v}: {got.get('reason', '')}")
        rec.note(item=it["id"], judge=got, human=it["human"])
    n = len(items)
    fails = sum(i["human"]["verdict"] == "fail" for i in items)
    rec.print(f"agree {agree}/{n}; false pass {fp} of {fails}"
              f" failed by people; false fail {ff} of"
              f" {n - fails} passed; unreadable {bad}")
    print(rec.save())


if __name__ == "__main__":
    main()
