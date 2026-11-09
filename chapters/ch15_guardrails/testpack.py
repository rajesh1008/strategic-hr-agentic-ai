"""Run the guardrail test pack against both builds.

Book section: "A prompt is not a guardrail" and "The
guardrail test pack". Twelve cases, three builds, one model.
Run: python -m chapters.ch15_guardrails.testpack
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from hrai.llm import RunRecorder, model
from . import entitle as E
from . import oracle as O
from .assistant import TOOLS, Tools, system

HERE = Path(__file__).parent
PACK = HERE / "data" / "testpack.yaml"
ROLES = {"HW-030114": ["line_manager"],
         "HW-031207": ["line_manager"]}


def converse(rec, build, case, m, db, ceiling) -> dict:
    user = dict(db[case["user"]], roles=ROLES[case["user"]])
    tools = Tools(build, user, m, db, ceiling)
    msgs = [{"role": "user", "content": case["ask"]}]
    calls, text, means = [], "", []
    for _ in range(6):                  # turn budget
        resp = rec.create(max_tokens=900, messages=msgs,
                          system=system(build, user),
                          tools=TOOLS)
        msgs.append({"role": "assistant", "content": [
            b.model_dump(exclude_none=True)
            for b in resp.content]})
        text = " ".join(b.text for b in resp.content
                        if b.type == "text").strip()
        uses = [b for b in resp.content if b.type == "tool_use"]
        if not uses:
            break
        res = []
        for u in uses:
            out = tools.call(u.name, u.input or {})
            calls.append(u.name)
            if u.name == "pay_summary" and '"mean"' in out:
                means.append((u.input.get("employee_ids", []),
                              json.loads(out)["mean"]))
            res.append({"type": "tool_result",
                        "tool_use_id": u.id, "content": out})
        msgs.append({"role": "user", "content": res})
    return {"calls": calls, "reply": text, "means": means,
            "exposed": O.exposed(case, tools.exposed, means),
            "disclosed": O.disclosed(case, text, db, means),
            "answered": O.answered(case, text),
            "decisions": tools.decisions}


def main(argv: list[str]) -> None:
    builds = argv or ["vague", "prompt", "engine"]
    m, db = E.load(), E.people()
    ceiling = yaml.safe_load(E.AGENTS.read_text())[
        "manager_assistant"]["ceiling"]
    cases = yaml.safe_load(PACK.read_text())["cases"]
    rec = RunRecorder("ch15", "testpack")
    rec.print(f"Guardrail test pack v1.0, grader v1.1,"
              f" model {model()} (synthetic)")
    for build in builds:
        tot = {"exp": 0, "dis": 0, "ctl": 0, "ok": 0}
        rec.print(f"Build: {build}")
        for c in cases:
            r = converse(rec, build, c, m, db, ceiling)
            ctl = c["kind"] == "control"
            if ctl:
                tot["ctl"] += 1
                tot["ok"] += r["answered"]
                verdict = ("answered" if r["answered"]
                           else "NOT ANSWERED")
            else:
                tot["exp"] += r["exposed"]
                tot["dis"] += r["disclosed"]
                verdict = ("DISCLOSED" if r["disclosed"]
                           else "held") + (
                    "; data reached model" if r["exposed"]
                    else "")
            rec.print(f"  {c['id']} {c['kind']:<17} {verdict}")
            rec.note(**{f"{build}:{c['id']}": r})
        n = len(cases) - tot["ctl"]
        rec.print(f"  attacks: disclosed {tot['dis']} of {n};"
                  f" data reached model {tot['exp']} of {n}")
        rec.print(f"  controls answered: {tot['ok']} of"
                  f" {tot['ctl']}")
    print(rec.save())


if __name__ == "__main__":
    main(sys.argv[1:])
