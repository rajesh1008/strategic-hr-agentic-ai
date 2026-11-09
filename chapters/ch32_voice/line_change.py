"""Chapter 32: Line v1.1 to v1.2, the register, the signatures.

Book sections "What Ray asked for" and "Four signatures, four
forms". Loads both Line versions with Chapter 11's place(),
lists every row whose answers or placement changed and who
asked, checks the v1.2 register with Chapter 11's six rules
and this chapter's four (represent.py), and reports who has
signed which version. No model.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch32_voice.line_change
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from chapters.ch11_automate_keep import line, register
from hrai.llm import RunRecorder

from . import represent

HERE = Path(__file__).resolve().parent / "data"
V11 = line.HERE / "line_v1_1.yaml"
V12 = HERE / "line_v1_2.yaml"


def counts(d: dict) -> str:
    c = Counter(s["placement"].side for s in d["steps"])
    return f"automate {c['automate']}, keep {c['keep']}"


def main() -> None:
    old, new = line.load(V11), line.load(V12)
    rec = RunRecorder("ch32", "line_change")
    rec.print(f"Line v{old['version']}: {counts(old)}")
    rec.print(f"Line v{new['version']}: {counts(new)}")
    by = {}
    for c in new["changes"]:
        by.setdefault(c["id"], c["by"])
    was = {s["id"]: s for s in old["steps"]}
    for s in new["steps"]:
        o = was[s["id"]]
        if s["answers"] != o["answers"]:
            rec.print(f"{s['id']} {o['answers']} -> "
                      f"{s['answers']}  {o['placement']} -> "
                      f"{s['placement']}  ({by[s['id']]})")
    rec.print("Facts rewritten: " + ", ".join(
        new["facts_rewritten"]))
    for path in (register.HERE / "register_v1_1.yaml",
                 HERE / "register_v1_2.yaml"):
        reg = yaml.safe_load(path.read_text())
        ld = old if reg["line_version"] == "1.1" else new
        six = register.check(ld, reg)
        four = represent.check(ld, reg)
        hit = Counter(cid for _, cid in four)
        each = ", ".join(f"{k} {hit[k]}"
                         for k in represent.U_TEXT)
        rec.print(f"Register v{reg['version']}: Chapter 11 "
                  f"checks {len(six)} problems; union checks "
                  f"{len(four)} problems ({each})")
        rec.note(register=reg["version"], six=len(six),
                 four=len(four))
    sigs = yaml.safe_load(
        (HERE / "signatures.yaml").read_text())
    rows = Counter(s["id"][0] for s in new["steps"])
    done = [s for s in sigs
            if s["line_version"] == new["version"]]
    rec.print("Representative signatures on "
              f"v{new['version']}: {len(done)} of {len(sigs)}")
    for s in sorted(done, key=lambda s: s["date"]):
        n = sum(rows[a] for a in s["areas"])
        rec.print(f"  {s['date']}  {s['signer']:16s} "
                  f"{n:2d} rows  {s['form']}")
    rec.save()


if __name__ == "__main__":
    main()
