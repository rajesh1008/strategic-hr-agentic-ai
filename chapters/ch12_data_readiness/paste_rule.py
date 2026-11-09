"""Chapter 12: the what-you-may-paste rule, as a checker.

Four classes, most open first. The checker finds what it can see
(identifiers, keywords, small counts, likely names) and returns the
most restrictive class it finds, with the reason. It cannot see
context, so it never upgrades text a person has marked restricted.
No model is involved.

Run: HRAI_MODEL=no-model python -m chapters.ch12_data_readiness.paste_rule
(writes runs/ch12/paste_rule/...)
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CLASSES = ["OPEN", "INTERNAL", "PERSONAL", "NEVER"]
WHERE = {
    "OPEN": "any tool on the approved list",
    "INTERNAL": "Hartwell Gate tools only",
    "PERSONAL": "only the tool registered for that data",
    "NEVER": "no model tool; use the system built for it",
}
NEVER = {
    "health": r"\b(sick\w*|diagnos\w*|surgery|pregnan\w*|"
              r"medication|fit note|mental health|therapy)\b",
    "union": r"\b(union member\w*|union dues|shop steward)\b",
    "immigration": r"\b(visa|work permit|immigration)\b",
    "conduct case": r"\b(grievance|disciplinary|allegation\w*|"
                    r"investigation)\b",
    "bank details": r"\b\d{2}-\d{2}-\d{2}\b.*\b\d{8}\b",
    "national ID": r"\b([A-Z]{2}\d{6}[A-D]|\d{3}-\d{2}-\d{4})\b",
    "ethnicity or disability": r"\b(ethnicity|disabilit\w*)\b",
}
PERSONAL = {
    "employee ID": r"\bHW-\d{6}\b",
    "email": r"\b[\w.]+@[\w.]+\.\w+\b",
    "phone": r"\+?\d[\d ]{9,}\d",
    "small group": r"\b[1-9] (people|employees|staff|women|men|"
                   r"nurses|technicians)\b",
    "pay of a person": r"\b(salary|pay|rate) (is|of|was)\b",
}
INTERNAL = {
    "internal marking": r"\b(internal|confidential|draft)\b",
    "Hartwell figures": r"\b(headcount|attrition|budget)\b",
}
NAME = re.compile(r"\b([A-Z][a-z]+) ([A-Z][a-z]+)\b")
NOT_NAMES = {"Hartwell", "Field", "Service", "Technician", "Grade",
             "Policy", "Leave", "Annual", "The", "Our", "Data",
             "Readiness", "Register", "Operations", "Shared"}


def classify(text: str) -> tuple[str, list[str]]:
    hits: list[tuple[str, str]] = []
    for cls, rules in (("NEVER", NEVER), ("PERSONAL", PERSONAL),
                       ("INTERNAL", INTERNAL)):
        for why, pat in rules.items():
            flags = 0 if why == "national ID" else re.I
            if re.search(pat, text, flags):
                hits.append((cls, why))
    for a, b in NAME.findall(text):
        if a not in NOT_NAMES and b not in NOT_NAMES:
            hits.append(("PERSONAL", "likely name"))
            break
    if not hits:
        return "OPEN", []
    top = max(CLASSES.index(c) for c, _ in hits)
    return CLASSES[top], [w for c, w in hits if CLASSES.index(c) == top]


def main() -> None:
    from hrai.llm import RunRecorder
    cases = yaml.safe_load((HERE / "paste_cases.yaml").read_text())
    rec = RunRecorder("ch12", "paste_rule")
    agree = 0
    for c in cases["cases"]:
        cls, why = classify(c["text"])
        ok = cls == c["label"]
        agree += ok
        rec.print(f"{c['id']} {cls:<8} label {c['label']:<8}"
                  f"{'' if ok else ' MISS'}  {', '.join(why)}")
        rec.note(case=c["id"], checker=cls, label=c["label"], why=why)
    n = len(cases["cases"])
    rec.print(f"Checker agrees with the privacy office on "
              f"{agree} of {n}")
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
