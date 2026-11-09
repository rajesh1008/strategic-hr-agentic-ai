"""Rule lookup: facts of one step at one place and date -> findings.

Four outcomes, and only four:
  APPLIES  a recorded rule reaches the step (or will, from a date)
  PAUSED   it reaches the step but enforcement is on hold
  UNCLEAR  the record does not settle whether it reaches the step
  GAP      the register holds no record for this place or topic
UNCLEAR and GAP are calls to counsel, not answers. The absence of
a record is never read as the absence of a law.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RULES = HERE / "rules"

DUTIES = {
    "NOTICE": "tell the person that AI is used in the decision",
    "POSTING": "state AI use in the public job posting",
    "POLICY": "describe automated decisions in the privacy policy",
    "EXPLAIN": "explain the decision and its main factors",
    "CORRECT": "let the person see and correct the data used",
    "REVIEW": "a person reconsiders the decision on request",
    "OVERSIGHT": "a person oversees and verifies the decision",
    "AUDIT": "independent bias audit before use",
    "PUBLISH": "publish the audit results",
    "ASSESS": "risk or impact assessment",
    "REPS": "inform or consult worker representatives",
    "CONSENT": "written consent before collecting biometrics",
    "NO_EFFECT": "no discriminatory effect",
    "NO_INTENT": "no intent to discriminate",
    "NO_PROXY": "no ZIP code as a proxy for a protected class",
    "BANNED": "the practice is prohibited",
    "LITERACY": "support AI literacy of the staff who use it",
    "CONSULT": "consult on significant workplace change",
    "SAFETY": "manage health and safety risk of the system",
    "COUNSEL": "duties not itemized in the record",
}
AI_LEVELS = ["none", "assist", "substantial", "solely"]
TRIGGERS = {"any": 0, "ai": 1, "substantial": 2, "solely": 3}
LIVE = {"in_force", "enacted", "paused"}


@dataclass(frozen=True)
class Facts:
    """One step of a workflow, at one place."""
    place: str              # e.g. US-IL, CA-ON, UK, NL, AU-QLD
    decision: str           # advertise, hire, book, terms,
                            # discipline, allocate, schedule,
                            # monitor, layoff
    ai: str = "none"        # none, assist, substantial, solely
    subject: str = "applicant"   # applicant, employee, worker
    employees: int = 1000
    employer_type: str = "employer"   # or platform
    features: frozenset = frozenset()  # emotion, biometric
    via_eor: bool = False   # employed through an employer of record


@dataclass
class Finding:
    outcome: str            # APPLIES, PAUSED, UNCLEAR, GAP
    lane: str
    rule_id: str = ""
    name: str = ""
    duties: list = field(default_factory=list)
    when: str = ""          # "in force", "from 2027-12-02", ...
    evidence: list = field(default_factory=list)
    note: str = ""
    verify: bool = True

    def tag(self) -> str:
        return "[VERIFY]" if self.verify else ""


def load_rules(path: Path = RULES) -> list[dict]:
    rules = []
    for f in sorted(path.glob("*.yaml")):
        if f.name == "coverage.yaml":
            continue
        for r in yaml.safe_load(f.read_text()) or []:
            r["file"] = f.name
            for d in r.get("duties", []):
                if d not in DUTIES:
                    raise ValueError(f"{r['id']}: unknown duty {d}")
            rules.append(r)
    ids = [r["id"] for r in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate rule id")
    return rules


def coverage(path: Path = RULES) -> dict:
    return yaml.safe_load((path / "coverage.yaml").read_text())


def place_chain(place: str, cov: dict | None = None) -> list[str]:
    """US-NYC -> [US-NYC, US-NY, US]; NL -> [NL, EU]."""
    parents = (cov or coverage())["parents"]
    chain = [place]
    while True:
        p = chain[-1]
        nxt = parents.get(p) or (p.rsplit("-", 1)[0]
                                 if "-" in p else None)
        if not nxt:
            return chain
        chain.append(nxt)


def _date(v) -> date | None:
    if v is None or isinstance(v, date):
        return v
    return date.fromisoformat(str(v))


def _reaches(r: dict, f: Facts, chain: list[str]) -> str | None:
    """None if out of scope, else 'yes' or 'unclear: why'."""
    if r.get("kind", "rule") != "rule" or r["status"] not in LIVE:
        return None
    if not set(r["places"]) & set(chain):
        return None
    if f.employer_type not in r.get("employer_types", ["employer"]):
        return None
    if f.employees < r.get("min_employees", 0):
        return None
    if f.subject not in r.get("subjects",
                              ["applicant", "employee", "worker"]):
        return None
    need = r.get("features")
    if need and not set(need) & set(f.features):
        return None
    if not need and TRIGGERS[r["trigger"]] > AI_LEVELS.index(f.ai):
        return None
    if f.decision in r.get("unclear_decisions", []):
        return f"unclear: is '{f.decision}' a covered decision?"
    if f.decision not in r["decisions"]:
        return None
    if f.via_eor and r.get("eor_unclear"):
        return "unclear: who deploys the system under an EOR?"
    return "yes"


def obligations(f: Facts, as_of: date, rules: list[dict],
                cov: dict | None = None) -> list[Finding]:
    cov = cov or coverage()
    chain = place_chain(f.place, cov)
    out: list[Finding] = []
    for r in rules:
        hit = _reaches(r, f, chain)
        if hit is None:
            continue
        start = _date(r.get("in_force"))
        when = ("in force" if start is None or start <= as_of
                else f"from {start.isoformat()}")
        outcome = "APPLIES"
        if r["status"] == "paused":
            outcome = "PAUSED"
        if hit != "yes":
            outcome = "UNCLEAR"
        note = hit if hit != "yes" else r.get("note", "")
        if r.get("trigger_basis") == "conservative":
            note = (note + "; " if note else "") + \
                "trigger not in record, assumed"
        out.append(Finding(outcome, r["lane"], r["id"], r["name"],
                           list(r.get("duties", [])), when,
                           list(r.get("evidence", [])), note,
                           not r.get("checked")))
    out += gaps(f, chain, cov)
    return out


def gaps(f: Facts, chain: list[str], cov: dict) -> list[Finding]:
    found = [Finding("GAP", g["place"], note=g["note"])
             for g in cov.get("gaps", [])
             if g["place"] in chain and f.decision in g["decisions"]]
    named = {g.lane for g in found}
    checked = set(cov["checked"])
    for p in chain:
        if p not in checked and p not in named:
            found.append(Finding(
                "GAP", p, note=f"no rules recorded for {p}"))
    return found


def horizon(rules: list[dict], start: date, end: date) -> list[dict]:
    """Rules whose date falls after start and on or before end."""
    rows = []
    for r in rules:
        for key in ("in_force", "expected"):
            d = _date(r.get(key))
            if d and start < d <= end:
                rows.append({"date": d, "lane": r["lane"],
                             "id": r["id"], "name": r["name"],
                             "status": r["status"],
                             "evidence": r.get("evidence", []),
                             "basis": key,
                             "date_basis": r.get("date_basis", "")})
    return sorted(rows, key=lambda x: (x["date"], x["lane"]))
