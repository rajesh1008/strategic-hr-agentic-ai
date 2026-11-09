"""Chapter 34: ask the operating model "who decides?".

Book section "Test the charter, not the forum". Twelve
questions go to the forum's assistant in three designs:

  slide  the operating-model slide (prose), the way most
         operating models are written down; NOT_SET allowed
  pick   the same slide, told to pick the most likely role,
         the way a busy manager asks a colleague
  table  charter v1 as rows (decides, does, prepares,
         checks, told, record); NOT_SET allowed

Each answer must be one role code or NOT_SET. Grading is a
lookup in charter v1 (charter.lookup), not a model.

Run:  HRAI_MODEL=claude-haiku-5-5 \\
        python -m chapters.ch34_operating_model.ask
"""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from chapters.ch34_operating_model import charter as C
from hrai.llm import RunRecorder, model

HERE = Path(__file__).resolve().parent
THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
RUNS = int(os.environ.get("HRAI_RUNS", "3"))
SYSTEM = """You answer questions about who decides what in
Hartwell's HR operating model, using only the document
given. For each question reply with exactly one role code
from this list: {codes}.
{rule}
Reply with JSON only: {{"Q01": "CODE", ...}}"""
RULE = {"abstain": "If the document does not say, reply "
        "NOT_SET. Do not guess from what is usual "
        "elsewhere.",
        "pick": "Where the document is not explicit, pick "
        "the most likely role."}


def questions() -> list[dict]:
    return yaml.safe_load(
        (HERE / "data" / "questions.yaml").read_text())


def table_text(rows: list[dict]) -> str:
    cols = ("decides", "does", "prepares", "checks")
    out = []
    for r in rows:
        bits = [f"{k}={r[k] or '-'}" for k in cols]
        bits.append("told=" + ",".join(r["told"]))
        out.append(f"{r['id']} {r['decision']}: "
                   + "; ".join(bits))
    return "\n".join(out)


def expected(q: dict, rows: list[dict]) -> str:
    if not q["row"]:
        return "NOT_SET"
    return C.lookup(rows, q["row"], q["column"])


def ask(rec, doc: str, qs: list[dict], codes,
        rule: str) -> dict:
    text = (f"Document:\n{doc}\n\nQuestions:\n" + "\n".join(
        f"{q['id']} {q['text']}" for q in qs))
    resp = rec.create(
        max_tokens=3000,
        system=SYSTEM.format(codes=", ".join(codes),
                             rule=RULE[rule]),
        messages=[{"role": "user", "content": text}],
        thinking=THINK.get(model(), {"type": "disabled"}))
    raw = "".join(b.text for b in resp.content
                  if b.type == "text")
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def grade(got: dict, qs, rows) -> dict:
    out = {"right": 0, "not_set": 0, "wrong": 0, "miss": []}
    for q in qs:
        a, e = got.get(q["id"], "NOT_SET"), expected(q, rows)
        if a == e:
            out["right"] += 1
        elif a == "NOT_SET":
            out["not_set"] += 1
            out["miss"].append(f"{q['id']} {a}")
        else:
            out["wrong"] += 1
            out["miss"].append(f"{q['id']} {a}")
    return out


def main() -> None:
    rec = RunRecorder("ch34", "ask")
    c = C.load()
    rows, qs = c["versions"]["v1"], questions()
    codes = c["roles"] + ["NOT_SET"]
    docs = {"slide": (c["slide"], "abstain"),
            "pick": (c["slide"], "pick"),
            "table": (table_text(rows), "abstain")}
    jobs = [(d, i) for d in docs for i in range(1, RUNS + 1)]
    with ThreadPoolExecutor(6) as ex:
        got = list(ex.map(
            lambda j: ask(rec, *docs[j[0]][:1], qs, codes,
                          docs[j[0]][1]), jobs))
    rec.print(f"== {model()}: 12 questions, {RUNS} runs "
              f"per design")
    rec.print("design run right not_set wrong")
    for (d, i), g in zip(jobs, got):
        s = grade(g, qs, rows)
        rec.print(f"{d:<6} {i:>3} {s['right']:>5} "
                  f"{s['not_set']:>7} {s['wrong']:>5}")
        bad = [m for m in s["miss"]
               if not m.endswith("NOT_SET")]
        for k in range(0, len(bad), 3):
            rec.print("   wrong: " + ", ".join(bad[k:k + 3]))
        rec.note(design=d, run=i, answers=g, grade=s)
    rec.save()


if __name__ == "__main__":
    main()
