"""Chapter 34: sizing the oversight work, 38,000 to 400.

Book section "Sizing: from 38,000 people to 410". Monthly
oversight hours for five organizations (synthetic) from
what they run, not how many people they employ. The rates
are illustrative assumptions; change them and rerun.
Platform engineering and the human route itself (people
answering people) are outside these totals.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch34_operating_model.sizing
"""
from __future__ import annotations

from pathlib import Path

import yaml

from chapters.ch34_operating_model import owners
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
OWN = {"act": 24, "act_with_approval": 20,
       "recommend": 16, "retrieve": 8}
SHARE = {"built": 1.0, "bundled": 0.25, "provider": 0.25}
EVAL_H = 2.0      # one rerun of the agent's test set
SAMPLE_H = 50 / 3 * 4 / 60   # 50 actions a quarter, 4 min
LANE_H = 3.0      # obligations and law watch, per lane
REP_H = 4.0       # monthly briefing per representative body
STOP_H = 2 / 3    # a stop drill a quarter, per agent
MONTH_H = 140     # one full-time person


def hartwell_agents() -> tuple[list[dict], int]:
    agents = owners.load()["versions"]["v1"]
    out = [{"id": a["id"], "mode": owners.top_mode(a),
            "kind": "built", "every_days":
            a["eval"]["every_days"], "hours": a["hours"]}
           for a in agents]
    acts = {r for a in agents for r, m in a["rows"].items()
            if m in ("act", "act_with_approval")}
    return out, len(acts)


def hours(org: dict) -> dict[str, float]:
    if org["agents"] == "from_inventory":
        agents, rows = hartwell_agents()
    else:
        agents, rows = org["agents"], org["action_rows"]
    own = sum(a.get("hours") or
              OWN[a["mode"]] * SHARE[a["kind"]]
              for a in agents)
    ev = sum(EVAL_H * 30 / a["every_days"] for a in agents)
    f = org["forum"]
    return {
        "ownership": own,
        "evaluation": ev,
        "sampling": rows * SAMPLE_H,
        "stop drills": len(agents) * STOP_H,
        "lanes": org["lanes"] * LANE_H,
        "forum": f["members"] * 2 * f["per_year"] / 12,
        "representatives": org["reps"] * REP_H,
    }


def separation(org: dict) -> list[str]:
    """S-rules a combined role breaks."""
    r, out = org["roles"], []
    if org["agents"] == "from_inventory":
        risky = True
    else:
        risky = any(a["mode"] != "retrieve"
                    for a in org["agents"])
    if risky and r["evaluator"] == r["product"]:
        out.append("S1")
    if r["signs"] == r["product"]:
        out.append("S2")
    if r["appeal"] == r["process"]:
        out.append("S3")
    if r["platform"] == r["product"]:
        out.append("S4")
    return out


def main() -> None:
    rec = RunRecorder("ch34", "sizing")
    orgs = yaml.safe_load(
        (HERE / "data" / "orgs.yaml").read_text())["orgs"]
    rec.print("== oversight hours a month (illustrative "
              "rates)")
    rec.print(f"{'organization':<15}{'staff':>7}"
              f"{'agents':>7}{'hours':>7}{'FTE':>6}"
              f"{'per 1k':>8}")
    for o in orgs:
        h = hours(o)
        tot = sum(h.values())
        n = (len(owners.load()["versions"]["v1"])
             if o["agents"] == "from_inventory"
             else len(o["agents"]))
        rec.print(f"{o['name']:<15}{o['employees']:>7,}"
                  f"{n:>7}{tot:>7.0f}{tot / MONTH_H:>6.2f}"
                  f"{tot / o['employees'] * 1000:>8.1f}")
        rec.note(org=o["name"], hours=h, total=tot)
    rec.print("== largest share of each total")
    for o in orgs:
        h = hours(o)
        k = max(h, key=h.get)
        rec.print(f"{o['name']:<15}{k}, "
                  f"{h[k] / sum(h.values()):.0%}")
    rec.print("== separation rules a combined role breaks")
    rec.print("   S1 product owner also evaluates; S2 also"
              " signs gates")
    rec.print("   S3 process owner also hears appeals; S4"
              " product owner")
    rec.print("   also runs the platform")
    for o in orgs:
        s = separation(o)
        rec.print(f"{o['name']:<15}"
                  + (", ".join(s) if s else "none"))
    rec.save()


if __name__ == "__main__":
    main()
