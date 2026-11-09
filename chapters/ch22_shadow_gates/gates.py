"""Chapter 22: the Five Gates as code, and the refusal record.

Book sections "Five gates, five questions" and "Refusing the
Production gate". A gate pack (data/pack_*.yaml) lists the
evidence for one system at one gate. This code checks it
against the gate's required items (data/gates.yaml):

  - an item with no evidence fails (deny by default);
  - a numeric item is recomputed from its named run
    record, never copied from a slide;
  - an item that is met in one lane and not another fails
    for the lane that lacks it;
  - any failure refuses the gate, and the refusal is
    printed as a record with what would reopen it.

The checker decides nothing a person should: it says
whether the pack holds what the gate asked for. The
accountable executive signs, or refuses, on top of it.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch22_shadow_gates.gates pack_attrition
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder

DATA = Path(__file__).parent / "data"
GATES = yaml.safe_load((DATA / "gates.yaml").read_text())


def events(run_id: str) -> dict:
    folder = REPO / "runs" / Path(run_id).parent
    f = next(folder.glob(f"{Path(run_id).name}-*.json"))
    ev = json.loads(f.read_text())["events"]
    return {k: v for e in ev for k, v in e.items()}


def check(name: str, item: dict | None) -> list[str]:
    """Problems with one evidence item; empty means met."""
    if not item:
        return ["no evidence in the pack"]
    t = item.get("test")
    if t is None:
        bad = [f"{k}: {v}" for k, v in
               item.get("lanes", {}).items() if v != "met"]
        if item.get("status") != "met":
            bad.insert(0, item.get("status", "no status"))
        return bad
    e = events(item["run"]) if "run" in item else {}
    if t == "equals":
        return [] if item["value"] == item["want"] else \
            [f"is '{item['value']}', intent says"
             f" '{item['want']}'"]
    if t == "lift":
        u = e[item["path"][0]]
        base = u["outcomes"]["resigned"] / sum(
            u["outcomes"].values())
        lift = u["hits"] / u["flags"] / base
        return [] if lift >= item["min"] else \
            [f"lift {lift:.2f} below {item['min']}"]
    if t == "ratio_band":
        lo, hi = item["band"]
        out = []
        for lane in item["lanes"]:
            (k1, n1), (k2, n2) = e[lane][item["a"]], \
                e[lane][item["b"]]
            r = (k1 / n1) / (k2 / n2)
            if not lo <= r <= hi:
                out.append(f"{lane.upper()} {item['a']} vs"
                           f" {item['b']} {r:.2f}, outside"
                           f" {lo:.2f} to {hi:.2f}")
        return out
    if t == "at_least_watch":
        u, w = e["us"], e["watch"]
        m, h = u["hits"] / u["flags"], w["hits"] / w["listed"]
        return [] if m >= h else \
            [f"model {m:.3f} per flag, list {h:.3f}"]
    return [f"unknown test {t}"]


def review(pack: dict) -> dict:
    gate = GATES["gates"][pack["gate"]]
    res = {n: check(n, pack["evidence"].get(n))
           for n in gate["requires"]}
    return {"gate": pack["gate"], "items": res,
            "decision": "REFUSE" if any(res.values())
            else "PASS"}


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else \
        "pack_attrition"
    pack = yaml.safe_load((DATA / f"{name}.yaml").read_text())
    rec = RunRecorder("ch22", f"gate_{name.removeprefix('pack_')}")
    r = review(pack)
    rec.print(f"{pack['system']}: {r['gate']} gate")
    rec.print(f"asks: {pack['asks']}")
    for item, probs in r["items"].items():
        rec.print(f"  {'ok  ' if not probs else 'FAIL'} {item}")
        for p in probs:
            rec.print(f"       {p}")
    rec.print(f"decision: {r['decision']}")
    if r["decision"] == "REFUSE":
        rec.print("--- refusal record")
        rec.print(f"owner: {pack['accountable_executive']}")
        rec.print(f"prepared by: {pack['prepared_by']}")
        rec.print("reasons: " + ", ".join(
            k for k, v in r["items"].items() if v))
        rec.print(f"to reopen: {' '.join(pack['to_reopen'].split())}")
    rec.note(review=r)
    print(rec.save())


if __name__ == "__main__":
    main()
