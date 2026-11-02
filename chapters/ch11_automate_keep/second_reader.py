"""Chapter 11: a model as second reader of the Automate/Keep Line.

The owners' answers decide the Line. The model reads each step
blind (never the owners' answers), answers the five tests, and
line.place() turns its answers into a placement. Wherever the
model and the owners differ, the step goes to the Line review
panel, a group of named people. The model changes nothing.

Run: python -m chapters.ch11_automate_keep.second_reader
(needs ANTHROPIC_API_KEY; writes runs/ch11/second_reader/...)
"""
from __future__ import annotations

import json
import re
import textwrap
from collections import Counter

from hrai.llm import RunRecorder

from . import line

BATCH = 16
SYSTEM = """You review HR process steps for an employer.
For each step answer five tests with Y or N.
1 Consequence: does the step decide or change a person's
access to work, pay, employment, schedule, standing or legal
status, other than exactly as that person asked?
2 Reversibility: can a wrong result be fully undone within one
business day, before the person bears any cost?
3 Rule: is the outcome fully set by a written rule applied to
system-of-record data, with no weighing of circumstances?
4 Reservation: does a law, collective or works-council
agreement, professional standard or contract reserve the step
for a person or give a right to human review of it?
5 Sensitivity: does the step rest on the person's conduct,
health, a protected characteristic or immigration status?
Judge only from the text given. Reply with a JSON array only:
[{"id": "...", "answers": "YNYNN", "why": "one sentence"}]
"why" names the test you were least sure of and the reason."""


def ask(rec: RunRecorder, batch: list[dict]) -> dict[str, dict]:
    shown = [{k: s[k] for k in ("id", "step", "kind", "facts")}
             for s in batch]
    resp = rec.create(max_tokens=8000, system=SYSTEM, messages=[
        {"role": "user", "content": json.dumps(shown, indent=1)}])
    text = "".join(b.text for b in resp.content if b.type == "text")
    m = re.search(r"\[.*\]", text, re.S)
    try:
        rows = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        rows = []
    out = {}
    for r in rows:
        try:
            out[r["id"]] = {"answers": line.answers(r["answers"]),
                            "why": str(r.get("why", ""))}
        except (KeyError, TypeError, ValueError):
            continue  # malformed row: no answer, so it is routed
    return out


def main() -> None:
    data = line.load()
    steps = data["steps"]
    rec = RunRecorder("ch11", "second_reader")
    model_says: dict[str, dict] = {}
    for i in range(0, len(steps), BATCH):
        model_says.update(ask(rec, steps[i:i + BATCH]))

    owners = Counter(s["placement"].side for s in steps)
    test_diff: Counter = Counter()
    queue, moves = [], Counter()
    for s in steps:
        m = model_says.get(s["id"])
        if m is None:
            queue.append((s, None, "no usable answer"))
            moves["no answer"] += 1
            continue
        for t in line.TESTS:
            if m["answers"][t] != s["owner_answers"][t]:
                test_diff[t] += 1
        mp = line.place(s["kind"], m["answers"])
        if mp != s["placement"]:
            if mp.side == s["placement"].side:
                moves["mode only"] += 1
            else:
                moves[f"to {mp.side}"] += 1
            queue.append((s, mp, m["why"]))

    n = len(steps)
    rec.print(f"Line v{data['version']}: {n} steps, second reader "
              f"{rec.calls[-1]['response']['model']}")
    rec.print(f"Owners: automate {owners['automate']}, "
              f"keep {owners['keep']}")
    rec.print(f"Same placement: {n - len(queue)} of {n}")
    rec.print("Moves the model would make: " + ", ".join(
        f"{k} {moves[k]}" for k in
        ("to keep", "to automate", "mode only", "no answer")))
    rec.print("Test answers that differ: " + ", ".join(
        f"{t} {test_diff[t]}" for t in line.TESTS))
    rec.print(f"Routed to the Line review panel: {len(queue)}")
    for s, mp, why in queue:
        rec.print(f"{s['id']} owners {s['placement']} | "
                  f"model {mp or '-'}")
        for w in textwrap.wrap(why, 58):
            rec.print(f"    {w}")
        rec.note(routed=s["id"], owners=str(s["placement"]),
                 model=str(mp), why=why,
                 to="Line review panel")
    rec.note(model_answers={k: "".join(
        "Y" if v["answers"][t] else "N" for t in line.TESTS)
        for k, v in model_says.items()})
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
