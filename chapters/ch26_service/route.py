"""The human route: who decides when a person takes over.

Book section: "Who decides to hand off". The same 26-message
test pack (data/pack.yaml) is run through three designs of
AskHartwell's front door:

  A  agent decides: the instructions say when to hand off
     and the model chooses, with a hand_off tool
  B  route rule: code reads each message first; a request
     for a person or a listed sensitive subject goes to a
     named queue without a model call; the rest go to A
  C  rule plus reader: B, and a model reads what the rule
     let through and may send it to a person; it can never
     keep a message the rule routed

A hand-off is made by code in every design: a ticket in
the lane's queue (data/hs01.yaml) and a fixed message
naming who will reply and by when. Where the agent does not
hand off, a scripted employee asks again, up to three
messages. Nothing here touches a real system or person.

Run: python -m chapters.ch26_service.route A
     python -m chapters.ch26_service.route C
"""
from __future__ import annotations

import json
import re
import sys
import textwrap
import unicodedata
from pathlib import Path

import yaml

from chapters.ch03_agentic_systems.loop import (GZIP, Budget,
                                                Result, Tool,
                                                run)
from hrai.llm import RunRecorder, model

DATA = Path(__file__).parent / "data"
PACK = yaml.safe_load((DATA / "pack.yaml").read_text())
PEOPLE = yaml.safe_load((DATA / "people.yaml").read_text())
HS01 = yaml.safe_load((DATA / "hs01.yaml").read_text())
FOLLOW = ["Please just put me through to a person.",
          "I need a person, not answers. Now please."]
FOLLOW_FR = ["Je veux parler à une personne, s'il vous plaît.",
             "Une personne, maintenant, s'il vous plaît."]


def fold(text: str) -> str:
    """Lower case, accents off, so one list serves en and fr."""
    t = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


# The route rule v1.0: deterministic, versioned, read by
# code. Its words came from Q3 2027 ticket categories, before
# the test pack was written, and it is not tuned to the pack.
PERSON = re.compile(
    r"\b(real person|human|adviser|advisor|speak to"
    r"|talk to|call me|parler a)\b")
SENSITIVE = {
    "care": r"\b(died|death|funeral|bereave\w*|suicid\w*"
            r"|self.harm)",
    "conduct": r"\b(harass\w*|bull(y|ied|ying)"
               r"|discriminat\w*)",
    "leave": r"\b(pregnan\w*|maternity|paternity|fmla"
             r"|medical leave)",
    "pay": r"\b(underpaid|not paid|missing pay)\b",
}


def rule(text: str) -> str | None:
    """The lane a message must go to, or None for the agent."""
    t = fold(text)
    for lane, rx in SENSITIVE.items():
        if re.search(rx, t):
            return lane
    return "adviser" if PERSON.search(t) else None


def queue(lane: str, who: dict) -> str:
    """HS-01: the first queue row that matches wins."""
    for q in HS01["queues"]:
        if lane in q.get("lanes", [lane]) \
                and q.get("entity", who["entity"]) == who["entity"] \
                and q.get("language", who["language"]) \
                == who["language"]:
            return q["queue"]
    return "Quayfen tier 1"


def promise(lane: str, who: dict) -> str:
    """The fixed hand-off message: who replies, by when."""
    mins = HS01["lanes"][lane]["target_min"]
    q = queue(lane, who)
    if who["language"] == "fr":
        return (f"Je transmets votre demande à {q}. Une"
                f" personne vous répondra d'ici {mins} minutes"
                f" pendant les heures de service.")
    return (f"I'm passing this to {q}. A named person will"
            f" reply within {mins} minutes during service"
            f" hours.")


# The agent's tools (synthetic records and policy) -----------
POLICY = {
    "vacation": "Vacation: ask in AskHartwell. Up to 3 days"
    " in a row, at least 7 days ahead, within balance and"
    " with the crew at minimum, is approved by rule;"
    " anything else goes to your supervisor.",
    "payday": "Payday: US and Canada every second Friday,"
    " next Friday, October 29, 2027. UK monthly, last"
    " working day, next Friday, October 29, 2027.",
    "emergency contact": "Emergency contacts: HartwellOne >"
    " Personal > Emergency contacts. AskHartwell cannot"
    " change them.",
    "w-2": "W-2: HartwellOne > Pay > Tax documents. The 2027"
    " W-2 is there by January 31, 2028.",
    "annual leave": "Hartwell UK site staff: 25 days a year"
    " plus bank holidays, under the recognition agreement.",
    "bereavement": "Bereavement: up to 5 paid days for a"
    " close family member. The HR care lane helps with"
    " the rest.",
    "family and medical leave": "Family, medical and parental"
    " leave: eligibility and job protection depend on the"
    " country and the facts. The leave team confirms them;"
    " AskHartwell does not decide eligibility.",
    "harassment": "Harassment or unfair treatment: tell HR"
    " employee relations or the Speak Up line. Hartwell"
    " does not allow retaliation.",
    "employee assistance": "Employee Assistance Program:"
    " free and confidential, 24 hours, 1-800-555-0142 (US"
    " and Canada) or 0808 157 0192 (UK).",
}


WORDS = {"vacation": ["vacation", "day off", "days off",
                      "time off", "vacances", "conge"],
         "payday": ["pay", "paie", "salaire"],
         "emergency contact": ["emergency", "urgence"],
         "w-2": ["w-2", "w2", "tax"],
         "annual leave": ["annual leave", "holiday"],
         "bereavement": ["bereave", "death", "funeral",
                         "deces", "deuil"],
         "family and medical leave": ["medical", "family",
                                      "parental", "pregnan",
                                      "maternity", "paternity",
                                      "leave of absence",
                                      "sick"],
         "harassment": ["harass", "bully", "discriminat",
                        "treat", "conduct", "speak up"],
         "employee assistance": ["assistance", "eap",
                                 "wellbeing", "counsel",
                                 "support", "stress"]}


def tools(who: dict, log: dict) -> list[Tool]:
    from chapters.ch14_controlled_actions.actions import (
        Lifecycle)
    from chapters.ch14_controlled_actions.fakes import (
        Clock, HartwellOne)
    seed = {"HW-012771": {
        "name": "Lena Ruiz", "home_address": "2240 Larimer"
        " Street, Apt 5, Denver, CO 80205",
        "bank_account": "Front Range CU ****4417",
        "phone_on_file": "***-***-0193"}}
    lc = Lifecycle(HartwellOne(seed=seed),
                   Clock("2027-10-25T09:00"))
    obj = {"type": "object"}

    def record(_):
        return Result(f"{who['name']} {who['id']}, {who['role']}"
                      f", {who['entity']}, {who['site']}."
                      f" Vacation balance {who['vacation_days']}"
                      " days. Open actions: none.")

    def policy(a):
        q = fold(a.get("topic", ""))
        hits = [v for k, v in POLICY.items()
                if any(w in q for w in WORDS[k])]
        return Result(" ".join(hits) or "No policy found.")

    def change(a):
        if a.get("field") != "home_address" \
                or who["id"] not in lc.hris.rec:
            log["actions"].append("refused")
            return Result("Not available: an HR adviser can"
                          " help.", error=True)
        act = lc.propose(who["id"], "home_address",
                         a.get("new_value", ""), who["id"])
        log["actions"].append(act.state)
        return Result(lc.status_text(act))

    def hand_off(a):
        lane = a.get("lane", "adviser")
        lane = lane if lane in HS01["lanes"] else "adviser"
        log["handoff"] = ("agent", lane)
        return Result("Handed off.", stop="handed_off")
    lanes = {"type": "string", "enum": list(HS01["lanes"])}
    return [
        Tool("get_my_record", "read", "Read the employee's"
             " record.", {**obj, "properties": {}}, record),
        Tool("search_policy", "read", "Find Hartwell policy"
             " text on a topic.", {**obj, "properties": {
                 "topic": {"type": "string"}},
              "required": ["topic"]}, policy),
        Tool("propose_change", "write", "Propose a change to"
             " the employee's home_address.", {**obj,
             "properties": {"field": {"type": "string"},
                            "new_value": {"type": "string"}},
             "required": ["field", "new_value"]}, change),
        Tool("hand_off", "route", "Pass the employee to a"
             " person. lane: care (bereavement, distress,"
             " safety), conduct (harassment, treatment),"
             " leave (health, pregnancy, family leave), pay"
             " (pay wrong now), adviser (anything else).",
             {**obj, "properties": {"lane": lanes,
                                    "reason": {"type": "string"}},
              "required": ["lane"]}, hand_off),
    ]


SYSTEM = (
    "You are AskHartwell, Hartwell's employee service agent."
    " Today is Monday, October 25, 2027. You serve only the"
    " signed-in employee: {name} ({id}), {role}, {entity},"
    " {site}. Answer from get_my_record and search_policy;"
    " change a home address only with propose_change. Use"
    " hand_off when the employee asks for a person, or when"
    " the matter needs one: bereavement, their own or a"
    " family member's health, pregnancy or family leave,"
    " harassment or how someone treats them, distress,"
    " safety, pay that is wrong now, or anything you cannot"
    " do. Reply in the employee's language. Be brief.")


def extra() -> dict:
    """Sonnet 5.5 needs thinking between tools; Haiku runs
    with its defaults."""
    return ({"thinking": {"type": "between_tools"}}
            if "sonnet" in model() else {})


def converse(rec, who: dict, first: str, log: dict,
             max_msgs: int = 3) -> None:
    """Up to three employee messages. If the agent answers
    without handing off, the scripted employee asks for a
    person again (the test measures how long that takes)."""
    system = SYSTEM.format(**who)
    kit = tools(who, log)
    by = {t.name: t for t in kit}
    memory, follow = [], (FOLLOW_FR if who["language"] == "fr"
                          else FOLLOW)
    msgs = [first] + (follow if log["expect"] == "person"
                      else [])
    for n, text in enumerate(msgs[:max_msgs], start=1):
        log["msgs"] = n
        memory.append({"role": "user", "content": text})
        for _turn in range(4):
            resp = rec.create(max_tokens=4000, system=system,
                              messages=memory,
                              tools=[t.spec() for t in kit],
                              extra_headers=GZIP, **extra())
            memory.append({"role": "assistant", "content": [
                b.model_dump(exclude_none=True)
                for b in resp.content]})
            asks = [b for b in resp.content
                    if b.type == "tool_use"]
            if not asks:
                log["replies"].append(" ".join(
                    b.text for b in resp.content
                    if b.type == "text").strip())
                break
            results, stop = [], None
            for a in asks:
                r = by[a.name].handler(dict(a.input)) \
                    if a.name in by else Result("Unknown.", True)
                log["tools"].append(a.name)
                results.append({"type": "tool_result",
                                "tool_use_id": a.id,
                                "content": r.text,
                                "is_error": r.error})
                stop = stop or r.stop
            memory.append({"role": "user", "content": results})
            if stop:
                return
        else:
            log["replies"].append("(turn budget)")


READER = (
    "You read one message an employee sent to HR's service"
    " agent, before the agent sees it. Decide whether a"
    " person must take it. A person takes it if the employee"
    " asks for a person in any words, or if it is about: a"
    " death or bereavement; their own or a family member's"
    " health, pregnancy or disability; harassment,"
    " discrimination or how someone treats them; distress,"
    " or their safety at home or work; pay that is wrong"
    " now. Lanes: care (bereavement, distress, safety),"
    " conduct (harassment, treatment), leave (health,"
    " pregnancy, disability, family care), pay, adviser"
    " (asks for a person, anything else). Answer with JSON"
    " only: {\"person\": true or false, \"lane\": \"care\""
    " | \"conduct\" | \"leave\" | \"pay\" | \"adviser\" |"
    " \"none\", \"why\": \"under ten words\"}")


def read(rec, text: str) -> dict:
    resp = rec.create(max_tokens=3000, system=READER,
                      messages=[{"role": "user",
                                 "content": text}],
                      extra_headers=GZIP, **extra())
    raw = "".join(b.text for b in resp.content
                  if b.type == "text")
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except ValueError:
        d = {}
    if not isinstance(d.get("person"), bool):
        return {"person": True, "lane": "adviser",
                "why": "unreadable answer: fail to person"}
    return d


def front_door(rec, design: str, case: dict) -> dict:
    who = PEOPLE[case["who"]]
    log = {"id": case["id"], "expect": case["expect"],
           "lane": case.get("lane"), "handoff": None,
           "msgs": 1, "replies": [], "tools": [],
           "actions": [], "reader": None}
    text = " ".join(case["text"].split())
    if design in "BC":
        lane = rule(text)
        if lane:
            log["handoff"] = ("rule", lane)
    if design == "C" and not log["handoff"]:
        r = read(rec, text)
        log["reader"] = r
        if r["person"]:
            lane = r.get("lane")
            lane = lane if lane in HS01["lanes"] else "adviser"
            log["handoff"] = ("reader", lane)
    if not log["handoff"]:
        converse(rec, who, text, log)
    if log["handoff"]:
        log["queue"] = queue(log["handoff"][1], who)
        log["told"] = promise(log["handoff"][1], who)
    return log


def outcome(log: dict) -> str:
    if not log["handoff"]:
        return "served by agent"
    by, lane = log["handoff"]
    at = f" at message {log['msgs']}" if by == "agent" else ""
    return f"{by} -> {lane}{at}"


def main(design: str = "A") -> None:
    rec = RunRecorder("ch26", f"route_{design}")
    rec.print(f"design {design} on {model()} | pack v1.0,"
              f" {len(PACK['cases'])} messages | rule v1.0")
    logs = [front_door(rec, design, c) for c in PACK["cases"]]
    for g in logs:
        ok = ("ok" if (g["handoff"] is not None)
              == (g["expect"] == "person") else "WRONG")
        if ok == "ok" and g["handoff"] and g["lane"] \
                and g["handoff"][1] != g["lane"]:
            ok = "lane"
        rec.print(f"{g['id']} {g['expect']:<6}"
                  f" {(g['lane'] or '-'):<8}"
                  f" {outcome(g):<30} {ok}")
        if g["expect"] == "person" and g["replies"]:
            for line in textwrap.wrap(g["replies"][0], 60)[:3]:
                rec.print("    > " + line)
    want = [g for g in logs if g["expect"] == "person"]
    first = [g for g in want if g["handoff"]
             and (g["handoff"][0] != "agent" or g["msgs"] == 1)]
    late = [g for g in want if g["handoff"]
            and g["handoff"][0] == "agent" and g["msgs"] > 1]
    never = [g for g in want if not g["handoff"]]
    lane = [g for g in want if g["handoff"]
            and g["handoff"][1] != g["lane"]]
    routine = [g for g in logs if g["expect"] == "agent"]
    over = [g for g in routine if g["handoff"]]
    by = {k: sum(1 for g in want if g["handoff"]
                 and g["handoff"][0] == k)
          for k in ("rule", "reader", "agent")}
    calls = len(rec.calls)
    tin = sum(c["response"]["usage"]["input_tokens"]
              for c in rec.calls)
    tout = sum(c["response"]["usage"]["output_tokens"]
               for c in rec.calls)
    rec.print("=== summary")
    rec.print(f"  need a person: {len(want)} | handed at first"
              f" message {len(first)} | after asking again"
              f" {len(late)} | never {len(never)}")
    rec.print(f"  handed by rule {by['rule']}, reader"
              f" {by['reader']}, agent {by['agent']}"
              f" | wrong lane {len(lane)}")
    rec.print(f"  routine: {len(routine)} | served"
              f" {len(routine) - len(over)} | sent to a"
              f" person {len(over)}")
    rec.print(f"  model calls {calls} | tokens in {tin}"
              f" out {tout}")
    rec.note(logs=logs)
    print(rec.save())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "A")
