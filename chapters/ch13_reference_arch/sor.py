"""System-of-Record Register checks (deterministic).

Book section: "The system-of-record rule". Five checks:
SOR-1 one system of record per field and population;
SOR-2 an agent writes only by controlled action;
SOR-3 every copy has an owner and a deletion route;
SOR-4 an agent that can act on a field reads the record;
SOR-5 no agent store holds a record field.

Run: HRAI_MODEL=no-model python -m \
     chapters.ch13_reference_arch.sor
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).parent / "data" / "sor.yaml"
AGENTS = ("agent", "chatbot", "Shortlist")


def is_agent(who: str) -> bool:
    return any(a in who for a in AGENTS)


def check(reg: dict) -> dict[str, list[str]]:
    bad = {f"SOR-{i}": [] for i in range(1, 6)}
    record_fields = {f["field"] for f in reg["fields"]}
    for f in reg["fields"]:
        name, sor = f["field"], f["sor"]
        if len(sor) != 1 and not f.get("exception"):
            bad["SOR-1"].append(name)
        for w in f["writers"]:
            if is_agent(w["who"]) and \
                    w["via"] != "controlled action":
                bad["SOR-2"].append(f"{name} ({w['who']})")
        for c in f["copies"]:
            if not c.get("owner") or not c.get("deletion"):
                bad["SOR-3"].append(f"{name} in {c['system']}")
        if f["agent_acts"] and f["agent_reads"] not in sor:
            bad["SOR-4"].append(
                f"{name} read from {f['agent_reads']}")
    for s in reg.get("agent_stores", []):
        for h in s["holds"]:
            if h in record_fields:
                bad["SOR-5"].append(f"{h} in {s['store']}")
    return bad


def main() -> None:
    rec = RunRecorder("ch13", "sor")
    regs = yaml.safe_load(DATA.read_text())["registers"]
    for reg in regs:
        bad = check(reg)
        n = sum(len(v) for v in bad.values())
        rec.print(f"{reg['org']} {reg['version']}: "
                  f"{len(reg['fields'])} fields, {n} problems")
        for rule, items in bad.items():
            for it in items:
                rec.print(f"  {rule} {it}")
        for f in reg["fields"]:
            if f.get("exception"):
                e = f["exception"]
                rec.print(f"  exception {f['field']}: until "
                          f"{e['until']}, {e['owner']}")
        rec.note(**{f"{reg['org']} {reg['version']}": bad})
    print(rec.save())


if __name__ == "__main__":
    main()
