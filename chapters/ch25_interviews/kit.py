"""Chapter 25: check a structured interview kit.

Book section "A structured interview Hartwell can defend".
Seven checks, KIT-1 to KIT-7. A kit passes when all seven do.

Run:  python -m chapters.ch25_interviews.kit
"""
from __future__ import annotations

from pathlib import Path

import yaml

from chapters.ch25_interviews.words import PERSONAL, TRAITS, hits
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
CHECKS = {
    "KIT-1": "every question tied to job-analysis tasks",
    "KIT-2": "anchors at 1, 3 and 5 for every question",
    "KIT-3": "anchors describe behavior, not traits",
    "KIT-4": "no question about a personal topic",
    "KIT-5": "fixed probes only",
    "KIT-6": "scored alone before discussion; no overall"
             " impression",
    "KIT-7": "an adjustment route on the invitation",
}


def check(kit: dict) -> dict[str, list[str]]:
    """Return check -> list of findings (empty = pass)."""
    f: dict[str, list[str]] = {k: [] for k in CHECKS}
    for q in kit["questions"]:
        qid, a = q["id"], q.get("anchors") or {}
        if not q.get("tasks"):
            f["KIT-1"].append(qid)
        if not all(k in a for k in (1, 3, 5)):
            f["KIT-2"].append(qid)
        for lvl, text in a.items():
            for w in hits(str(text), TRAITS):
                f["KIT-3"].append(f"{qid}.{lvl} '{w}'")
        for w in hits(q["ask"], PERSONAL):
            f["KIT-4"].append(f"{qid} '{w}'")
        if "any" in q.get("probes", []):
            f["KIT-5"].append(qid)
    s = kit["scoring"]
    if not s["independent_before_discussion"]:
        f["KIT-6"].append("scored together")
    if s["overall_impression_rating"]:
        f["KIT-6"].append("overall impression rating")
    if not kit.get("adjustments", "").strip():
        f["KIT-7"].append("none")
    return f


def main() -> None:
    rec = RunRecorder("ch25", "kit")
    for name in ("kit_ft_v0.yaml", "kit_ft_v1.yaml"):
        kit = yaml.safe_load((HERE / "data" / name).read_text())
        res = check(kit)
        ok = sum(1 for v in res.values() if not v)
        rec.print(f"== {kit['kit']} v{kit['version']}: "
                  f"{len(kit['questions'])} questions, "
                  f"passes {ok} of {len(CHECKS)}")
        for k, v in res.items():
            mark = "ok  " if not v else "FAIL"
            tail = "" if not v else ": " + ", ".join(v)
            rec.print(f"  {mark} {k} {CHECKS[k]}{tail}")
        rec.note(kit=name, findings=res)
    rec.save()


if __name__ == "__main__":
    main()
