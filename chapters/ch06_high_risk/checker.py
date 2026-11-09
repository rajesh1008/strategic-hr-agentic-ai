"""Chapter 6: classify an HR AI system under the EU AI Act.

The rules are data and code, never a model. Counsel answers the
facts for each system from records (systems.yaml); classify()
turns the facts into one of five results; article22() applies
the GDPR test for solely automated decisions; obligations()
lists what the deployer (or provider) must do, by date, with the
evidence-register ID behind each item or VERIFY where the book
has no checked record yet.

Run: HRAI_MODEL=no-model \
     python -m chapters.ch06_high_risk.checker
(writes runs/ch06/checker/...)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent

# Annex III point 4 (employment), four triggers [R-020]
ANNEX = ("recruit_select", "work_decisions",
         "task_allocation", "monitor_evaluate")
POINT = {"recruit_select": "4(a)", "work_decisions": "4(b)",
         "task_allocation": "4(b)", "monitor_evaluate": "4(b)"}
# Article 6(3)(a) to (d): narrow procedural task, improves a
# completed human activity, detects patterns without replacing
# human assessment, preparatory task [R-021 for (c) and (d)]
EXEMPT = ("narrow_procedural", "improves_human_work",
          "pattern_check", "preparatory")
FACTS = ("ai_system", "infers_emotion", "medical_or_safety",
         *ANNEX, "profiling", *EXEMPT, "materially_influences")


@dataclass
class Result:
    label: str
    why: str
    points: list[str] = field(default_factory=list)

    @property
    def high_risk(self) -> bool:
        return self.label == "high-risk"


def classify(f: dict[str, bool]) -> Result:
    """The high-risk classification test, in order."""
    if not f["ai_system"]:
        return Result("not an AI system", "rule-based lookup")
    if f["infers_emotion"] and not f["medical_or_safety"]:
        return Result("prohibited", "Art 5(1)(f) emotion")
    pts = [k for k in ANNEX if f[k]]
    if not pts:
        return Result("not high-risk", "outside Annex III 4")
    ex = [k for k in EXEMPT if f[k]]
    if ex and f["profiling"]:
        return Result("high-risk", "profiling: no 6(3)", pts)
    if ex and not f["materially_influences"]:
        return Result("exempt (document it)",
                      f"Art 6(3): {ex[0]}", pts)
    return Result("high-risk", "Annex III 4", pts)


def role(s: dict) -> str:
    """Provider if built in-house, sold under its own name or
    substantially modified; otherwise deployer."""
    if not s["facts"]["ai_system"]:
        return "n/a"
    r = s.get("role_facts", {})
    if r.get("built_in_house") or r.get("own_name") \
            or r.get("substantial_modification"):
        return "provider"
    return "deployer"


def article22(d: dict[str, bool]) -> str:
    """GDPR Article 22: a decision about a person, with legal or
    similarly significant effect, based solely on automated
    processing. Review that cannot change the outcome, or a
    score given a determining role, does not make it human."""
    if not d["decision_about_person"]:
        return "no decision"
    solely = not d["meaningful_review"]
    if solely and d["significant_effect"]:
        return "Art 22 applies"
    if d["significant_effect"]:
        return "outside: meaningful review"
    return "outside: no significant effect"


def dpia_needed(s: dict, res: Result, a22: str) -> list[str]:
    """Hartwell's DPIA trigger: any one reason is enough."""
    if res.label == "prohibited":
        return ["n/a, do not use"]
    why = []
    if res.high_risk:
        why.append("high-risk AI")
    if a22 == "Art 22 applies":
        why.append("Art 22")
    if s["data"].get("systematic_monitoring"):
        why.append("monitoring")
    if s["data"].get("special_category"):
        why.append("special category")
    return why


def obligations(res: Result, who: str,
                table: list[dict]) -> list[dict]:
    """The checklist rows that apply to this result and role."""
    if res.label == "not an AI system":
        return []
    scope = {"all"}
    if res.label == "prohibited":
        scope.add("prohibited")
    if res.high_risk:
        # every system on the inventory is one the employer
        # uses, so deployer duties always apply; a provider
        # carries the design duties on top
        scope |= {"high-risk deployer", f"high-risk {who}"}
    if res.label.startswith("exempt"):
        scope.add("exempt")
    return [o for o in table if o["applies"] in scope]


def load() -> dict:
    return yaml.safe_load((HERE / "systems.yaml").read_text())


def main() -> None:
    from hrai.llm import RunRecorder
    data = load()
    rec = RunRecorder("ch06", "checker")
    rec.print(f"EU AI Act check, rules as of {data['as_of']}")
    for s in data["systems"]:
        res = classify(s["facts"])
        who = role(s)
        a22 = article22(s["decision"])
        dp = dpia_needed(s, res, a22)
        obs = obligations(res, who, data["obligations"])
        ver = sum(1 for o in obs if not o.get("rid"))
        rec.print(f"{s['id']:<4}{s['name'][:40]}")
        pts = "/".join(sorted({POINT[p] for p in res.points}))
        pts = pts or "-"
        rec.print(f"    {res.label} ({res.why}); {who}; "
                  f"points {pts}")
        dps = "no" if not dp else (
            dp[0] if dp[0].startswith("n/a")
            else "yes: " + ", ".join(dp))
        rec.print(f"    {a22}; DPIA {dps}")
        rec.print(f"    AI Act duties {len(obs)}, of which "
                  f"{ver} VERIFY")
        rec.note(system=s["id"], label=res.label, role=who,
                 art22=a22, dpia=dp, duties=len(obs))
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
