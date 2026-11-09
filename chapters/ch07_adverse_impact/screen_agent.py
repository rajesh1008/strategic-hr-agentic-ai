"""Chapter 7: one screening agent, one table per version.

Book section "An agent's step is a selection procedure". The
agent reads job-related fields only (never self-ID), and
recommends who a recruiter should phone first. It holds no
write tool: Line row A04 is Keep at recommend (Chapter 11).
After the run, the code joins self-ID by candidate ID and
builds the adverse-impact table for this version: criteria
version plus model. A new version gets a new table.

Run:  HRAI_MODEL=claude-haiku-5-5 \\
      python -m chapters.ch07_adverse_impact.screen_agent S2
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder, model

from . import impact as ai
from .audit import AXES, joined
from .make_data import load

HERE = Path(__file__).resolve().parent
BATCH = 40
# the box's brotli is too old for the SDK's HTTP client
GZIP = {"Accept-Encoding": "gzip, deflate"}
SHOWN = ("candidate_id", "years_field_service",
         "longest_gap_months", "certifications")
SYSTEM = """You help a recruiter at a facilities company.
Role: {role}
Screening criteria (version {version}):
{criteria}
For each applicant, answer "Y" (phone first) or "N" (not
now), and one reason code: CERT, YEARS, GAP or OTHER.
You recommend only; a recruiter decides.
Reply with a JSON array only:
[{{"id": "...", "rec": "Y", "reason": "CERT"}}]"""


def ask(rec, system: str, batch: list[dict]) -> dict:
    shown = [{k: a[k] for k in SHOWN} for a in batch]
    resp = rec.create(max_tokens=6000, system=system,
                      extra_headers=GZIP,
                      messages=[{"role": "user", "content":
                                 json.dumps(shown)}])
    text = "".join(b.text for b in resp.content
                   if b.type == "text")
    m = re.search(r"\[.*\]", text, re.S)
    try:
        rows = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        rows = []
    return {r.get("id"): r for r in rows
            if isinstance(r, dict) and r.get("rec") in "YN"}


def main(version: str) -> None:
    cfg = yaml.safe_load((HERE / "screen_versions.yaml")
                         .read_text())
    v = cfg["versions"][version]
    system = SYSTEM.format(role=cfg["role"], version=version,
                           criteria=v["criteria"].strip())
    apps = [a for a in load("hartwell-q4-2026.csv")
            if a["agent_sample"] == "Y"]
    rec = RunRecorder("ch07", f"screen_{version}")
    said: dict = {}
    for i in range(0, len(apps), BATCH):
        said.update(ask(rec, system, apps[i:i + BATCH]))
    rec.print(f"version {version} on {model()}: "
              f"{len(apps)} applicants")
    blank = [a for a in apps if a["candidate_id"] not in said]
    reasons: dict = {}
    for r in said.values():
        k = (r["rec"], r.get("reason", "OTHER"))
        reasons[k] = reasons.get(k, 0) + 1
    yes = sum(r["rec"] == "Y" for r in said.values())
    rec.print(f"recommended {yes}; not now {len(said) - yes}"
              f"; no answer {len(blank)}")
    rec.print("reasons: " + ", ".join(
        f"{y}/{c} {n}" for (y, c), n in sorted(reasons.items())))
    recs = joined(apps, load("hartwell-q4-2026-self-id.csv"))
    for r in recs:
        s = said.get(r["candidate_id"])
        r["rec"] = "none" if s is None else s["rec"]
    sel = lambda r: r["rec"] == "Y"  # noqa: E731
    out = {}
    for name, key in AXES + [("sex & age", None)]:
        g = ai.intersect("sex_", "age") if key is None \
            else (lambda r, k=key: r[k])
        t, miss = ai.table(recs, g, sel)
        for line in ai.render(t, f"-- {name}", miss):
            rec.print(line)
        out[name] = [ai.as_dict(x) for x in t]
    rec.note(version=version, criteria=v["criteria"],
             recommendations={k: v["rec"] for k, v in
                              said.items()})
    path = Path(rec.save())
    side = path.with_name(path.name.split("-")[0]
                          + ".tables.json")
    side.write_text(json.dumps(out, indent=1) + "\n")
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "S2")
