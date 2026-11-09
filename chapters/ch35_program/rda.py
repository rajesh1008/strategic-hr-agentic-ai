"""Chapter 35: Ready, Done and Accepted as checks.

Book section "Ready, Done, Accepted". A sprint item passes
Ready, Done and Accepted only when every check in the
definition passes on what the tracker and the run records
hold. v0 is the team's working agreement of March 2027; v1
is the program definition signed with DR-35-01 (synthetic).
Deterministic; no model is involved.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch35_program.rda
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from chapters.ch11_automate_keep import line
from hrai.llm import REPO, RunRecorder

HERE = Path(__file__).resolve().parent
LINE = {s["id"]: s for s in
        line.load(line.HERE / "line_v1_1.yaml")["steps"]}
RANK = {m: i for i, m in enumerate(reversed(line.MODES))}


def run_ok(ev: str) -> bool:
    """A run ID names a committed record on a clean tree."""
    if ev == "demo" or "/" not in ev:
        return False
    f = list((REPO / "runs").glob(ev + "-*.json"))
    return bool(f) and not json.loads(
        f[0].read_text())["git_dirty"]


def ceiling_ok(it: dict) -> bool:
    s = LINE.get(it["line_row"])
    return bool(s) and RANK[it["mode"]] <= RANK[
        s["placement"].mode]


CHECKS = {
    "R0-1": lambda it: it["cases"]["allowed"] > 0,
    "D0-1": lambda it: it["checks_run"]["level1"],
    "D0-2": lambda it: it["cases"]["allowed"] > 0,
    "D0-3": lambda it: True,
    "A0-1": lambda it: bool(it["accepted_by"]),
    "R-1": ceiling_ok,
    "R-2": lambda it: bool(it["classes"]) and all(
        c.get("rule") and c.get("use") for c in it["classes"])
    and {t["reads"] for t in it["tools"]} <= {
        c["class"] for c in it["classes"]},
    "R-3": lambda it: it["cases"]["denied"] >= max(
        1, len(it["classes"])),
    "R-4": lambda it: bool(it["gate_items"]),
    "R-5": lambda it: bool(it["hr_owner"]),
    "R-6": lambda it: it["pack_needed"] is not None,
    "D-1": lambda it: it["checks_run"]["level1"],
    "D-2": lambda it: all(t["enforced_at"] == "adapter"
                          for t in it["tools"]),
    "D-3": lambda it: it["checks_run"]["test_pack_runs"] >= 3,
    "D-4": lambda it: run_ok(it["evidence"])
    or it["evidence"].startswith("northgate-staging/"),
    "D-5": lambda it: it["registry_updated"],
    "D-6": lambda it: it["runbook"],
    "A-1": lambda it: bool(it["hr_owner"])
    and it["accepted_by"] == it["hr_owner"],
    "A-2": lambda it: it["evidence"] != "demo",
    "A-3": lambda it: bool(it.get("gate_evidence_ok_by"))
    and bool(it["gate_items"]),
    "A-4": lambda it: it["run_team_read"],
}


def load(name: str) -> dict:
    return yaml.safe_load((HERE / "data" / name).read_text())


def check(it: dict, d: dict) -> dict[str, list[str]]:
    """Failed check IDs per stage; an empty list passes."""
    return {stage: [c for c in d[stage] if not CHECKS[c](it)]
            for stage in ("ready", "done", "accepted")}


def verdict(failed: dict[str, list[str]]) -> str:
    for stage, word in (("ready", "NOT READY"),
                        ("done", "NOT DONE"),
                        ("accepted", "NOT ACCEPTED")):
        if failed[stage]:
            return word
    return "ACCEPTED"


def fill(it: dict, runs: dict[str, str]) -> dict:
    ev = it["evidence"]
    return dict(it, evidence=runs.get(ev, ev))


def main(runs: dict[str, str] | None = None) -> None:
    rda = load("rda.yaml")
    items = [fill(i, runs or {}) for i in
             load("sprints.yaml")["items"]]
    rec = RunRecorder("ch35", "rda")
    for it in items:
        rec.print(f"== {it['id']} ({it['sprint']['name']},"
                  f" {it['team']})")
        for v in ("v0", "v1"):
            d = rda[v]
            f = check(it, d)
            n = {s: len(d[s]) for s in f}
            ok = {s: n[s] - len(f[s]) for s in f}
            rec.print(f"  {v}: ready {ok['ready']}/{n['ready']},"
                      f" done {ok['done']}/{n['done']},"
                      f" accepted {ok['accepted']}/"
                      f"{n['accepted']} -> {verdict(f)}")
            bad = [c for s in f.values() for c in s]
            for c in bad:
                rec.print(f"      {c} {rda['text'][c]}")
            rec.note(item=it["id"], definition=v, failed=bad,
                     verdict=verdict(f))
    rec.save()


if __name__ == "__main__":
    main()
