"""Chapter 22: crew allocation for Hartwell Energy Services,
in shadow beside the dispatchers.

Book section "Hartwell Energy Services: shadow beside the
dispatch board". For two weeks of substation maintenance
work orders in Texas and Colorado (synthetic), an agent
proposes a lead technician for each order while the
dispatchers assign as they always have. Nothing the agent
proposes is sent. Code then checks both against the same
rules:

  CERT    every certification the order needs is valid on
          the LAST day of the job, not only today
  HOURS   booked hours that week plus the job stay at or
          under 60
  INDUCT  the technician holds the site owner's induction,
          where the site requires one
and compares travel miles. The agent is given what the
learning system holds (certifications and expiry dates) and
the dispatch board (hours, miles). Site inductions live in a
dispatcher's spreadsheet, not in any system of record, so
the agent is not given them: that is what shadow is for.

Run:  python -m chapters.ch22_shadow_gates.crew
      (needs ANTHROPIC_API_KEY; writes runs/ch22/crew/)
"""
from __future__ import annotations

import json
import random
import re
from datetime import date, timedelta

from hrai.llm import RunRecorder, model

GZIP = {"Accept-Encoding": "gzip, deflate"}
THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
SEED = 2207
TODAY = date(2027, 7, 30)          # orders cut on a Friday
CERTS = ["HV switching", "NFPA 70E", "confined space",
         "relay testing"]
BASES = {"Houston": "TX", "Dallas": "TX", "Denver": "CO"}
SITES = [("Baytown 138kV", "Houston", True),
         ("Pasadena 69kV", "Houston", False),
         ("Katy 345kV", "Houston", True),
         ("Mesquite 138kV", "Dallas", False),
         ("Denton 69kV", "Dallas", True),
         ("Waco 138kV", "Dallas", False),
         ("Aurora 115kV", "Denver", False),
         ("Brighton 230kV", "Denver", True),
         ("Pueblo 115kV", "Denver", False)]
SYSTEM = (
    "You propose a lead technician for one substation work"
    " order for Hartwell Energy Services dispatch. Rules, in"
    " order: (1) the technician holds every certification the"
    " order needs, valid on every day of the job, including"
    " the last day; (2) hours already booked that week plus"
    " the job's hours must not exceed 60; (3) among those who"
    " pass, prefer the fewest travel miles. If nobody passes,"
    " say so. Reply with JSON only: {\"tech\": \"<id or"
    " none>\", \"reason\": \"<one sentence>\"}.")


def make() -> tuple[list[dict], list[dict]]:
    rng = random.Random(SEED)
    techs = []
    for i in range(18):
        base = list(BASES)[i % 3]
        certs = {}
        for c in CERTS:
            if rng.random() < 0.7 or c == "NFPA 70E":
                certs[c] = (TODAY + timedelta(
                    days=rng.choice([5, 9, 60, 90, 120, 200,
                                     250, 300, 400, 500, 600,
                                     700, 800, 900]))
                            ).isoformat()
        techs.append({
            "id": f"HES-T{i + 1:02d}", "base": base,
            "certs": certs,
            "inductions": [s for s, b, need in SITES
                           if need and (b == base and
                                        rng.random() < 0.6
                                        or rng.random() < 0.1)]
        })
    orders = []
    for j in range(40):
        site, base, need = rng.choice(SITES)
        start = date(2027, 8, 2) + timedelta(
            days=rng.choice([0, 1, 2, 3, 7, 8, 9, 10]))
        days = rng.choice([1, 1, 2, 3])
        want = ["NFPA 70E"] + rng.sample(
            ["HV switching", "confined space", "relay testing"],
            rng.choice([1, 1, 2]))
        board = []
        for t in techs:
            far = 0 if t["base"] == base else (
                250 if BASES[t["base"]] == BASES[base] else 1050)
            board.append({"id": t["id"],
                          "miles": far + rng.randint(5, 60),
                          "booked": rng.choice(
                              [10, 20, 30, 40, 40, 50])})
        orders.append({"id": f"WO-27-{4100 + j}", "site": site,
                       "induction": need, "start":
                       start.isoformat(), "days": days,
                       "hours": 10 * days, "needs": want,
                       "board": board})
    return techs, orders


def rules(o: dict, tid: str, techs: dict) -> list[str]:
    if tid in (None, "none"):
        return ["NONE"]
    t, b = techs[tid], {x["id"]: x for x in o["board"]}[tid]
    last = date.fromisoformat(o["start"]) + timedelta(
        days=o["days"] - 1)
    bad = []
    if any(c not in t["certs"] or
           date.fromisoformat(t["certs"][c]) < last
           for c in o["needs"]):
        bad.append("CERT")
    if b["booked"] + o["hours"] > 60:
        bad.append("HOURS")
    if o["induction"] and o["site"] not in t["inductions"]:
        bad.append("INDUCT")
    return bad


def dispatcher(o: dict, techs: dict) -> str:
    """What the board shows a dispatcher on the Friday:
    certifications valid TODAY, inductions from the
    spreadsheet, a habit of calling the base's regular lead
    (the first two IDs at that base) before looking at
    hours."""
    site_base = next(b for s, b, _ in SITES if s == o["site"])
    ok = []
    for x in sorted(o["board"], key=lambda x: x["miles"]):
        t = techs[x["id"]]
        if all(c in t["certs"] and date.fromisoformat(
                t["certs"][c]) >= TODAY for c in o["needs"]) \
                and (not o["induction"]
                     or o["site"] in t["inductions"]):
            ok.append(x["id"])
    regulars = [t for t in techs.values()
                if t["base"] == site_base][:2]
    for r in regulars:
        if r["id"] in ok:
            return r["id"]
    return ok[0] if ok else "none"


def prompt(o: dict, techs: dict) -> str:
    lines = [f"Work order {o['id']} at {o['site']}: starts"
             f" {o['start']}, {o['days']} day(s), {o['hours']}"
             f" hours. Needs: {', '.join(o['needs'])}.",
             "Candidates (certification: valid until; hours"
             " booked that week; travel miles):"]
    for x in o["board"]:
        t = techs[x["id"]]
        c = "; ".join(f"{k}: {v}" for k, v in t["certs"].items())
        lines.append(f"- {x['id']} | {c} | booked"
                     f" {x['booked']} | {x['miles']} miles")
    return "\n".join(lines)


def ask(rec, text: str) -> tuple[str | None, str]:
    resp = rec.create(max_tokens=400, system=SYSTEM,
                      messages=[{"role": "user",
                                 "content": text}],
                      thinking=THINK.get(model(),
                                         {"type": "disabled"}),
                      extra_headers=GZIP)
    raw = "".join(b.text for b in resp.content
                  if b.type == "text")
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        j = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        j = {}
    return j.get("tech"), j.get("reason", raw[:120])


def main() -> None:
    rec = RunRecorder("ch22", "crew")
    tl, orders = make()
    techs = {t["id"]: t for t in tl}
    tally = {"agent": {}, "dispatcher": {}}
    miles = {"agent": 0, "dispatcher": 0}
    same = 0
    rec.print(f"Energy Services crew shadow, {len(orders)}"
              f" orders, {model()}; nothing sent")
    for o in orders:
        a, why = ask(rec, prompt(o, techs))
        d = dispatcher(o, techs)
        ra, rd = rules(o, a, techs), rules(o, d, techs)
        b = {x["id"]: x["miles"] for x in o["board"]}
        for who, t, r in (("agent", a, ra),
                          ("dispatcher", d, rd)):
            for f in r:
                tally[who][f] = tally[who].get(f, 0) + 1
            miles[who] += b.get(t, 0)
        same += a == d
        rec.print(f"{o['id']} agent {a} {','.join(ra) or 'ok'}"
                  f" | dispatcher {d} {','.join(rd) or 'ok'}")
        rec.note(order=o["id"], agent=a, reason=why,
                 dispatcher=d, agent_rules=ra,
                 dispatcher_rules=rd)
    rec.print("=== shadow comparison")
    rec.print(f"same technician: {same} of {len(orders)}")
    for who in ("agent", "dispatcher"):
        t = tally[who]
        rec.print(f"{who}: CERT {t.get('CERT', 0)}, HOURS"
                  f" {t.get('HOURS', 0)}, INDUCT"
                  f" {t.get('INDUCT', 0)}, none"
                  f" {t.get('NONE', 0)}; miles {miles[who]}")
    rec.note(summary={"same": same, "tally": tally,
                      "miles": miles, "orders": len(orders)})
    print(rec.save())


if __name__ == "__main__":
    main()
