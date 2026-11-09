"""Chapter 10: a model reads tickets; the taxonomy routes them.

The model sees a ticket's text and returns a category code and
two flags (sensitive, chasing). It never sees the advisers'
labels, holds no tools and closes nothing. taxonomy.route()
turns its reading into a route, and the result is compared with
the advisers' labels on 60 tickets per route.

Run: python -m chapters.ch10_diagnose.triage
(needs ANTHROPIC_API_KEY; writes runs/ch10/triage/...)
"""
from __future__ import annotations

import json
import random
import re
from collections import Counter

from hrai.llm import RunRecorder

from . import export
from .taxonomy import ROUTES, TAX, gold, route

PER_ROUTE, BATCH = 60, 20
SYSTEM = """You sort HR service tickets for an employer.
For each ticket choose one category code from this list:
{codes}
Also set two flags.
sensitive: true if the text mentions the person's health,
pregnancy, disability, conduct by or toward them, harassment,
safety, a protected characteristic, or immigration status.
chasing: true if the person is following up an earlier request.
Judge only from the text. Reply with a JSON array only:
[{{"id": "...", "category": "...", "sensitive": false,
"chasing": false}}]"""


def stratified(rows: list[dict]) -> list[dict]:
    by: dict[str, list] = {r: [] for r in ROUTES}
    for t in rows:
        by[gold(t["label"], int(t["sensitive"]))].append(t)
    rng = random.Random(1010)
    out = []
    for r in ROUTES:
        out += rng.sample(by[r], PER_ROUTE)
    rng.shuffle(out)
    return out


def read(rec: RunRecorder, batch: list[dict]) -> dict[str, dict]:
    codes = "\n".join(f"{c} {v['name']}" for c, v in TAX.items())
    shown = [{"id": t["ticket_id"], "text": t["text"]}
             for t in batch]
    resp = rec.create(max_tokens=4000,
                      system=SYSTEM.format(codes=codes),
                      messages=[{"role": "user",
                                 "content": json.dumps(shown)}])
    text = "".join(b.text for b in resp.content if b.type == "text")
    m = re.search(r"\[.*\]", text, re.S)
    try:
        rows = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        rows = []
    out = {}
    for r in rows:
        if isinstance(r, dict) and "id" in r:
            out[str(r["id"])] = r
    return out


def main() -> None:
    rec = RunRecorder("ch10", "triage")
    tickets = stratified(export.sample(export.load()))
    seen: dict[str, dict] = {}
    for i in range(0, len(tickets), BATCH):
        seen.update(read(rec, tickets[i:i + BATCH]))
    conf: Counter = Counter()
    unread = 0
    for t in tickets:
        g = gold(t["label"], int(t["sensitive"]))
        m = seen.get(t["ticket_id"])
        if m is None:
            unread += 1
            r = "person"  # no usable reading: fail closed
        else:
            r = route(str(m.get("category")),
                      m.get("sensitive") is True,
                      m.get("chasing") is True)
        conf[(g, r)] += 1
        rec.note(ticket=t["ticket_id"], gold=g, model=r,
                 label=t["label"],
                 read=m.get("category") if m else None)
    p = rec.print
    p(f"Tickets read: {len(tickets)} ({PER_ROUTE} per route), "
      f"model {rec.calls[-1]['response']['model']}")
    p(f"No usable reading (sent to a person): {unread}")
    p("Advisers' route (rows) by the rule's route from the "
      "model's reading:")
    p("          " + "".join(f"{r:>8}" for r in ROUTES))
    for g in ROUTES:
        p(f"  {g:<8}" + "".join(f"{conf[(g, r)]:>8}"
                                for r in ROUTES))
    same = sum(conf[(r, r)] for r in ROUTES)
    p(f"Same route: {same} of {len(tickets)}")
    missed = sum(conf[("person", r)] for r in ROUTES
                 if r != "person")
    p(f"Person tickets the rule would have sent elsewhere: "
      f"{missed} of {PER_ROUTE}")
    extra = sum(conf[(g, "person")] for g in ROUTES
                if g != "person")
    p(f"Tickets sent to a person that the advisers routed "
      f"elsewhere: {extra}")
    for t in tickets:
        g = gold(t["label"], int(t["sensitive"]))
        m = seen.get(t["ticket_id"])
        if g == "person" and m is not None and route(
                str(m.get("category")), m.get("sensitive") is True,
                m.get("chasing") is True) != "person":
            p(f"  MISSED {t['ticket_id']} {t['text'][:70]}")
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
