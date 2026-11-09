"""Ashby & Lowe: what a suite copilot can reach on a shared
drive (book section "Three organizations, three ways it goes
wrong"). No model is called.

A suite copilot answers from what the asking user can open, so
its entitlement is the drive's permissions. This scan counts,
for each HR file, how many people outside HR can open it, before
and after the clean-up, then runs one supervisor's question
through retrieval that uses drive permission as entitlement.

Run: HRAI_MODEL=no-model python -m chapters.ch17_surface_brain.drive_scan
(writes runs/ch17/drive_scan/...)
"""
from __future__ import annotations

import yaml

from hrai.llm import RunRecorder

from .entitled import DATA
from .retrieve import bm25

Q = "who is on the redundancy list for my warehouse"


def reach(groups: list[str], sizes: dict) -> int:
    """People outside HR who can open a file (largest group)."""
    out = [sizes[g] for g in groups if g != "hr"]
    return max(out, default=0)


def opens(person: dict, f: dict, when: str) -> bool:
    return bool(set(person["groups"]) & set(f[when]))


def main() -> None:
    d = yaml.safe_load((DATA / "ashby" / "drive.yaml").read_text())
    sizes, files = d["groups"], d["files"]
    dave = d["people"][0]
    rec = RunRecorder("ch17", "drive_scan")
    rec.print("Ashby & Lowe shared drive, HR files (synthetic)")
    rec.print(f"{'file':<38} {'class':<8} before after")
    for f in files:
        if not f["hr"]:
            continue
        name = f["path"].split("/")[-1][:37]
        rec.print(f"{name:<38} {f['sensitive']:<8} "
                  f"{reach(f['before'], sizes):>6} "
                  f"{reach(f['after'], sizes):>5}")
    for when in ("before", "after"):
        bad = [f for f in files if f["hr"] and
               f["sensitive"] == "PERSONAL" and
               reach(f[when], sizes) > 0]
        wide = [f for f in bad if reach(f[when], sizes) >= 41]
        rec.print(f"{when}: PERSONAL HR files open outside HR "
                  f"{len(bad)}")
        rec.print(f"{'':>{len(when) + 2}}open to 41 or more people "
                  f"{len(wide)}")
    rec.print(f"\n{dave['name']}, {dave['title']}")
    rec.print(f"asks: {Q}")
    docs = {f["path"]: {"title": f["path"], "text": f["text"]}
            for f in files}
    for when in ("before", "after"):
        pool = [f["path"] for f in files if opens(dave, f, when)]
        hits = [p for p, _ in bm25(Q, docs, pool)[:3]]
        rec.print(f"  {when}: copilot can ground on")
        for p in hits:
            rec.print(f"    {p}")
    rec.note(files=files, groups=sizes)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
