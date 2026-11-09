"""Chapter 12: ask a model whether the thirteen sample texts may be
pasted, first with no rule and then with the four-class rule.

The point of the run is the comparison with the Group DPO office's
labels and with the deterministic checker in paste_rule.py. The
model is never the control: Hartwell Gate runs the checker, and
people apply the rule.

Run: python -m chapters.ch12_data_readiness.paste_model
(needs ANTHROPIC_API_KEY; writes runs/ch12/paste_model/...)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

from . import paste_rule

HERE = Path(__file__).resolve().parent
ASK_PLAIN = """An HR team member wants to paste each text below into a
general-purpose AI chatbot to get help. For each, answer whether it
is acceptable to paste. Reply with a JSON array only:
[{"id": "P01", "ok": true, "why": "one short sentence"}]"""
ASK_RULE = """Classify each text under this rule.
OPEN: no information about any identifiable person or the employer's
internal figures. Any approved tool.
INTERNAL: the employer's internal figures or documents, no person
identifiable. Only the employer's gateway tools.
PERSONAL: information about an identifiable person, including a
person identifiable from a small group or from context. Only the tool
registered for that data and purpose.
NEVER: health, religion or belief, ethnicity, disability, union
membership, immigration status, a conduct or grievance case, bank
details or a national ID number, about any person, stated or
implied. No model tool.
Reply with a JSON array only:
[{"id": "P01", "class": "OPEN", "why": "one short sentence"}]"""


def ask(rec: RunRecorder, system: str, cases: list[dict]) -> dict:
    shown = [{"id": c["id"], "text": c["text"]} for c in cases]
    resp = rec.create(max_tokens=4000, system=system, messages=[
        {"role": "user", "content": json.dumps(shown, indent=1)}])
    text = "".join(b.text for b in resp.content if b.type == "text")
    m = re.search(r"\[.*\]", text, re.S)
    return {r["id"]: r for r in json.loads(m.group(0))} if m else {}


def main() -> None:
    cases = yaml.safe_load(
        (HERE / "paste_cases.yaml").read_text())["cases"]
    rec = RunRecorder("ch12", "paste_model")
    plain = ask(rec, ASK_PLAIN, cases)
    ruled = ask(rec, ASK_RULE, cases)
    rec.print(f"Model {rec.calls[-1]['response']['model']}, "
              f"{len(cases)} texts")
    rec.print("id   label     no rule  with rule  checker   strictest")
    n_plain = n_rule = n_check = n_both = 0
    looser = {"no rule": 0, "rule": 0, "checker": 0, "strictest": 0}
    rank = paste_rule.CLASSES.index
    for c in cases:
        ok = plain.get(c["id"], {}).get("ok")
        cls = ruled.get(c["id"], {}).get("class", "-")
        chk, _ = paste_rule.classify(c["text"])
        both = max(chk, cls if cls in paste_rule.CLASSES else chk,
                   key=rank)
        for k, v in (("rule", cls), ("checker", chk),
                     ("strictest", both)):
            if v in paste_rule.CLASSES and rank(v) < rank(c["label"]):
                looser[k] += 1
        n_both += both == c["label"]
        want_ok = c["label"] == "OPEN"
        looser["no rule"] += bool(ok) and not want_ok
        n_plain += ok is want_ok
        n_rule += cls == c["label"]
        n_check += chk == c["label"]
        rec.print(f"{c['id']}  {c['label']:<8}  "
                  f"{'paste' if ok else 'no' if ok is False else '-':<7}"
                  f"  {cls:<9}  {chk:<8}  {both}")
    n = len(cases)
    rec.print(f"Right: no rule {n_plain} of {n} (paste only OPEN); "
              f"with rule {n_rule} of {n}; checker {n_check} of {n}; "
              f"strictest {n_both} of {n}")
    rec.print("Looser than the label: " + ", ".join(
        f"{k} {v}" for k, v in looser.items()))
    for c in cases:
        if c["label"] == "NEVER" and plain.get(c["id"], {}).get("ok"):
            rec.print(f"  no rule said paste {c['id']}: "
                      f"{plain[c['id']].get('why', '')[:60]}")
    rec.note(plain=plain, ruled=ruled)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
