"""Chapter 35: the Hand-Over Board.

Book section "The Hand-Over Board". Each service on the board
moves from the team that built it to the team that will run
it. A check either applies (all ten for a handed-over service;
the five retained checks for a managed service) or it does not,
and an applying check is open or closed on each review date.
The board prints a grid and the open items. Statuses are
synthetic.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch35_program.handover
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent


def load() -> dict:
    p = HERE / "data" / "handover.yaml"
    return yaml.safe_load(p.read_text())


def applies(svc: dict, board: dict) -> list[str]:
    if svc["model"] == "managed":
        return list(board["retained"])
    return list(board["checks"])


def grid(board: dict, date: str) -> list[dict]:
    rows = []
    for s in board["services"]:
        app = applies(s, board)
        op = s["open"].get(date) or {}
        bad = [c for c in op if c not in app]
        assert not bad, (s["id"], bad)
        rows.append({"id": s["id"], "name": s["name"],
                     "model": s["model"], "applies": app,
                     "open": op})
    return rows


def cell(c: str, r: dict) -> str:
    if c not in r["applies"]:
        return "."
    return "X" if c in r["open"] else "+"


def main() -> None:
    b = load()
    rec = RunRecorder("ch35", "handover")
    ids = list(b["checks"])
    head = " ".join(f"{i[3:]:>2}" for i in ids)
    for date in b["reviews"]:
        rows = grid(b, date)
        rec.print(f"== Hand-Over Board {date}"
                  f"  (+ closed, X open, . n/a)")
        rec.print(f"   {'HO':<8}{head}")
        for r in rows:
            cells = " ".join(f"{cell(c, r):>2}" for c in ids)
            rec.print(f"{r['id']} {r['model']:<8}{cells}")
        n_app = sum(len(r["applies"]) for r in rows)
        n_open = sum(len(r["open"]) for r in rows)
        done = [r["id"] for r in rows if not r["open"]]
        rec.print(f"checks applying {n_app}, open {n_open};"
                  f" handed over {len(done)} of {len(rows)}"
                  f" ({', '.join(done) or 'none'})")
        for r in rows:
            for c, why in r["open"].items():
                rec.print(f"  {r['id']} {c}: {why}")
        rec.note(date=date, applying=n_app, open=n_open,
                 handed=done)
    f = b["fieldnote"]
    rec.print(f"== Fieldnote ({len(f['checks'])} checks)")
    rec.print(f"open {len(f['open'])} of {len(f['checks'])}:"
              f" {', '.join(f['open'])}")
    for c, why in f["open"].items():
        rec.print(f"  {c}: {why}")
    print(rec.save())


if __name__ == "__main__":
    main()
