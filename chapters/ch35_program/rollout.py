"""Chapter 35: Brightwater's nine-plant rollout, all at once
or in waves.

Book section "Nine plants, one scheduler". Plan v1 put every
plant live on one date. Plan v2 lets a plant into a wave only
when all six plant Ready checks have closed by that wave's
date, and draws the order of the Ohio plants that are Ready at
the same time by a seeded lottery, so plants still waiting
are the comparison for plants already live (a stepped-wedge
order). Data are synthetic.

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch35_program.rollout
"""
from __future__ import annotations

import random
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent


def load() -> dict:
    p = HERE / "data" / "rollout.yaml"
    return yaml.safe_load(p.read_text())


def open_on(plant: dict, checks: list[str],
            date: str) -> list[str]:
    cl = plant["closed"]
    return [c for c in checks if c not in cl or cl[c] > date]


def waves(d: dict) -> dict[str, list[str]]:
    checks = list(d["checks"])
    rng = random.Random(d["seed"])
    left = list(d["plants"])
    out = {}
    cap = 2
    for w in d["waves"]:
        ready = [p for p in left
                 if not open_on(d["plants"][p], checks, w)]
        first = [p for p in ready
                 if d["plants"][p].get("first")]
        ohio = sorted(p for p in ready
                      if p.startswith("OH-") and p not in first)
        rng.shuffle(ohio)
        other = [p for p in ready
                 if not p.startswith("OH-")]
        take = first + ohio[:max(0, cap - len(first))] + other
        out[w] = take
        left = [p for p in left if p not in take]
    out["not placed"] = left
    return out


def main() -> None:
    d = load()
    checks = list(d["checks"])
    rec = RunRecorder("ch35", "rollout")
    v1 = d["v1_date"]
    rec.print(f"== plan v1: all nine plants live {v1}")
    ready = 0
    for p, pl in d["plants"].items():
        op = open_on(pl, checks, v1)
        ready += not op
        rec.print(f"{p:<7} {'READY' if not op else 'NOT READY'}"
                  f" {' '.join(op)}".rstrip())
    rec.print(f"Ready on {v1}: {ready} of {len(d['plants'])}")
    rec.print("== plan v2: a plant joins a wave once Ready")
    rec.print(f"   Ohio order by lottery, seed {d['seed']},"
              " 2 Ohio plants a wave")
    plan = waves(d)
    for w, ps in plan.items():
        rec.print(f"{w}: {', '.join(ps) or '-'}")
    rec.note(v1_ready=ready, plan=plan)
    print(rec.save())


if __name__ == "__main__":
    main()
