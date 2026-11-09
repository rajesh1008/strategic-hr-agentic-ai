"""Chapter 12: check the Data Readiness Register before a build.

check_source() reads one register row; check_use() reads one planned
agent use against the rows it touches. Each finding is BLOCKED or
FIX FIRST; a use with neither is READY. The rules check that the
register's entries exist and follow Hartwell's house rules. They do
not decide what the law requires; counsel and the Group DPO write
the lawful-basis entries. No model is involved.

Run: HRAI_MODEL=no-model python -m chapters.ch12_data_readiness.readiness
(writes runs/ch12/readiness/...)
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
BLOCK, FIX = "BLOCKED", "FIX FIRST"
EUROPE = {"UK", "NL", "DE", "CZ", "IE"}


def load(path: Path = HERE / "register.yaml") -> dict:
    return yaml.safe_load(path.read_text())


def check_source(s: dict) -> list[tuple[str, str]]:
    out = []
    if not s.get("owner") or "none" in s["owner"]:
        out.append((BLOCK, f"{s['id']} has no owner"))
    for lane in s["subjects"]:
        basis = s.get("basis", {}).get(lane)
        if not basis:
            out.append((BLOCK, f"{s['id']} no lawful basis "
                               f"for {lane}"))
        elif (basis == "consent" and lane in EUROPE
              and s.get("people", "employees") == "employees"):
            out.append((FIX, f"{s['id']} relies on employee "
                             f"consent in {lane}"))
        if (s["category"] == "special"
                and not s.get("condition", {}).get(lane)):
            out.append((BLOCK, f"{s['id']} special category,"
                               f" no condition for {lane}"))
    for hop in s.get("lineage", []):
        if hop.get("owner", "none") == "none":
            out.append((FIX, f"{s['id']} lineage hop "
                             f"'{hop['system']}' has no "
                             "owner"))
        if (hop["system"] == "Model provider"
                and not hop.get("via")):
            out.append((BLOCK, f"{s['id']} reaches a model "
                               "with no gateway"))
    if not s.get("retention"):
        out.append((FIX, f"{s['id']} has no retention period"))
    if not s.get("deletion"):
        out.append((FIX, f"{s['id']} has no deletion route"))
    return out


def check_use(u: dict, reg: dict) -> list[tuple[str, str]]:
    src = {s["id"]: s for s in reg["sources"]}
    out: list[tuple[str, str]] = []
    touched = set(u.get("reads", {}))
    touched |= set(u.get("writes", {}))
    for sid in sorted(touched):
        out += check_source(src[sid])
    for sid, fields in u.get("reads", {}).items():
        s = src[sid]
        for f in fields:
            if f not in s["fields"]:
                out.append((BLOCK, f"{sid}.{f} is not in "
                                   "the register"))
            elif f in s.get("never", []):
                out.append((BLOCK, f"{sid}.{f} is never "
                                   "read by an agent"))
        for lim in s.get("use_limits", []):
            if u.get("lane", lim["lane"]) != lim["lane"]:
                continue
            if u["purpose"] not in lim["allow"]:
                out.append((BLOCK, f"{sid} in {lim['lane']}: "
                                   f"{lim['rule']}"))
    for sid, w in u.get("writes", {}).items():
        if (w["fields"]
                and w.get("via") != "controlled_action"):
            out.append((BLOCK, f"{sid} write is not a "
                               "controlled action"))
    for sid, need in u.get("need", {}).items():
        have = src[sid].get("quality", {})
        for m, floor in need.items():
            if m not in have:
                out.append((FIX, f"{sid} {m} not measured"))
            elif have[m] < floor:
                out.append((FIX, f"{sid} {m} {have[m]}% needs "
                                 f"{floor}%"))
    return out


def verdict(findings: list[tuple[str, str]]) -> str:
    levels = {lvl for lvl, _ in findings}
    return BLOCK if BLOCK in levels else FIX if FIX in levels \
        else "READY"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        HERE / "register.yaml"
    reg = load(path)
    rec = RunRecorder("ch12", "readiness")
    rec.print(f"Data Readiness Register v{reg['version']}, "
              f"{reg['as_of']}: {len(reg['sources'])} sources, "
              f"{len(reg['uses'])} planned uses")
    for u in reg["uses"]:
        f = check_use(u, reg)
        seen = list(dict.fromkeys(f))
        rec.print(f"{u['id']} {verdict(f)}: {u['name']}")
        for lvl, text in seen:
            rec.print(f"   {'B' if lvl == BLOCK else 'F'}  {text}")
        rec.note(use=u["id"], verdict=verdict(f),
                 findings=[t for _, t in seen])
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
