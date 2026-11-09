"""Chapter 24: which candidate notices each hiring step
triggers, by jurisdiction (no model).

Book section "Telling candidates". Each step of Hartwell's
redesigned path carries the features that matter to the
rules; each rule names the feature it turns on, the duty, and
the evidence record behind it. A rule whose detail is not yet
in the evidence register is marked V (verify) and printed as
such: the table never states more than the register holds.

Not legal advice. As of November 2026.

Run:  HRAI_MODEL=no-model python -m chapters.ch24_candidate_path.notice
"""
from __future__ import annotations

from hrai.llm import RunRecorder

STEPS = {  # step: (Line row, features)
    "advert": ("A02", {"posting"}),
    "knock-out": ("-", {"rule"}),
    "screen lanes": ("A04", {"ai_assists_decision"}),
    "scheduling": ("A03", {"scheduling"}),
    "video answers": ("-", {"recorded_video"}),
    "rejection": ("A05", {"human_decision"}),
}
CODE = {"NYC": "NYC", "Illinois": "IL", "California": "CA",
        "Connecticut": "CT", "Ontario": "ON", "UK": "UK",
        "EU": "EU", "Australia": "AU", "Singapore": "SG"}
JURIS = ["NYC", "Illinois", "California", "Connecticut",
         "Ontario", "UK", "EU", "Australia", "Singapore"]

# (jurisdiction, feature, status, duty, sources)
# status: N = duty recorded in the register, V = verify,
#         X = recorded as outside the rule
RULES = [
    ("NYC", "ai_assists_decision", "N", "bias audit within a "
     "year, public summary, candidate notice", "R-003 R-310"),
    ("NYC", "ai_assists_decision", "V", "notice timing and "
     "alternative-process detail", "-"),
    ("Illinois", "ai_assists_decision", "N", "notice of AI in "
     "covered decisions; no zip-code proxy", "R-064 R-325"),
    ("Illinois", "recorded_video", "V", "AI Video Interview Act "
     "(if AI analyses the video)", "-"),
    ("Illinois", "recorded_video", "N", "written release only if "
     "a face or voice template is made", "R-326"),
    ("California", "ai_assists_decision", "N", "FEHA rules on "
     "automated-decision systems", "R-005"),
    ("Connecticut", "ai_assists_decision", "N", "covered "
     "employment decision technology", "R-327"),
    ("Connecticut", "scheduling", "X", "scheduling excluded "
     "from employment-related decisions", "R-327"),
    ("Ontario", "posting", "N", "posting states whether AI "
     "screens, assesses or selects", "R-040 R-071"),
    ("Ontario", "human_decision", "V", "post-interview response "
     "within 45 days", "-"),
    ("UK", "ai_assists_decision", "N", "tell candidates how AI "
     "processes their data; DPIA", "R-105"),
    ("UK", "human_decision", "N", "if no meaningful human "
     "involvement: Art 22A-D safeguards", "R-243 R-033"),
    ("EU", "ai_assists_decision", "N", "high-risk (Annex III "
     "4(a)) from Dec 2, 2027; inform", "R-020 R-245 R-281"),
    ("EU", "recorded_video", "N", "emotion inference "
     "prohibited at work", "R-022"),
    ("EU", "scheduling", "V", "outside Annex III 4(a), as "
     "onboarding chatbots are", "-"),
    ("Australia", "ai_assists_decision", "N", "privacy policy "
     "names automated decisions from Dec 10, 2026",
     "R-038 R-299"),
    ("Australia", "recorded_video", "N", "the same, for "
     "profiles built from video", "R-038"),
    ("Singapore", "posting", "N", "FCF: 14 days on "
     "MyCareersFuture before an EP or S Pass", "R-330"),
    ("Singapore", "human_decision", "N", "grievance process "
     "under the WFA, from end-2027", "R-107 R-264"),
]


def cell(juris: str, feats: set[str]) -> str:
    """N beats V beats X; '.' when no rule applies."""
    hit = {s for j, f, s, *_ in RULES if j == juris and f in feats}
    for s in "NVX":
        if s in hit:
            return s + ("v" if s == "N" and "V" in hit else "")
    return "."


def main() -> None:
    rec = RunRecorder("ch24", "notice")
    rec.print("duties by step (N recorded, V verify, "
              "X recorded as outside, . none)")
    rec.print(f"{'step':<14}{'row':<5}" +
              "".join(f"{CODE[j]:>4}" for j in JURIS))
    grid = {}
    for step, (row, feats) in STEPS.items():
        cells = [cell(j, feats) for j in JURIS]
        grid[step] = cells
        rec.print(f"{step:<14}{row:<5}" +
                  "".join(f"{c:>4}" for c in cells))
    n = sum(c.startswith("N") for cs in grid.values() for c in cs)
    v = sum(1 for r in RULES if r[2] == "V")
    rec.print(f"cells with a recorded duty: {n}; "
              f"rules to verify: {v}")
    rec.print("knock-out (a rule, no AI): no AI notice, "
              "but the impact table still applies")
    for j, f, s, duty, src in RULES:
        if s == "V":
            rec.print(f"verify: {j}: {duty}")
    rec.note(grid=grid, rules=RULES)
    print(rec.save())


if __name__ == "__main__":
    main()
