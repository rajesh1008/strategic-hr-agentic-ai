"""Chapter 5: the obligation register for one workflow.

For every step of a workflow at every site, ask hrai.law which
recorded rules reach it, then turn the findings into one row per
(lane, rule, duty): which steps trigger it, who owns it, and
which control shows it is done. UNCLEAR and GAP findings become
questions for counsel. Deterministic; no model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from hrai import law

HERE = Path(__file__).resolve().parent


@dataclass
class Row:
    lane: str
    rule: str
    duty: str
    when: str
    outcome: str
    evidence: list
    steps: list = field(default_factory=list)
    owner: str = ""
    control: str = ""


def load(name: str = "hartwell_hiring.yaml") -> dict:
    return yaml.safe_load((HERE / name).read_text())


def findings(wf: dict, design: str, rules, as_of: date):
    """Yield (lane code, step id, Finding) for one design."""
    over = wf.get(design) or {}
    for lane in wf["lanes"]:
        for s in wf["steps"]:
            f = law.Facts(place=lane["code"],
                          decision=s["decision"],
                          ai=over.get(s["id"], s["ai"]),
                          employees=wf["employees"],
                          features=frozenset(s.get("features", [])),
                          subject=s.get("subject", "applicant"),
                          via_eor=lane.get("via_eor", False))
            for x in law.obligations(f, as_of, rules):
                yield lane["code"], s["id"], x


def register(wf: dict, rules, as_of: date, design: str = ""):
    rows: dict[tuple, Row] = {}
    questions: dict[tuple, set] = {}
    for site, step, x in findings(wf, design, rules, as_of):
        if x.outcome in ("UNCLEAR", "GAP"):
            key = (site, x.lane, x.rule_id, x.note)
            questions.setdefault(key, set()).add(step)
            continue
        for d in x.duties:
            k = (x.lane, x.rule_id, d)
            if k not in rows:
                rows[k] = Row(x.lane, x.rule_id, d, x.when,
                              x.outcome, x.evidence,
                              owner=wf["owners"].get(d, ""),
                              control=wf["controls"].get(
                                  f"{x.lane}/{d}", ""))
            if step not in rows[k].steps:
                rows[k].steps.append(step)
    return list(rows.values()), questions


def by_lane(wf, rules, as_of, design=""):
    """Site -> (set of rule ids, set of duties) for one design."""
    out = {ln["code"]: (set(), set()) for ln in wf["lanes"]}
    for site, _, x in findings(wf, design, rules, as_of):
        if x.outcome in ("APPLIES", "PAUSED"):
            out[site][0].add(x.rule_id)
            out[site][1].update(x.duties)
    return out
