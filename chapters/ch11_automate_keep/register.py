"""Chapter 11: the consequential-decision register and its check.

Every Keep step of the Line needs an entry: who decides each case, who
reviews before the decision is issued, who hears an appeal, how long the
person has to ask, and what they are told. check() applies six rules
and lists every gap. No model is involved.

Run: HRAI_MODEL=no-model python -m chapters.ch11_automate_keep.register
     HRAI_MODEL=no-model python -m chapters.ch11_automate_keep.register \
         chapters/ch11_automate_keep/register_v1_1.yaml
(writes runs/ch11/register/...)
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

from . import line

HERE = Path(__file__).resolve().parent
LINES = {"1.0": HERE / "line_v1.yaml", "1.1": HERE / "line_v1_1.yaml"}


def load(path: Path = HERE / "register_v1.yaml") -> dict:
    return yaml.safe_load(path.read_text())


def check(line_data: dict, reg: dict) -> list[tuple[str, str]]:
    """Return (step id, problem) for every rule an entry breaks."""
    keep = {s["id"] for s in line_data["steps"]
            if s["placement"].side == "keep"}
    entries = {e["id"]: e for e in reg["entries"]}
    gaps = []
    if reg["line_version"] != line_data["version"]:
        gaps.append(("-", f"register is for Line v{reg['line_version']}, "
                          f"Line is v{line_data['version']}"))
    for sid in sorted(keep - entries.keys()):
        gaps.append((sid, "Keep step with no register entry"))
    for sid in sorted(entries.keys() - keep):
        gaps.append((sid, "entry for a step that is not on the Keep side"))
    for sid in sorted(keep & entries.keys()):
        e = entries[sid]
        if not e.get("appeal_to"):
            if not e.get("no_appeal_reason"):
                gaps.append((sid, "no appeal path"))
        elif e["appeal_to"] in (e["decider"], e["reviewer"]):
            gaps.append((sid, f"appeal goes to {e['appeal_to']}, "
                              "who decided or reviewed the case"))
        if e["reviewer"] == e["decider"]:
            gaps.append((sid, "reviewer is the decider"))
        if e.get("appeal_to") and e.get("window_days", 0) < 5:
            gaps.append((sid, f"appeal window {e.get('window_days', 0)} "
                              "days; minimum is 5 business days"))
        if len(e.get("reasons", [])) < 2:
            gaps.append((sid, "fewer than two reason codes: the "
                              "decider has nothing to choose"))
    return gaps


def main(path: str | None = None) -> None:
    reg = load(Path(path)) if path else load()
    ld = line.load(LINES[reg["line_version"]])
    rec = RunRecorder("ch11", "register")
    keep = sum(s["placement"].side == "keep" for s in ld["steps"])
    gaps = check(ld, reg)
    bad = {sid for sid, _ in gaps if sid != "-"}
    rec.print(f"Register v{reg['version']} against Line v{ld['version']}: "
              f"{keep} Keep steps, {len(reg['entries'])} entries")
    rec.print(f"Entries with no problem: {keep - len(bad)} of {keep}")
    rec.print(f"Problems: {len(gaps)} on {len(bad)} steps")
    for sid, problem in gaps:
        rec.print(f"{sid}  {problem}")
        rec.note(step=sid, problem=problem)
    for e in reg["entries"]:
        if not e.get("appeal_to") and e.get("no_appeal_reason"):
            rec.print(f"{e['id']}  recorded exception, no appeal: "
                      f"{e['no_appeal_reason']}")
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
