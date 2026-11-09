"""Chapter 5: a model drafts rule records; counsel decides.

A horizon scan finds new items. The model reads each item and
drafts a proposed rule record in the schema of hrai/law/rules.
The code validates the draft, compares it field by field with
what the register already holds for the same source, and puts
every draft in counsel's queue. Nothing is written to rules/.

Run: python -m chapters.ch05_jurisdiction_map.horizon_drafter
(needs ANTHROPIC_API_KEY; writes runs/ch05/horizon_drafter/...)
"""
from __future__ import annotations

import json
import re
import textwrap
from datetime import date
from pathlib import Path

import yaml

from hrai import law
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
DECISIONS = ["advertise", "hire", "book", "terms", "discipline",
             "allocate", "schedule", "monitor", "layoff"]
TRIGGERS = ["any", "ai", "substantial", "solely"]
STATUS = ["in_force", "enacted", "paused", "pending",
          "proposed", "guidance"]
FIELDS = ["lane", "status", "in_force", "trigger", "decisions",
          "duties"]

AS_OF = "2026-11-09"
SYSTEM = f"""You draft proposed rule records for an employer's
register of AI-in-employment law. You do not decide whether a rule
applies to anyone; a lawyer reviews every draft. Today is {AS_OF}.
For each source item, write one record per distinct obligation
with a distinct start date. Use only what the item says.
Fields:
 source: the item id
 lane: place code (US-CA, US-CT, CA, CA-ON, UK, EU, AU, ...)
 name: short name of the instrument and provision
 status: in_force (duties apply today), enacted (law made,
  duties start later), paused (enforcement on hold), pending,
  proposed (a bill), or guidance
 in_force: YYYY-MM-DD when duties start, or null if not stated
 trigger: any (applies with or without AI), ai (any AI use),
  substantial (AI output is a substantial factor) or solely
 decisions: subset of {DECISIONS}
 duties: subset of these codes:
""" + "\n".join(f"  {k}: {v}" for k, v in law.DUTIES.items()) + """
 check: one sentence on what a lawyer must confirm in the
  primary text before this record is used
Reply with a JSON array only."""


# the box's Brotli is too old for the SDK's decoder
GZIP = {"Accept-Encoding": "gzip, deflate"}


def draft(rec: RunRecorder, items: list[dict]) -> list[dict]:
    resp = rec.create(
        max_tokens=6000, system=SYSTEM, extra_headers=GZIP,
        messages=[{"role": "user",
                   "content": json.dumps(items, indent=1)}])
    text = "".join(b.text for b in resp.content if b.type == "text")
    m = re.search(r"\[.*\]", text, re.S)
    try:
        rows = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        rows = []
    return [r for r in rows if isinstance(r, dict)]


def problems(p: dict) -> list[str]:
    """Schema check: a draft that fails is still queued, flagged."""
    out = []
    if p.get("status") not in STATUS:
        out.append("status")
    if p.get("trigger") not in TRIGGERS:
        out.append("trigger")
    if not set(p.get("decisions") or []) <= set(DECISIONS):
        out.append("decisions")
    if not set(p.get("duties") or []) <= set(law.DUTIES):
        out.append("duties")
    d = p.get("in_force")
    if d is not None:
        try:
            date.fromisoformat(str(d))
        except ValueError:
            out.append("in_force")
    return out


def norm(v):
    if isinstance(v, list):
        return sorted(v)
    return None if v in (None, "", "null") else str(v)


def closest(p: dict, held: list[dict]) -> dict | None:
    def score(r):
        return (r["lane"] == p.get("lane"),
                str(r.get("in_force")) == str(p.get("in_force")),
                len(set(r.get("duties", []))
                    & set(p.get("duties") or [])))
    return max(held, key=score) if held else None


def main() -> None:
    items = yaml.safe_load(
        (HERE / "horizon_sources.yaml").read_text())
    rules = law.load_rules()
    rec = RunRecorder("ch05", "horizon_drafter")
    drafts = draft(rec, items)
    model = rec.calls[-1]["response"]["model"]
    rec.print(f"Sources: {len(items)}; drafts from {model}: "
              f"{len(drafts)}")
    agree = total = 0
    for p in drafts:
        src = str(p.get("source", "?"))
        held = [r for r in rules if src in r.get("evidence", [])]
        r = closest(p, held)
        bad = problems(p)
        rec.print("")
        rec.print(f"{src} draft: {p.get('lane')} "
                  f"{str(p.get('name', ''))[:40]}")
        if bad:
            rec.print(f"  schema problems: {', '.join(bad)}")
        if r is None:
            rec.print("  register holds nothing from this source")
        else:
            rec.print(f"  register: {r['id']}")
            for k in FIELDS:
                total += 1
                a, b = norm(p.get(k)), norm(r.get(k))
                if a == b:
                    agree += 1
                    continue
                show = (lambda v: ",".join(v) if isinstance(v, list)
                        else str(v))
                rec.print(f"  {k:<9} draft {show(a)[:22]:<22} "
                          f"held {show(b)[:22]}")
        for w in textwrap.wrap("check: " + str(p.get("check", "")),
                               60):
            rec.print("  " + w)
        rec.note(draft=p, compared_with=r["id"] if r else None,
                 schema_problems=bad, to="employment counsel")
    rec.print("")
    rec.print(f"Fields matching the register: {agree} of {total}")
    rec.print(f"Queued for counsel: {len(drafts)}; "
              "written to rules/: 0")
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
