"""Leave policy 2.1 against 2.2 on four request pairs.

Book section: "Closing the split-request gap". Each pair is
two requests from Lena Ruiz (synthetic), the second made
after the first is decided. No model is involved.
Run: HRAI_MODEL=no-model python -m \
     chapters.ch15_guardrails.leave_demo
"""
from __future__ import annotations

from hrai.llm import RunRecorder
from .leave import Calendar, conditions
from .policy import Engine, load_policy

EMP, TODAY = "HW-012771", "2027-04-12"
PAIRS = {
    "A split week": [("2027-06-07", "2027-06-09"),
                     ("2027-06-10", "2027-06-11")],
    "B over a weekend": [("2027-06-17", "2027-06-18"),
                         ("2027-06-21", "2027-06-23")],
    "C second part first": [("2027-06-10", "2027-06-11"),
                            ("2027-06-07", "2027-06-09")],
    "D two separate breaks": [("2027-06-07", "2027-06-08"),
                              ("2027-06-21", "2027-06-22")],
}


def run_pair(version: str, pair) -> list[str]:
    cal = Calendar()
    eng = Engine(load_policy(version), conditions(cal, TODAY))
    out = []
    for a, b in pair:
        d = eng.decide({"employee": EMP, "type": "vacation",
                        "start": a, "end": b})
        if d.effect == "approve_by_rule":
            cal.book(EMP, a, b)
        out.append(f"{a[5:]}..{b[5:]} {d.rule} {d.effect}")
    return out, eng.log


def main() -> None:
    rec = RunRecorder("ch15", "leave_demo")
    rec.print("Leave policy as code, 2.1 vs 2.2 (synthetic)")
    for name, pair in PAIRS.items():
        rec.print(name)
        for v in ("2.1", "2.2"):
            out, log = run_pair(v, pair)
            rec.print(f"  {v}: " + " | ".join(out))
            rec.note(**{f"{name}:{v}": log})
    print(rec.save())


if __name__ == "__main__":
    main()
