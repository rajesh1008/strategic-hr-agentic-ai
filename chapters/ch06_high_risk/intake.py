"""Chapter 6: a model drafts the AI Act intake, counsel decides.

The model reads each system's description (the words a vendor
or an internal team uses) and answers the classification facts.
It never sees counsel's answers. checker.classify() turns both
sets of facts into a result. Wherever the results differ, the
system goes to counsel with the facts that differ and the
model's note. The model classifies nothing and changes nothing.

Run: python -m chapters.ch06_high_risk.intake
(needs ANTHROPIC_API_KEY; writes runs/ch06/intake/...)
"""
from __future__ import annotations

import json
import re
import textwrap
from collections import Counter

from hrai.llm import RunRecorder

from . import checker

QUESTIONS = {
    "ai_system": "Does it infer outputs (scores, predictions,"
    " content, recommendations) from inputs by machine learning"
    " or similar methods, rather than only apply rules people"
    " wrote?",
    "infers_emotion": "Does it infer a person's emotions or"
    " intentions (for example stress or enthusiasm) from face,"
    " voice or other biometric data?",
    "medical_or_safety": "Is any such inference made for a"
    " medical or safety reason?",
    "recruit_select": "Is it used to recruit or select people:"
    " target job ads, analyze or filter applications, or"
    " evaluate candidates?",
    "work_decisions": "Is it used to make or inform decisions"
    " on terms of work, promotion or termination?",
    "task_allocation": "Does it allocate tasks or shifts based"
    " on individual behavior or personal traits?",
    "monitor_evaluate": "Does it monitor or evaluate the"
    " performance or behavior of workers?",
    "profiling": "Does it evaluate personal aspects of"
    " individuals (performance, reliability, behavior, skills)"
    " from their personal data?",
    "narrow_procedural": "Does it perform only a narrow"
    " procedural task?",
    "improves_human_work": "Does it only improve the result of"
    " an activity a person has already completed?",
    "pattern_check": "Does it only detect patterns or deviations"
    " in past decisions, without replacing or influencing a"
    " person's assessment?",
    "preparatory": "Does it perform only a preparatory task"
    " to an assessment?",
    "materially_influences": "Can its output materially"
    " influence the outcome of a decision about a person?",
}
SYSTEM = (
    "You help an employer's counsel take stock of software used"
    " on its EU workforce. For each system, answer every"
    " question Y or N from the description alone. Do not give"
    " a legal conclusion.\nQuestions:\n"
    + "\n".join(f"{k}: {q}" for k, q in QUESTIONS.items())
    + '\nReply with a JSON array only: [{"id": "...", '
    '"answers": {"<question key>": "Y" or "N", ...}, '
    '"note": "one sentence on the answer you were least sure'
    ' of"}]')
ORDER = ["prohibited", "high-risk", "exempt (document it)",
         "not high-risk", "not an AI system"]


def ask(rec: RunRecorder, systems: list[dict]) -> dict:
    shown = [{"id": s["id"], "name": s["name"],
              "description": s["description"]} for s in systems]
    resp = rec.create(max_tokens=8000, system=SYSTEM, messages=[
        {"role": "user",
         "content": json.dumps(shown, indent=1)}],
        # the box's Brotli is too old for the SDK's decoder
        extra_headers={"Accept-Encoding": "gzip"})
    text = "".join(b.text for b in resp.content
                   if b.type == "text")
    m = re.search(r"\[.*\]", text, re.S)
    try:
        rows = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        rows = []
    out = {}
    for r in rows:
        try:
            a = r["answers"]
            facts = {k: str(a[k]).strip().upper() == "Y"
                     for k in checker.FACTS}
            out[r["id"]] = {"facts": facts,
                            "note": str(r.get("note", ""))}
        except (KeyError, TypeError, AttributeError):
            continue  # malformed: no answer, so it is routed
    return out


def main() -> None:
    systems = checker.load()["systems"]
    rec = RunRecorder("ch06", "intake")
    got = ask(rec, systems)
    same, routed, moves = 0, [], Counter()
    diff_by_fact = Counter()
    for s in systems:
        mine = checker.classify(s["facts"]).label
        g = got.get(s["id"])
        if g is None:
            routed.append((s, mine, "no usable answer", [], ""))
            moves["no answer"] += 1
            continue
        theirs = checker.classify(g["facts"]).label
        diff = [k for k in checker.FACTS
                if g["facts"][k] != s["facts"][k]]
        diff_by_fact.update(diff)
        if theirs == mine:
            same += 1
            continue
        lower = ORDER.index(theirs) > ORDER.index(mine)
        moves["lower" if lower else "higher"] += 1
        routed.append((s, mine, theirs, diff, g["note"]))
    rec.print(f"Intake: {len(systems)} systems, model "
              f"{rec.calls[-1]['response']['model']}")
    rec.print(f"Same result as counsel: {same} of "
              f"{len(systems)}")
    rec.print(f"Model result less strict: {moves['lower']}, "
              f"stricter: {moves['higher']}, "
              f"no answer: {moves['no answer']}")
    top = ", ".join(f"{k} {n}" for k, n in
                    diff_by_fact.most_common())
    lines = textwrap.wrap(f"Facts that differ: {top or 'none'}",
                          60, subsequent_indent="    ")
    for ln in lines:
        rec.print(ln)
    rec.print(f"Routed to counsel: {len(routed)}")
    for s, mine, theirs, diff, note in routed:
        rec.print(f"{s['id']} counsel {mine} | model {theirs}")
        if diff:
            rec.print(f"    differs on: {', '.join(diff)}")
        for ln in textwrap.wrap(note, 56):
            rec.print(f"    {ln}")
        rec.note(system=s["id"], counsel=mine, model=theirs,
                 differs=diff)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
