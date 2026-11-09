"""Chapter 5 / Appendix C: print the full jurisdiction matrix.

Writes Markdown tables, one per lane group, three columns each so
they fit a six-inch screen: the rule (with evidence IDs), what it
asks, and its status and date. Generated from hrai/law/rules, so
the appendix and the lookup can never disagree.

Run: python -m chapters.ch05_jurisdiction_map.matrix > app-C.md
"""
from __future__ import annotations

from hrai import law

GROUPS = [
    ("United States", "us.yaml"), ("Canada", "canada.yaml"),
    ("United Kingdom", "uk.yaml"),
    ("European Union and member states", "eu.yaml"),
    ("Australia", "australia.yaml"),
    ("Comparison lanes (Chapter 9)", "comparison.yaml")]
STATUS = {"in_force": "In force", "enacted": "Enacted",
          "paused": "Enforcement paused", "pending": "Pending",
          "proposed": "Proposed", "guidance": "Guidance"}
KIND = {"posture": "Posture, no duty", "context": "Context",
        "guidance": "Guidance"}
DECIDE = {"advertise": "job ads", "hire": "hiring",
          "book": "booking", "terms": "terms of work",
          "discipline": "discipline and dismissal",
          "allocate": "task allocation", "schedule": "scheduling",
          "monitor": "monitoring", "layoff": "layoffs"}
TRIG = {"any": "with or without AI", "ai": "any AI use",
        "substantial": "AI a substantial factor",
        "solely": "solely automated decisions"}


def when(r: dict) -> str:
    d = r.get("in_force") or r.get("expected")
    s = STATUS.get(r["status"], r["status"])
    if d:
        s += (", target " if r.get("expected") and not
              r.get("in_force") else ", from ") + \
            d.strftime("%B %-d, %Y")
    elif r.get("since"):
        s += f" ({r['since']})"
    if r.get("date_basis"):
        s += f"; date basis: {r['date_basis']}"
    return s


def asks(r: dict) -> str:
    kind = r.get("kind", "rule")
    if kind in ("posture", "context") or not r.get("duties"):
        return KIND.get(kind, "Context") + (
            f": {r['note']}" if r.get("note") else "")
    duties = "; ".join(law.DUTIES[d] for d in r["duties"])
    scope = ", ".join(DECIDE[d] for d in r["decisions"])
    text = f"{duties[0].upper()}{duties[1:]}. Reaches {scope}"
    text += f" ({TRIG[r['trigger']]})"
    if r.get("features"):
        text += f", where {' or '.join(r['features'])} data are used"
    if r.get("min_employees"):
        text += f", employers of {r['min_employees']} or more"
    if r.get("note"):
        text += f". Note: {r['note']}"
    return text + "."


def main() -> None:
    rules = law.load_rules()
    for title, fname in GROUPS:
        print(f"## {title}\n")
        print("::: jurisdiction-table")
        print("| Rule | What it asks | Status |")
        print("|---|---|---|")
        for r in rules:
            if r["file"] != fname:
                continue
            ev = " ".join(f"[{e}]" for e in r["evidence"])
            print(f"| {r['name']} ({r['lane']}) {ev} | {asks(r)} "
                  f"| {when(r)} [VERIFY] |")
        print(":::\n")


if __name__ == "__main__":
    main()
