"""Chapter 9: ask a model to do the quota count.

Gives the model the same rules (quota_rules.yaml) and the
same cohorts (data/hartwell_me.yaml) that quota.py uses, and
asks for the count as JSON. Then compares with quota.py.
This is the test that decides whether a model may do the
count. The model's answer is never used as the count.

Run: python -m chapters.ch09_gulf_asia.model_count
(writes runs/ch09/model_count/...; HRAI_MODEL picks model)
"""
from __future__ import annotations

import json
import re

import yaml

from chapters.ch09_gulf_asia import quota

SYSTEM = (
    "You support an HR operations team in the Gulf. Apply the "
    "rules exactly as written to the headcount data. Show no "
    "working outside the JSON. Reply with one JSON object.")

ASK = {
    "AE": ('Return {"base": int, "counted": int, "required": '
           'int, "shortfall": int} for the 2026-12-31 '
           "checkpoint."),
    "SA": ('Return {"weighted": number, "ratio": number, '
           '"band": string} with ratio as a fraction.'),
}
RULE = {"AE": "AE-EMIRATISATION", "SA": "SA-NITAQAT"}


def rule_text(key: str) -> str:
    """The rule's block from quota_rules.yaml, comments kept."""
    text = (quota.HERE / "quota_rules.yaml").read_text()
    block = text.split(f"{key}:", 1)[1].split("\n\n", 1)[0]
    return f"{key}:{block}"


def prompt(ent: dict, rules: dict) -> str:
    data = {k: v for k, v in ent.items() if k != "hris_view"}
    return ("RULES\n" + rule_text(RULE[ent["country"]])
            + "\n\nDATA\n"
            + yaml.safe_dump(data, sort_keys=False)
            + "\n" + ASK[ent["country"]])


def parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def truth(ent: dict, rules: dict, as_of: str) -> dict:
    if ent["country"] == "AE":
        r = quota.emiratisation(ent, rules[RULE["AE"]], as_of)
        keys = ("base", "counted", "required", "shortfall")
        return {k: r[k] for k in keys}
    r = quota.nitaqat(ent, rules[RULE["SA"]])
    return {"weighted": r["weighted"],
            "ratio": round(r["ratio"], 4), "band": r["band"]}


def same(a, b) -> bool:
    if isinstance(b, float) and isinstance(a, (int, float)):
        tol = 0.0005 if b < 1 else 0.01
        return abs(a - b) < tol
    return a == b


def main() -> None:
    from hrai.llm import RunRecorder
    rules = quota.load_rules()
    hme = quota.load("hartwell_me.yaml")
    as_of = str(hme["as_of"])
    rec = RunRecorder("ch09", "model_count")
    for ent in hme["entities"]:
        resp = rec.create(
            max_tokens=4000, system=SYSTEM,
            messages=[{"role": "user",
                       "content": prompt(ent, rules)}])
        text = "".join(b.text for b in resp.content
                       if b.type == "text")
        got, want = parse(text), truth(ent, rules, as_of)
        rec.print(f"{ent['id']}")
        for k, v in want.items():
            g = got.get(k)
            mark = "same" if same(g, v) else "DIFFERENT"
            rec.print(f"  {k:<10} model {g!s:<14} "
                      f"calculator {v!s:<12} {mark}")
        rec.note(entity=ent["id"], model=got, calculator=want)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
