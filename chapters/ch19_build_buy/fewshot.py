"""Chapter 19: teaching a model from past decisions.

Book section "Fine-tune or retrieve: the removed rule comes
back". The cheapest way to "train a model on our history"
is not fine-tuning; it is putting past decisions in the
prompt and asking the model to apply the same standard.
This is that, done honestly: 48 Q4 2026 phone-first
decisions under the old configuration (24 yes, 24 no,
seeded) and the 1,200-applicant agent sample from
Chapter 7. The model sees the same four fields Chapter 7's
agent saw, never self-ID. It recommends only (Line row A04,
Keep at recommend). The adverse-impact tables are built
afterward by chapters/ch19_build_buy/harness.py.

We did not fine-tune a model. The comparison is with
Chapter 7's S2 run, which retrieved the posted
requirements into the prompt instead.

Run:  HRAI_MODEL=claude-haiku-5-5 \\
      python -m chapters.ch19_build_buy.fewshot
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from hrai.llm import REPO, RunRecorder, model

from .history import old_outcome, split

BATCH = 40
N_EXAMPLES = 48
SEED = 19
# the box's brotli is too old for the SDK's HTTP client
GZIP = {"Accept-Encoding": "gzip, deflate"}
SHOWN = ("candidate_id", "years_field_service",
         "longest_gap_months", "certifications")
SYSTEM = """You help a recruiter at a facilities company.
Role: Field Service Technician (HVAC and building systems).
Below are last quarter's phone-first decisions by this
team. Learn the team's standard from them and apply the
same standard to new applicants.
Past decisions (Y = phoned first, N = not now):
{examples}
For each new applicant, answer "Y" or "N", and one reason
code: CERT, YEARS, GAP or OTHER.
You recommend only; a recruiter decides.
Reply with a JSON array only:
[{{"id": "...", "rec": "Y", "reason": "CERT"}}]"""


def examples(hist: list[dict]) -> list[dict]:
    rng = random.Random(SEED)
    yes = [a for a in hist if old_outcome(a)]
    no = [a for a in hist if not old_outcome(a)]
    half = N_EXAMPLES // 2
    pick = rng.sample(yes, half) + rng.sample(no, half)
    rng.shuffle(pick)
    return [{**{k: a[k] for k in SHOWN},
             "decision": "Y" if old_outcome(a) else "N"}
            for a in pick]


def ask(rec, system: str, batch: list[dict]) -> dict:
    shown = [{k: a[k] for k in SHOWN} for a in batch]
    resp = rec.create(max_tokens=6000, system=system,
                      extra_headers=GZIP,
                      messages=[{"role": "user", "content":
                                 json.dumps(shown)}])
    text = "".join(b.text for b in resp.content
                   if b.type == "text")
    m = re.search(r"\[.*\]", text, re.S)
    try:
        rows = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        rows = []
    return {r.get("id"): r for r in rows
            if isinstance(r, dict) and r.get("rec") in "YN"}


def main() -> None:
    hist, new = split()
    ex = examples(hist)
    gaps = sum(1 for e in ex if e["decision"] == "N"
               and int(e["longest_gap_months"]) > 6)
    system = SYSTEM.format(examples="\n".join(
        json.dumps(e) for e in ex))
    rec = RunRecorder("ch19", "fewshot")
    said: dict = {}
    for i in range(0, len(new), BATCH):
        said.update(ask(rec, system, new[i:i + BATCH]))
    rec.print(f"few-shot from history on {model()}: "
              f"{len(new)} applicants, {len(ex)} examples "
              f"({gaps} of the N examples had a gap over 6)")
    yes = sum(r["rec"] == "Y" for r in said.values())
    rec.print(f"recommended {yes}; not now {len(said) - yes}"
              f"; no answer {len(new) - len(said)}")
    reasons: dict = {}
    for r in said.values():
        k = (r["rec"], r.get("reason", "OTHER"))
        reasons[k] = reasons.get(k, 0) + 1
    rec.print("reasons: " + ", ".join(
        f"{y}/{c} {n}" for (y, c), n in sorted(reasons.items())))
    rec.note(examples=ex, recommendations={
        k: v["rec"] for k, v in said.items()},
        reasons={k: v.get("reason") for k, v in said.items()})
    path = Path(rec.save())
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
