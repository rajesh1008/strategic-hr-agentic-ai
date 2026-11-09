"""Check a tool permission table (Chapter 3). No model.

Book section: "The tool permission table". Each agent's
tools are listed as data. The checks are the questions an HR
owner asks before switching an agent on: does every write
name an approver, is every write read back, does a write that
changes someone's work or pay go to a person, is every read
scoped, and does memory say what it keeps and for how long.

Run:  HRAI_MODEL=no-model python -m \
        chapters.ch03_agentic_systems.permissions
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def findings(tool: dict) -> list[str]:
    f, w = [], tool["kind"] == "write"
    if w and tool.get("approver", "none") == "none":
        f.append("write with no approver")
    if w and not tool.get("readback"):
        f.append("write never read back")
    if tool.get("consequential") and \
            "supervisor" not in str(tool.get("approver")) and \
            tool.get("approver") != "human":
        f.append("consequential write without a person")
    if not w and not tool.get("scope"):
        f.append("read with no scope")
    if "memory" in tool["touches"] and (
            tool.get("keeps") == "everything"
            or not tool.get("retain_days")):
        f.append("memory keeps all, no retention")
    return f


def main() -> None:
    rec = RunRecorder("ch03", "permissions")
    tables = yaml.safe_load((HERE / "tool_tables.yaml")
                            .read_text())
    total = 0
    for agent, t in tables.items():
        rec.print(f"{agent} ({t['org']})")
        for tool in t["tools"]:
            f = findings(tool)
            total += len(f)
            rec.print(f"  {tool['name']:<24} {tool['kind']:<5} "
                      + ("; ".join(f) if f else "ok"))
    rec.print(f"findings: {total}")
    print("run record:", rec.save().relative_to(REPO))


if __name__ == "__main__":
    main()
