"""Chapter 7: what each screening run did, criterion by criterion.

Book section "An agent's step is a selection procedure". No
model is called: this reads the recorded screening runs in
runs/ch07/screen_S1 and screen_S2 and asks two questions of
each. Did the agent follow the posted requirements (at least
one EPA 608 certification and two years of field service)?
And who did the GAP reason hold back, by age and sex?

Run:  HRAI_MODEL=no-model \\
      python -m chapters.ch07_adverse_impact.reasons
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from hrai.llm import REPO, RunRecorder

from . import impact as ai
from .audit import joined
from .make_data import load

RUNS = REPO / "runs" / "ch07"


def meets_posted(a: dict) -> bool:
    return ("EPA 608" in a["certifications"]
            and int(a["years_field_service"]) >= 2)


def answers(record: dict) -> dict:
    """Candidate ID -> (rec, reason), from recorded replies."""
    out = {}
    for call in record["calls"]:
        text = "".join(b.get("text", "") for b in
                       call["response"]["content"]
                       if b.get("type") == "text")
        m = re.search(r"\[.*\]", text, re.S)
        try:
            rows = json.loads(m.group(0)) if m else []
        except json.JSONDecodeError:
            rows = []
        for r in rows:
            if isinstance(r, dict) and r.get("rec") in "YN":
                out[r.get("id")] = (r["rec"],
                                    r.get("reason", "OTHER"))
    return out


def records() -> list[Path]:
    return sorted(p for p in RUNS.glob("screen_S*/*.json")
                  if not p.name.endswith(".tables.json"))


def main() -> None:
    rec = RunRecorder("ch07", "reasons")
    apps = [a for a in load("hartwell-q4-2026.csv")
            if a["agent_sample"] == "Y"]
    recs = joined(apps, load("hartwell-q4-2026-self-id.csv"))
    out: dict = {}
    for path in records():
        run = json.loads(path.read_text())
        said = answers(run)
        tag = f"{path.parent.name[7:]} {run['model']}"
        rec.print(f"== {tag} ({path.stem.split('-')[0]})")
        yes_bad = sum(said.get(a["candidate_id"], ("",))[0] == "Y"
                      and not meets_posted(a) for a in apps)
        no_good = sum(said.get(a["candidate_id"], ("",))[0] == "N"
                      and meets_posted(a) for a in apps)
        rec.print(f"meet posted requirements: "
                  f"{sum(map(meets_posted, apps))} of {len(apps)}")
        rec.print(f"recommended without meeting them: {yes_bad}; "
                  f"held back while meeting them: {no_good}")
        gap = lambda r, s=said: s.get(  # noqa: E731
            r["candidate_id"], ("", ""))[1] != "GAP" or \
            s[r["candidate_id"]][0] != "N"
        held = sum(not gap(r) for r in recs)
        rec.print(f"held back with reason GAP: {held}")
        out[tag] = {"yes_bad": yes_bad, "no_good": no_good,
                    "gap_held": held}
        if held:
            for name, g in (("age", lambda r: r["age"]),
                            ("sex & age",
                             ai.intersect("sex_", "age"))):
                t, miss = ai.table(recs, g, gap)
                for line in ai.render(t, f"-- not held for GAP,"
                                      f" {name}", miss):
                    rec.print(line)
                out[f"{tag}|{name}"] = [ai.as_dict(x) for x in t]
        rec.print()
    path = Path(rec.save())
    side = path.with_name(path.name.split("-")[0]
                          + ".tables.json")
    side.write_text(json.dumps(out, indent=1) + "\n")
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
