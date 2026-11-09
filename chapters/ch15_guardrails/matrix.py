"""What each manager may read about each person (no model).

Book section: "The entitlement matrix". Prints the decision
for every data class, with the rule that decided it, for two
signed-in managers: Dominic Shaw (outside the bargaining
unit) and Ellie Sutton (a working supervisor inside it).
Run: HRAI_MODEL=no-model python -m \
     chapters.ch15_guardrails.matrix
"""
from __future__ import annotations

from hrai.llm import RunRecorder
from . import entitle as E

CLS = ["job", "pay", "absence_dates", "absence_reason",
       "union"]
SHOW = {"HW-030114": ["HW-031207", "HW-031244", "HW-NL0412",
                      "HW-031319", "HW-NL0147"],
        "HW-031207": ["HW-031244", "HW-031251"]}


def main() -> None:
    m, db = E.load(), E.people()
    rec = RunRecorder("ch15", "matrix")
    rec.print(f"Hartwell entitlements v{m['version']} "
              f"(synthetic)")
    rec.print("person        job   pay   dates reason union")
    for who, targets in SHOW.items():
        s = dict(db[who], roles=["line_manager"])
        rec.print(f"Signed in: {s['name']}, {s['entity']}, "
                  f"unit {s['unit'] or 'none'}")
        for t in targets:
            cells = []
            for c in CLS:
                d = E.can_read(s, db[t], c, m, db)
                cells.append(d.rule if d.allowed else "no")
            name = db[t]["name"].split()[0]
            rec.print(f"  {name:<11} " + " ".join(
                f"{x:<5}" for x in cells))
        rec.note(**{who: targets})
    print(rec.save())


if __name__ == "__main__":
    main()
