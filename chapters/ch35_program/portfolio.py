"""Chapter 35: the portfolio board (deterministic).

Book section "One board for the whole program". Each row is
a workstream of the Hartwell agentic HR program (synthetic)
with the dated events the book has already recorded: gates
passed, gates refused, returns to an earlier gate, go-lives,
pauses and decision records. The board is computed from the
events as of a date, never typed: where each row stands,
what moved it last, and the program totals.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch35_program.portfolio
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
GATES = ["Intent", "Build", "Shadow", "Production", "Scale"]
DATES = [date(2027, 3, 31), date(2027, 9, 30),
         date(2028, 3, 31), date(2028, 6, 30)]


def load() -> dict:
    return yaml.safe_load(
        (HERE / "data" / "portfolio.yaml").read_text())


def events(row: dict, upto: date | None = None) -> list[dict]:
    ev = sorted(row["events"], key=lambda e: e["date"])
    return [e for e in ev if upto is None or e["date"] <= upto]


def position(row: dict, on: date) -> str:
    """Where a row stands on a date, from its events only."""
    pos = "not started"
    for e in events(row, on):
        k = e["kind"]
        if k == "gate":
            pos = e["gate"]
        elif k in ("refuse", "back"):
            pos = e["to"]
        elif k == "live":
            pos = "live"
        elif k == "stop" and pos != "live":
            pos = "paused"
        elif k == "decide" and pos == "not started":
            pos = "decided"
        elif k == "plan" and pos == "not started":
            pos = "planned"
    if pos == "decided" and row.get("stage") == "refused":
        pos = "refused by design"
    return pos


def returns(row: dict, upto: date | None = None) -> list[dict]:
    return [e for e in events(row, upto)
            if e["kind"] in ("refuse", "back")]


def day(e: dict) -> str:
    d = e["date"]
    return d.strftime("%b %Y") if e.get("month") \
        else d.strftime("%b %d, %Y").replace(" 0", " ")


def main() -> None:
    p = load()
    rec = RunRecorder("ch35", "portfolio")
    rows = p["rows"]
    rec.print(f"== {p['program']}: {len(rows)} rows")
    for on in DATES:
        c = Counter(position(r, on) for r in rows)
        order = ["not started", "planned", "decided",
                 *GATES, "paused", "live",
                 "refused by design"]
        parts = [f"{k} {c[k]}" for k in order if c[k]]
        rec.print(f"{on.isoformat()}: " + ", ".join(parts))
    end = DATES[-1]
    rec.print("")
    rec.print(f"== board on {end.isoformat()}")
    for r in rows:
        last = events(r, end)[-1]
        tag = last.get("ref") or last.get("note") or last["kind"]
        rec.print(f"{r['id']} {position(r, end):<18}"
                  f" {r['name'][:34]:<34} {day(last)} {tag}")
    rec.print("")
    rec.print("== returns to an earlier gate")
    back = [(r, e) for r in rows for e in returns(r)]
    for r, e in sorted(back, key=lambda x: x[1]["date"]):
        how = (f"refused at {e['gate']}" if e["kind"] == "refuse"
               else "sent back")
        rec.print(f"{day(e)}: {r['id']} {how}, to {e['to']}"
                  f" ({e.get('ref') or e.get('note') or '-'})")
    refused = sum(e["kind"] == "refuse" for _, e in back)
    rec.print(f"returns {len(back)} (gate refusals {refused}),"
              f" on {len({r['id'] for r, _ in back})} rows")
    drs = sorted({e["ref"] for r in rows for e in r["events"]
                  if str(e.get("ref", "")).startswith("DR-")})
    rec.print(f"decision records on the board {len(drs)}")
    rec.print("")
    rec.print("== Shadow gate to Production gate")
    for r in rows:
        ev = events(r)
        prod = [e for e in ev if e["kind"] == "gate"
                and e["gate"] == "Production"]
        if not prod:
            continue
        sh = [e for e in ev if e["kind"] == "gate"
              and e["gate"] == "Shadow"
              and e["date"] < prod[0]["date"]]
        w = (prod[0]["date"] - sh[-1]["date"]).days / 7
        rec.print(f"{r['id']} {day(sh[-1])} to {day(prod[0])}:"
                  f" {w:.0f} weeks")
    rec.note(rows=len(rows), returns=len(back), refused=refused,
             drs=drs)
    rec.save()


if __name__ == "__main__":
    main()
