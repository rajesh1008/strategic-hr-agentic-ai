"""Chapter 32: the voice map (no model).

Book section "The voice map". One row per population: who
speaks for it, and the strongest right that channel has over
a new AI step. Then, for each AI system, whether every
population it touches was told through its channel before
go-live. A population whose channel has no legal right still
gets the pack: the right decides what Hartwell must do, not
whom Hartwell tells.

  VM-1  every population has a channel and a named contact
  VM-2  every right has a basis (an evidence ID or VERIFY)
  VM-3  every population a system touches was informed
  VM-4  the contact was chosen by the workers themselves

Run:  HRAI_MODEL=no-model python -m chapters.ch32_voice.voice
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"
ORDER = ["bargain", "consent", "consult", "inform", "none"]


VERSIONS = {"2028-01": "voice.yaml",
            "2028-06": "voice_2028_06.yaml"}


def load(version: str = "2028-01") -> dict:
    path = HERE / VERSIONS[version]
    return yaml.safe_load(path.read_text())


def gaps(v: dict) -> list[tuple[str, str]]:
    out = []
    for p in v["populations"]:
        if not (p.get("channel") and p.get("contact")):
            out.append(("VM-1", p["id"]))
        if not p.get("basis"):
            out.append(("VM-2", p["id"]))
        if not p.get("elected"):
            out.append(("VM-4", p["id"]))
    for s in v["systems"]:
        told = set(v["informed"].get(s["use"], []))
        for pid in s["touches"]:
            if pid not in told:
                out.append(("VM-3", f"{s['use']} {pid}"))
    return out


def main() -> None:
    v = load()
    rec = RunRecorder("ch32", "voice")
    rec.print("Voice map 2028-01")
    pops = v["populations"]
    total = sum(p["n"] for p in pops)
    rec.print(f"{'population':11s} {'n':>6s}  "
              f"{'right':8s} channel")
    rank = lambda p: ORDER.index(p["right"])  # noqa: E731
    for p in sorted(pops, key=rank):
        rec.print(f"{p['id']:11s} {p['n']:6,d}  "
                  f"{p['right']:8s} {p['channel']} "
                  f"({p['contact']})")
    for r in ORDER:
        n = sum(p["n"] for p in pops if p["right"] == r)
        if n:
            rec.print(f"right {r:8s} {n:6,d} ({n / total:.1%})")
            rec.note(right=r, n=n)
    legal = sum(p["n"] for p in pops if p["right"] != "none")
    rec.print("With a legal right over a new AI step: "
              f"{legal:,d} of {total:,d} ({legal / total:.1%})")
    none = sum(p["n"] for p in pops if not p.get("elected"))
    rec.print(f"With no contact the workers chose: {none:,d} "
              f"({none / total:.1%})")
    g = gaps(v)
    rec.print(f"Gaps: {len(g)}")
    for cid, what in g:
        rec.print(f"  {cid} {what}")
        rec.note(gap=cid, what=what)
    later = gaps(load("2028-06"))
    rec.print(f"Voice map 2028-06 gaps: {len(later)}")
    for cid, what in later:
        rec.print(f"  {cid} {what}")
    rec.save()


if __name__ == "__main__":
    main()
