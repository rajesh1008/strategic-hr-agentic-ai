"""Chapter 12: a model proposes Hartwell Grades for local job codes.

The agent reads code, title and description through the access
manifest for use U5, and nothing else: not the 2016 mapping, not pay,
not who holds the job. It proposes a grade with a confidence and a
reason. Every proposal is staged for the Head of Reward; none is
applied. The run compares the proposals with the reward team's
reviewed answers for the forty codes it checked by hand.

Run: python -m chapters.ch12_data_readiness.job_map
     python -m chapters.ch12_data_readiness.job_map --title-only
(needs ANTHROPIC_API_KEY; writes runs/ch12/job_map/... or
runs/ch12/job_map_title/...; --title-only withholds descriptions,
as a quarter of the UK catalog has none)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

from . import access, quality, readiness

HERE = Path(__file__).resolve().parent
SYSTEM = """You help an employer's reward team map local job codes
to its global grade structure. Grade definitions:
{grades}
For each job profile, propose the one grade whose definition fits
the work described. Judge from the description where there is
one; otherwise judge from the title.
Reply with a JSON array only:
[{{"code": "...", "grade": "F2", "confidence": 0.0 to 1.0,
  "basis": "one sentence"}}]"""


def grade_text() -> str:
    g = yaml.safe_load((HERE / "grades.yaml").read_text())
    return "\n".join(f"{k}: {' '.join(v.split())}"
                     for part in ("field", "salaried")
                     for k, v in g[part].items())


def main() -> None:
    reg = readiness.load()
    use = next(u for u in reg["uses"] if u["id"] == "U5")
    title_only = "--title-only" in sys.argv
    rec = RunRecorder("ch12", "job_map_title" if title_only
                      else "job_map")
    m = access.manifest("U5", reg)
    reader = access.Reader(m)
    key = {p["code"]: p for p in yaml.safe_load(
        (HERE / "profiles.yaml").read_text())["profiles"]}
    cat = [r for r in quality.rows("job_catalog.csv")
           if r["code"] in key]
    fields = ["code", "title"] if title_only else \
        ["code", "title", "desc"]
    shown = reader.read("S02", fields, cat)
    resp = rec.create(max_tokens=6000,
                      system=SYSTEM.format(grades=grade_text()),
                      messages=[{"role": "user",
                                 "content": json.dumps(shown, indent=1,
                                                       ensure_ascii=False)}])
    text = "".join(b.text for b in resp.content if b.type == "text")
    mt = re.search(r"\[.*\]", text, re.S)
    props = json.loads(mt.group(0)) if mt else []
    for p in props:
        if p.get("code") in key:
            reader.propose("S02", p["code"],
                           {"proposed_grade": p.get("grade")},
                           p.get("basis", ""))
    got = {p["key"]: p for p in reader.staged}
    verdict = readiness.verdict(readiness.check_use(use, reg))
    rec.print(f"U5 register verdict: {verdict} (test on 40 reviewed "
              "codes only)")
    rec.print(f"Agent read: {', '.join(fields)}")
    rec.print(f"Model {resp.model}: {len(got)} proposals staged, "
              f"{sum(p['status'] == 'applied' for p in reader.staged)}"
              " applied")
    conf = {p["code"]: float(p.get("confidence", 0)) for p in props
            if p.get("code") in key}
    right = [c for c in key if c in got and
             got[c]["change"]["proposed_grade"] == key[c]["reviewed"]]
    bad16 = [c for c in key if key[c]["mapped"] != key[c]["reviewed"]]
    rec.print(f"Agrees with the reward team: {len(right)} of "
              f"{len(key)}")
    rec.print(f"  where the 2016 grade was wrong: "
              f"{sum(c in right for c in bad16)} of {len(bad16)}")
    rec.print(f"  where the 2016 grade was right: "
              f"{sum(c in right for c in key if c not in bad16)} of "
              f"{len(key) - len(bad16)}")
    wrong = [c for c in key if c in got and c not in right]
    cross = [c for c in wrong if got[c]["change"]["proposed_grade"]
             and got[c]["change"]["proposed_grade"][0]
             != key[c]["reviewed"][0]]
    sure = [c for c in wrong if conf.get(c, 0) >= 0.8]
    rec.print(f"Wrong: {len(wrong)}; across field/salaried: "
              f"{len(cross)}; at confidence 0.8 or more: {len(sure)}")
    for c in wrong:
        g = got[c]["change"]["proposed_grade"]
        rec.print(f"  {c} {key[c]['title'][:26]:<26} model {g} "
                  f"reward {key[c]['reviewed']} ({conf.get(c, 0):.2f})")
    missing = [c for c in key if c not in got]
    if missing:
        rec.print(f"No proposal: {', '.join(missing)}")
    rec.note(staged=reader.staged, read_log=reader.log,
             confidence=conf)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
