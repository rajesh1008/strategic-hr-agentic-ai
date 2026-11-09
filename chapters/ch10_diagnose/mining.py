"""Chapter 10: process mining on HR service events.

An event log has three columns that matter: a case ID, an
activity and a timestamp. From them this module rebuilds every
request's path, counts the paths (variants) and measures what
happened at the end. No model is used.

Time-to-nothing: for an AskHartwell conversation that ended with
no accepted answer, no ticket and no change, the minutes from the
first message to the last event.

Run: HRAI_MODEL=no-model python -m chapters.ch10_diagnose.mining
"""
from __future__ import annotations

import csv
import gzip
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def load(path: Path = DATA / "events.csv.gz") -> dict[str, list]:
    cases: dict[str, list] = defaultdict(list)
    with gzip.open(path, "rt") as f:
        for r in csv.DictReader(f):
            r["t"] = datetime.fromisoformat(r["ts"])
            cases[r["case_id"]].append(r)
    for evs in cases.values():
        evs.sort(key=lambda e: e["t"])
    return cases


def path(evs: list) -> tuple[str, ...]:
    return tuple(e["activity"] for e in evs)


def ending(evs: list) -> str:
    """How a request ended, read from its events only."""
    acts = path(evs)
    if "Ticket created" in acts:
        if acts[-1] == "Closed, no response":
            return "ticket closed, no response"
        return "ticket resolved"
    if acts[-1] == "Answer accepted":
        return "bot answer accepted"
    if acts[-1] == "Handoff promised":
        return "nothing: handoff promised, no ticket"
    return "nothing: abandoned"


def minutes(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 60


def time_to_nothing(cases: dict) -> list[float]:
    out = []
    for evs in cases.values():
        if evs[0]["activity"] == "Chat opened" and \
                ending(evs).startswith("nothing"):
            out.append(minutes(evs[0]["t"], evs[-1]["t"]))
    return out


def ping_pong(evs: list) -> bool:
    acts = path(evs)
    return "Routed back to tier 1" in acts


def summary(cases: dict) -> dict:
    chats = [c for c in cases.values()
             if c[0]["activity"] == "Chat opened"]
    ends = Counter(ending(c) for c in cases.values())
    chat_ends = Counter(ending(c) for c in chats)
    no_ticket = sum(1 for c in chats
                    if "Ticket created" not in path(c))
    ttn = time_to_nothing(cases)
    promised = sum(1 for c in chats if "Handoff promised" in path(c))
    tickets = [c for c in cases.values()
               if "Ticket created" in path(c)]
    return {
        "cases": len(cases),
        "events": sum(len(c) for c in cases.values()),
        "variants": len({path(c) for c in cases.values()}),
        "chats": len(chats),
        "tickets": len(tickets),
        "ends": ends, "chat_ends": chat_ends,
        "containment": no_ticket / len(chats),
        "bot_resolved": chat_ends["bot answer accepted"] / len(chats),
        "ttn_n": len(ttn), "ttn_mean": st.mean(ttn),
        "ttn_median": st.median(ttn),
        "ttn_p90": st.quantiles(ttn, n=10)[-1],
        "promised": promised,
        "false_handoffs": chat_ends[
            "nothing: handoff promised, no ticket"],
    }


def by_site(cases: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for evs in cases.values():
        acts = path(evs)
        if "Ticket created" not in acts or \
                acts[-1] == "Closed, no response":
            continue
        site = next(e["team"].split()[-1] for e in evs
                    if e["team"].startswith("Meridian"))
        start = next(e["t"] for e in evs
                     if e["activity"] == "Ticket created")
        pick = next(e["t"] for e in evs
                    if e["activity"] == "Tier 1 picked up")
        s = out.setdefault(site, {"n": 0, "pp": 0, "first": [],
                                  "days": [], "hops": []})
        s["n"] += 1
        s["pp"] += ping_pong(evs)
        s["first"].append(minutes(start, pick) / 60)
        s["days"].append(minutes(start, evs[-1]["t"]) / 1440)
        s["hops"].append(len({e["team"] for e in evs
                              if e["team"] not in
                              ("AskHartwell", "Desk", "Employee")}))
    return out


def follows(cases: dict) -> Counter:
    """Directly-follows counts: how often activity b came next
    after activity a in the same case."""
    df: Counter = Counter()
    for evs in cases.values():
        acts = path(evs)
        for a, b in zip(acts, acts[1:]):
            df[(a, b)] += 1
    return df


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def main() -> None:
    from hrai.llm import RunRecorder
    rec = RunRecorder("ch10", "mining")
    cases = load()
    s = summary(cases)
    p = rec.print
    p(f"Event log: {s['cases']:,} requests, {s['events']:,} events,"
      f" {s['variants']:,} distinct paths")
    p(f"AskHartwell conversations: {s['chats']:,}; "
      f"tickets: {s['tickets']:,}")
    p("How AskHartwell conversations ended:")
    for k, v in s["chat_ends"].most_common():
        p(f"  {k:<38}{v:>6,}  {pct(v / s['chats'])}")
    p(f"Containment as the bot reports it: {pct(s['containment'])}")
    p(f"Answered by the bot and accepted:  {pct(s['bot_resolved'])}")
    p(f"Handoffs promised: {s['promised']:,}; no ticket created: "
      f"{s['false_handoffs']:,} "
      f"({pct(s['false_handoffs'] / s['promised'])})")
    p(f"Time-to-nothing, {s['ttn_n']:,} conversations:")
    p(f"  mean {s['ttn_mean']:.1f} min, median "
      f"{s['ttn_median']:.1f}, 90th percentile {s['ttn_p90']:.1f}")
    p(f"  employee hours spent: "
      f"{s['ttn_n'] * s['ttn_mean'] / 60:,.0f}")
    top = Counter(path(c) for c in cases.values()).most_common(5)
    p("Five most common paths:")
    for v, n in top:
        p(f"  {n:>6,}  " + " > ".join(v))
    p("Tickets resolved, by Meridian site:")
    for site, d in sorted(by_site(cases).items()):
        p(f"  {site:<7} {d['n']:>6,} tickets; ping-pong "
          f"{pct(d['pp'] / d['n'])}")
        p(f"          first pick-up median "
          f"{st.median(d['first']):.1f} h; resolved median "
          f"{st.median(d['days']):.1f} days")
    rec.note(summary={k: v for k, v in s.items()
                      if not isinstance(v, Counter)},
             chat_ends=dict(s["chat_ends"]), ends=dict(s["ends"]))
    rec.note(follows=[[a, b, n] for (a, b), n in
                      follows(cases).most_common()])
    rec.note(ttn_minutes=sorted(round(x, 1)
                                for x in time_to_nothing(cases)))
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
