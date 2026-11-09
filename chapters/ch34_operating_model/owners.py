"""Chapter 34: the agent ownership checks, OM-1 to OM-8.

Book section "Every agent has a name on it". The Hartwell
agent ownership register (synthetic), as Olivia Grant's
audit found it on January 31, 2028 (v0) and as DR-34-01
signed it on April 17, 2028 (v1). No model is involved.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch34_operating_model.owners
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from chapters.ch11_automate_keep import line
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
LINE = line.load(line.HERE / "line_v1_1.yaml")
STEPS = {s["id"]: s for s in LINE["steps"]}
RANK = {m: i for i, m in enumerate(reversed(line.MODES))}
MAX_LOAD = 2


def load() -> dict:
    return yaml.safe_load(
        (HERE / "data" / "inventory.yaml").read_text())


def ceiling(step: str) -> line.Placement:
    s = STEPS[step]
    return line.place(s["kind"], line.answers(s["answers"]))


def top_mode(agent: dict) -> str:
    modes = list(agent["rows"].values()) or ["retrieve"]
    return max(modes, key=RANK.get)


def check(agent: dict, reg: dict, load_: Counter) -> dict:
    """Eight yes/no answers for one agent."""
    ppl, po = reg["people"], agent["product_owner"]
    stop = agent["stop"]
    ev = agent["eval"]
    acting = RANK[top_mode(agent)] >= RANK["recommend"]
    rows_ok = all(
        STEPS.get(r) and STEPS[r]["owner"]
        and line.allowed(ceiling(r).mode, m)
        for r, m in agent["rows"].items())
    recs = "recommend" in agent["rows"].values()
    return {
        "OM-1": po in ppl,
        "OM-2": po != reg["platform_owner"],
        "OM-3": rows_ok,
        "OM-4": (len(stop) >= 2
                 and all(p in ppl for p in stop)
                 and len({ppl[p]["tz"] for p in stop}) >= 2),
        "OM-5": (bool(ev["owner"]) and bool(ev["every_days"])
                 and ev["owner"] in ppl
                 and not (acting and ev["owner"] == po)),
        "OM-6": agent["hours"] > 0,
        "OM-7": (not recs) or set(agent.get(
            "bp_rights", [])) >= {"see", "switch_off",
                                  "monthly_view"},
        "OM-8": load_[po] <= MAX_LOAD,
    }


def audit(reg: dict, version: str) -> list[dict]:
    agents = reg["versions"][version]
    load_ = Counter(a["product_owner"] for a in agents)
    return [{"id": a["id"], **check(a, reg, load_)}
            for a in agents]


def main() -> None:
    rec = RunRecorder("ch34", "owners")
    reg = load()
    checks = [f"OM-{i}" for i in range(1, 9)]
    for v in ("v0", "v1"):
        res = audit(reg, v)
        agents = reg["versions"][v]
        load_ = Counter(a["product_owner"] for a in agents)
        top = load_.most_common(1)[0]
        clean = sum(all(r[c] for c in checks) for r in res)
        rec.print(f"== register {v}: {len(res)} agents, "
                  f"{clean} pass all eight checks")
        rec.print("   " + " ".join(
            f"{c} {sum(r[c] for r in res)}/{len(res)}"
            for c in checks[:4]))
        rec.print("   " + " ".join(
            f"{c} {sum(r[c] for r in res)}/{len(res)}"
            for c in checks[4:]))
        rec.print(f"   heaviest owner: {top[0]}, "
                  f"{top[1]} agents")
        hrs = sum(a["hours"] for a in agents)
        rec.print(f"   funded ownership hours: {hrs} a month")
        for r in res:
            bad = [c for c in checks if not r[c]]
            if bad:
                rec.print(f"   {r['id']:<15} fails "
                          + ", ".join(bad))
        rec.note(version=v, results=res)
    rec.save()


if __name__ == "__main__":
    main()
