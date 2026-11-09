"""Knowledge-assistant test set, run through Hartwell Gate in one
design (book section "Proving it: the test set and the restart").

For each question: the documents the context held that the user
may not read (exposure), whether any reached what the person saw
(leak), whether the outcome matched the expected answer or route,
and whether the checks held the draft. Tokens and cost come from
the gateway log.

Run: python -m chapters.ch17_surface_brain.evalsuite \
       hartwell entitled [claude-haiku-5-5]
(needs ANTHROPIC_API_KEY; writes runs/ch17/eval_<org>_<design>/)
"""
from __future__ import annotations

import sys

import yaml

from hrai.llm import RunRecorder

from . import assistant, entitled
from .entitled import DATA
from .gateway import Gateway


def outcome(q: dict, res: dict) -> str:
    if res.get("refused"):
        return "refused " + res["refused"]
    if res["routed"] or (res["draft"] or {}).get("route"):
        return "route"
    return "answer"


def main(org: str, design: str, model: str) -> None:
    docs, users = entitled.load(org)
    qs = yaml.safe_load((DATA / org / "questions.yaml")
                        .read_text())["questions"]
    rec = RunRecorder("ch17", f"eval_{org}_{design}")
    gw = Gateway.load(rec)
    rec.print(f"Test set {org}, design {design}, model {model}")
    rec.print("id   user      expect  got      exposed leaked check")
    n_exp = n_leak = n_right = n_held = 0
    rows = []
    for q in qs:
        res = assistant.ask(gw, q["q"], users[q["user"]], docs,
                            design, "ka.eval", model)
        got = outcome(q, res)
        right = (got == "answer") == (q["expect"] == "answer")
        if right and got == "answer":
            right = set(q.get("need", [])) <= set(
                res["draft"]["sources"])
        exp = res.get("exposed", [])
        n_exp += bool(exp)
        n_leak += bool(res["leaks"])
        n_right += right
        n_held += bool(res.get("held"))
        chk = ("held" if res.get("held") else
               "fail" if res["fails"] else "pass")
        rec.print(f"{q['id']}  {q['user']:<8}  {q['expect']:<6}  "
                  f"{got[:7]:<7}  {len(exp):>7} "
                  f"{','.join(res['leaks']) or '-':<6} {chk}"
                  f"{'' if right else '  WRONG'}")
        for f in res["fails"]:
            rec.print(f"       {f}")
        rows.append({k: res.get(k) for k in
                     ("user", "shown", "exposed", "leaks", "fails",
                      "held", "routed", "final", "draft",
                      "refused", "tokens", "cost")} | {"id": q["id"]})
    n = len(qs)
    calls = [e for e in gw.log if e.get("status") == "ok"]
    tin = sum(e["tokens_in"] for e in calls)
    tout = sum(e["tokens_out"] for e in calls)
    cost = sum(e["cost_usd"] for e in calls)
    rec.print(f"Questions {n}: context held an unreadable document "
              f"{n_exp}; leaked to the person {n_leak}; right "
              f"outcome {n_right}; held by the checks {n_held}")
    rec.print(f"Gateway: {len(calls)} calls, {tin} input and {tout} "
              f"output tokens, ${cost:.4f}, "
              f"${cost / max(len(calls), 1):.5f} a call")
    rec.note(rows=rows, gateway_log=gw.log)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], a[2] if len(a) > 2 else "claude-haiku-5-5")
