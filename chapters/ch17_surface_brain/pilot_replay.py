"""The June 9 question replayed ten times through the pilot
design (book section "What went wrong on June 9"). One run is
an anecdote; ten show how often the pilot put another entity's
numbers in front of a Manchester manager.

Run: python -m chapters.ch17_surface_brain.pilot_replay
(needs ANTHROPIC_API_KEY; writes runs/ch17/pilot_replay/...)
"""
from __future__ import annotations

import textwrap

from hrai.llm import RunRecorder

from . import assistant, entitled
from .gateway import Gateway
from .incident import MODEL, Q

RUNS = 10


def main() -> None:
    docs, users = entitled.load("hartwell")
    paul = users["paul"]
    rec = RunRecorder("ch17", "pilot_replay")
    gw = Gateway.load(rec)
    rec.print(f"Pilot design, question K01, {RUNS} runs, {MODEL}")
    rec.print("run  leaked to the person      cited")
    out, first = [], None
    for k in range(1, RUNS + 1):
        r = assistant.ask(gw, Q, paul, docs, "pilot", "ka.eval",
                          MODEL)
        out.append(r)
        rec.print(f"{k:>3}  {', '.join(r['leaks']) or 'none':<24}  "
                  f"{', '.join(r['draft']['sources']) or 'none'}")
        if r["leaks"] and first is None:
            first = k
    n = sum(bool(r["leaks"]) for r in out)
    rec.print(f"Runs that showed another entity's figures: {n} of "
              f"{RUNS}")
    if first:
        rec.print(f"Run {first}, as the manager would have seen it:")
        for ln in textwrap.wrap(out[first - 1]["final"], 62):
            rec.print("  " + ln)
    rec.note(results=out, gateway_log=gw.log)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
