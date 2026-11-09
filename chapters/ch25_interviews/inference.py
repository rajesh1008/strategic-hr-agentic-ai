"""Chapter 25: the prohibited-inference list and lane check.

Book sections "What not to infer" and "Is one-way video with
AI scoring defensible anywhere?". A feature of an interview
or assessment product is checked twice: against Hartwell's
prohibited-inference list (policy, every country) and against
the rules each lane's law attaches to it (data/lanes.yaml).
Policy can only remove features the law allows; it never
switches on one the law bans.

Run:  python -m chapters.ch25_interviews.inference
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"


def load(name: str) -> dict:
    return yaml.safe_load((HERE / name).read_text())


def is_ai(f: dict) -> bool:
    return bool(f["infers"]) or f["decides"] != "none" \
        or "transcript" in f["inputs"]


def fires(rule: dict, f: dict) -> bool:
    if "infers_any" in rule and not set(
            rule["infers_any"]) & set(f["infers"]):
        return False
    if "inputs_any" in rule and not set(
            rule["inputs_any"]) & set(f["inputs"]):
        return False
    if "decides_any" in rule and \
            f["decides"] not in rule["decides_any"]:
        return False
    if rule.get("ai") and not is_ai(f):
        return False
    return True


def lane_duties(f: dict, lanes: list[str]) -> dict:
    """lane -> list of (duty, cite) the feature triggers."""
    out: dict[str, list] = {ln: [] for ln in lanes}
    for r in load("lanes.yaml")["rules"]:
        if fires(r, f):
            for ln in r["lanes"]:
                if ln in out:
                    out[ln].append((r["duty"], r["cite"]))
    return out


def verdict(f: dict, lanes: list[str]) -> tuple[str, dict]:
    """NEVER if policy forbids it; BANNED if a lane bans it;
    otherwise DUTIES (with what each lane asks) or CLEAR."""
    never = load("inferences.yaml")["never"]
    duties = lane_duties(f, lanes)
    if any(p in never for p in f["infers"]):
        return "NEVER", duties
    if any(d == "BANNED" for v in duties.values()
           for d, _ in v):
        return "BANNED", duties
    if any(duties.values()):
        return "DUTIES", duties
    return "CLEAR", duties


def duty_lines(d: dict, width: int = 52) -> list[str]:
    """'AUDIT US-NYC; NOTICE CA-ON AU' wrapped to width."""
    by: dict[str, list[str]] = {}
    for ln, x in d.items():
        for k, _ in x:
            if k != "BANNED" and ln not in by.setdefault(k, []):
                by[k].append(ln)
    parts = [f"{k} {' '.join(v)}" for k, v in sorted(by.items())]
    lines, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) + 2 > width:
            lines.append(cur + ";")
            cur = p
        else:
            cur = f"{cur}; {p}" if cur else p
    return lines + [cur] if cur else lines


def main() -> None:
    rec = RunRecorder("ch25", "inference")
    for key, m in load("manifests.yaml").items():
        rec.print(f"== {m['org']}: {m['product']}")
        rec.print(f"   lanes {', '.join(m['lanes'])}")
        for f in m["features"]:
            v, d = verdict(f, m["lanes"])
            state = "on " if f["enabled"] else "off"
            pis = ",".join(f["infers"]) or "-"
            rec.print(f"{f['id']} {state} {v:7s} {f['name']}"
                      f" [{pis}]")
            banned = [ln for ln, x in d.items()
                      if any(k == "BANNED" for k, _ in x)]
            if banned:
                rec.print(f"     banned in {', '.join(banned)}")
            for line in duty_lines(d):
                rec.print("     " + line)
            rec.note(org=key, feature=f["id"], verdict=v,
                     duties={k: x for k, x in d.items() if x})
        live = [f for f in m["features"] if f["enabled"]]
        bad = [f["id"] for f in live
               if verdict(f, m["lanes"])[0] in
               ("NEVER", "BANNED")]
        rec.print(f"   switched on and not allowed: "
                  f"{', '.join(bad) or 'none'}")
    rec.save()


if __name__ == "__main__":
    main()
