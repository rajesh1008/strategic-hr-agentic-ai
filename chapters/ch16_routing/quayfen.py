"""Chapter 16: one routing line across three client accounts.

Book section "Quayfen Outsourcing: one threshold, three
clients". Quayfen (synthetic) runs one ticket-sorting agent
for several clients. Each client owns its category list, and
each category has a route: answer, act or person. The agent
names a category and a confidence. The question is whether
one threshold, 0.80, means the same thing on every account.
A person category fails closed whatever the score; a word
guard, written by each client's HR lead, catches tickets the
agent sorted away from a person.

Run:  HRAI_MODEL=claude-haiku-5-5 \\
      python -m chapters.ch16_routing.quayfen
"""
from __future__ import annotations

import random
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from hrai import routing as rt
from hrai.llm import REPO, RunRecorder, model

HERE = Path(__file__).resolve().parent
GZIP = {"Accept-Encoding": "gzip, deflate"}
PER_ACCOUNT = 45
SHARED_AT = 0.80
GUARD = re.compile(
    r"wrong|short|missing|lower than|not on my|breach|"
    r"reference|not renewed|scored|score|recording|"
    r"comments|shouts|inappropriate|punishment", re.I)


def tickets(seed: int = 16) -> list[dict]:
    cfg = yaml.safe_load((HERE / "data" /
                          "quayfen_accounts.yaml").read_text())
    rng = random.Random(seed)
    out = []
    for acct, a in cfg["accounts"].items():
        pool = [(c, t) for c, ts in a["templates"].items()
                for t in ts]
        for i in range(PER_ACCOUNT):
            cat, t = pool[i % len(pool)] if i < len(pool) \
                else rng.choice(pool)
            text = re.sub(r"\{(\w+)\}", lambda m: rng.choice(
                cfg["fills"][m.group(1)]), t)
            out.append({"id": f"{acct[:3]}-{i + 1:03d}",
                        "account": acct, "text": text,
                        "label": cat, "_synthetic": True})
    return out, cfg["accounts"]


def form(cats: dict) -> dict:
    return {"name": "sort_ticket",
            "description": "Record the category for a ticket.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string",
                                 "enum": list(cats)},
                    "confidence": {"type": "number"}},
                "required": ["category", "confidence"]}}


def ask(rec, acct: dict, t: dict) -> dict | None:
    cats = acct["categories"]
    menu = "\n".join(f"{k}: {v['about']}"
                     for k, v in cats.items())
    system = (f"You sort HR tickets for {acct['client']}.\n"
              f"Categories:\n{menu}\nGive the category and "
              "your probability (0.00 to 1.00) that it is "
              "right.")
    resp = rec.create(
        max_tokens=200, system=system,
        messages=[{"role": "user", "content": t["text"]}],
        tools=[form(cats)], thinking={"type": "disabled"},
        tool_choice={"type": "tool", "name": "sort_ticket"},
        extra_headers=GZIP)
    for b in resp.content:
        if b.type == "tool_use":
            return dict(b.input)
    return None


def main() -> None:
    ts, accounts = tickets()
    rec = RunRecorder("ch16", "quayfen")
    with ThreadPoolExecutor(max_workers=6) as pool:
        outs = list(pool.map(
            lambda t: ask(rec, accounts[t["account"]], t), ts))
    rec.print(f"Quayfen ticket sorting on {model()}: "
              f"{len(ts)} tickets, shared line {SHARED_AT}")
    rec.print("account     n  sorted right  agent lane  "
              "right in lane  person sent away  guard caught")
    rows = []
    for t, o in zip(ts, outs):
        cats = accounts[t["account"]]["categories"]
        said = o.get("category") if o else None
        conf = o.get("confidence") if o else None
        line = rt.RoutingLine(
            step="ticket sort", version="1", model=model(),
            complete_at=SHARED_AT, review_at=0.5,
            fail_closed=["person"], review_if=["GUARD"])
        prop = cats.get(said, {}).get("route", "person")
        flags = ["GUARD"] if GUARD.search(t["text"]) else []
        lane, why = rt.route(rt.Case(t["id"], prop, conf,
                                     flags), line)
        rows.append({**t, "said": said, "conf": conf,
                     "lane": lane, "why": why,
                     "truth_route": cats[t["label"]]["route"]})
    for acct in accounts:
        rs = [r for r in rows if r["account"] == acct]
        ok = sum(r["said"] == r["label"] for r in rs)
        inl = [r for r in rs if r["lane"] == "complete"]
        okl = sum(r["said"] == r["label"] for r in inl)
        away = [r for r in rs if r["truth_route"] == "person"
                and accounts[acct]["categories"].get(
                    r["said"], {}).get("route", "person")
                != "person"]
        caught = sum(r["lane"] != "complete" for r in away)
        rec.print(f"{acct:<11}{len(rs):2d}  {ok:2d}"
                  f"            {len(inl):2d}          "
                  f"{okl:2d}             {len(away):2d}"
                  f"                {caught:2d}")
    for r in rows:
        if r["said"] != r["label"] and r["lane"] == "complete":
            rec.print(f"wrong in agent lane: {r['id']} "
                      f"'{r['text']}' -> {r['said']} "
                      f"{r['conf']:.2f} (label {r['label']})")
    rec.note(rows=rows)
    path = rec.save()
    print(f"saved {Path(path).relative_to(REPO)}")


if __name__ == "__main__":
    main()
