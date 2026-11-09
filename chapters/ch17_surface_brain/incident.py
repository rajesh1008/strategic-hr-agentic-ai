"""Chapter 17 opening and "What went wrong on June 9": the pay-
band question replayed through the pilot configuration, the
surface check, the pause, and the same question through the
entitled design.

Run: python -m chapters.ch17_surface_brain.incident
(needs ANTHROPIC_API_KEY; writes runs/ch17/incident/...)
"""
from __future__ import annotations

import textwrap

import yaml

from hrai.llm import RunRecorder

from . import assistant, entitled, pilot_log, surfaces
from .entitled import DATA
from .gateway import Gateway, Refused

Q = ("What's the pay band for a senior maintenance technician? "
     "I'm hiring two in Manchester.")
MODEL = "claude-haiku-5-5"


def show(rec, res, docs, user):
    rec.print("Retrieved, in rank order:")
    for i in res["shown"]:
        ok, why = entitled.can_read(user, docs[i])
        rec.print(f"  {i:<10} {docs[i]['entity']:<5} "
                  f"{docs[i]['class']:<8} "
                  f"{'may read' if ok else 'may NOT read: ' + why}")
    d = res["draft"]
    rec.print("Answer drafted:")
    for ln in textwrap.wrap(d["answer"], 62):
        rec.print("  " + ln)
    rec.print(f"Sources cited: {', '.join(d['sources']) or 'none'}")
    rec.print("Checks: " + ("pass" if not res["fails"] else ""))
    for f in res["fails"]:
        rec.print(f"  FAIL {f}")
    rec.print(f"What the person saw: "
              f"{'route to HR' if res['routed'] else 'the answer'}")
    rec.print(f"Unreadable documents in what they saw: "
              f"{', '.join(res['leaks']) or 'none'}")


def main() -> None:
    docs, users = entitled.load("hartwell")
    paul = users["paul"]
    inc = yaml.safe_load((DATA / "hartwell" / "incident.yaml")
                         .read_text())
    rec = RunRecorder("ch17", "incident")
    gw = Gateway.load(rec)
    rec.print("Hartwell Gate replay, June 9, 2027 (synthetic)")
    rec.print(f"User: {paul['name']}, {paul['title']}, "
              f"{paul['site']} (UK, manager)")
    rec.print(f"Question: {Q}")
    rec.print("")
    rec.print("1. Pilot design: one index, no entitlement filter")
    res = assistant.ask(gw, Q, paul, docs, "pilot", "ka.manager",
                        MODEL, caller="svc-knowledge-assistant",
                        surface="teams-ka-pilot")
    show(rec, res, docs, paul)
    e = gw.log[-1]
    rec.print(f"Gate log: use {e['use']} surface {e['surface']} "
              f"status {e['status']} docs {len(e['docs'])} "
              f"tokens {e['tokens_in']}/{e['tokens_out']} "
              f"cost ${e['cost_usd']:.4f}")
    rec.print("")
    rec.print("2. Surface check against use status")
    for p in surfaces.check(gw.uses) or ["no problems"]:
        rec.print("  " + p)
    rec.print("")
    rec.print("3. Pilot questions replayed through retrieval only")
    r = pilot_log.replay("pilot")
    conf = {i: n for i, n in r["by_doc"].items()}
    rec.print(f"  {r['questions']} questions from {r['managers']} "
              f"managers, May 27 to June 9")
    rec.print(f"  with an unreadable document in the context: "
              f"{r['exposed']}")
    rec.print(f"  with an unreadable PERSONAL document: "
              f"{r['personal']}")
    for i, n in sorted(conf.items(), key=lambda x: -x[1]):
        rec.print(f"    {i:<10} {docs[i]['entity']:<5} "
                  f"{docs[i]['class']:<8} {n}")
    rec.print("")
    rec.print("4. Off switch")
    for t, what in inc["timeline"]:
        rec.print(f"  {t}  {what}")
    gw.pause("ka.manager", by="Megan Hale")
    try:
        assistant.ask(gw, Q, paul, docs, "pilot", "ka.manager",
                      MODEL, caller="svc-knowledge-assistant",
                      surface="teams-ka-pilot")
    except Refused:
        pass
    e = gw.log[-1]
    rec.print(f"  next call: {e.get('status')} ({e.get('reason')})")
    rec.print("")
    rec.print("5. Same question, entitled design (test use ka.eval)")
    res2 = assistant.ask(gw, Q, paul, docs, "entitled", "ka.eval",
                         MODEL)
    show(rec, res2, docs, paul)
    rec.note(gateway_log=gw.log, pilot=res, entitled=res2)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
