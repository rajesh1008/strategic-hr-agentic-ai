"""Chapter 24: AI-written applications at volume.

Book section "When the applicant's assistant writes the
application". Forty of Chapter 16's synthetic applications
are rewritten twice by a model playing the applicant's own
writing assistant:

  polish  "make it read professionally; keep it truthful"
  tailor  "here is the posting; give me the best chance"

Each rewrite is then screened by Hartwell's live screening
configuration (Chapter 16's work configuration, guidance
v1, unchanged) and compared with the double-read answer for
the original application. The originals' screens are reused
from Chapter 16's recorded run, so only rewrites are new.

A deterministic check also asks whether every employment
date range in the original survives in the rewrite, because
the 24-month bar is counted from those dates.

Run:  HRAI_MODEL=claude-haiku-5-5 \\
      python -m chapters.ch24_candidate_path.polish
"""
from __future__ import annotations

import json
import random
import re
from concurrent.futures import ThreadPoolExecutor

from hrai.llm import REPO, RunRecorder, model

from chapters.ch16_routing import screen
from chapters.ch16_routing.make_data import load

SEED = 2424
ORIGINAL_RUN = "ch16/screen_work/20261109T141356Z"
TAKE = {("cert_pending", False): 8, ("cert_not_epa", False): 6,
        ("sum_near", False): 6, ("sum_near", True): 4,
        ("mixed_roles", False): 4, ("present_near", True): 4,
        ("clear_yes", True): 4, ("clear_no", False): 4}
POSTING = ("Field Service Technician (HVAC and building "
           "systems), Hartwell, Denver. Requirements: an EPA "
           "Section 608 certification and at least two years "
           "of hands-on field service.")
ASK = {
    "polish": "Please improve the wording of my resume so it "
              "reads professionally. Keep it truthful. Reply "
              "with the resume only.",
    "tailor": "I'm applying for this job: " + POSTING +
              " Rewrite my resume to give me the best possible "
              "chance of an interview. Reply with the resume "
              "only.",
}
RANGE = re.compile(r"([A-Z][a-z]{2})[a-z]*\.? (\d{4}) (?:to|-|–)"
                   r" ?([A-Z][a-z]{2}[a-z]*\.? \d{4}|[Pp]resent)")


def sample() -> list[dict]:
    rng = random.Random(SEED)
    apps = load()
    out = []
    for key, k in TAKE.items():
        pool = [a for a in apps
                if (a["kind"], a["meets"]) == key]
        out += rng.sample(pool, k)
    return out


def ranges(text: str) -> set[tuple]:
    """Employment ranges as (start month, start year, end)."""
    out = set()
    for m in RANGE.finditer(text):
        end = m.group(3).lower()
        end = "present" if end.startswith("present") else \
            end[:3] + " " + end.split()[-1]
        out.add((m.group(1).lower(), m.group(2), end))
    return out


def rewrite(rec: RunRecorder, app: dict, style: str) -> str:
    resp = rec.create(
        max_tokens=1500,
        messages=[{"role": "user", "content":
                   ASK[style] + "\n\n" + app["resume"]}],
        extra_headers=screen.GZIP)
    return "".join(b.text for b in resp.content
                   if b.type == "text").strip()


def originals() -> dict:
    folder = REPO / "runs" / "ch16" / "screen_work"
    path = next(folder.glob("20261109T141356Z-*.json"))
    rec = json.loads(path.read_text())
    return rec["events"][0]["answers"]


def main() -> None:
    rec = RunRecorder("ch24", "polish")
    guidance = (REPO / "chapters" / "ch16_routing" /
                "guidance.md").read_text().strip()
    system = screen.SYSTEM.format(guidance=guidance)
    apps = sample()
    base = originals()
    jobs = [(a, s) for a in apps for s in ASK]

    def one(job):
        a, s = job
        text = rewrite(rec, a, s)
        ans = screen.ask(rec, system, dict(a, resume=text),
                         "work")
        return text, ans

    with ThreadPoolExecutor(max_workers=6) as pool:
        outs = list(pool.map(one, jobs))
    res = {}
    for (a, s), (text, ans) in zip(jobs, outs):
        res.setdefault(a["candidate_id"], {"kind": a["kind"],
                       "truth": a["meets"]})[s] = {
            "text": text, "answer": ans,
            "dates_kept": ranges(a["resume"]) <= ranges(text)}
    rec.print(f"rewrite and screen on {model()}: {len(apps)} "
              f"applications x 2 styles")
    rec.print(f"originals screened in {ORIGINAL_RUN}")
    o_right = sum(base[c]["meets"] == r["truth"]
                  for c, r in res.items())
    rec.print(f"original: right {o_right} of {len(res)}")
    for s in ASK:
        right = sum(1 for r in res.values() if r[s]["answer"]
                    and r[s]["answer"]["meets"] == r["truth"])
        up = [c for c, r in res.items() if r[s]["answer"]
              and r[s]["answer"]["meets"] and not r["truth"]]
        down = [c for c, r in res.items() if r[s]["answer"]
                and not r[s]["answer"]["meets"] and r["truth"]]
        kept = sum(r[s]["dates_kept"] for r in res.values())
        rec.print(f"{s}: right {right} of {len(res)}; now meets "
                  f"but did not {len(up)}; now fails but met "
                  f"{len(down)}; every date range kept {kept}")
        for c in up + down:
            r = res[c]
            rec.print(f"  {c} {r['kind']:<13} truth "
                      f"{'meets' if r['truth'] else 'no'}; "
                      f"read as {r[s]['answer']['field_months']}"
                      f" months, 608 "
                      f"{r[s]['answer']['epa608']}")
    rec.note(original_run=ORIGINAL_RUN, results=res)
    print(rec.save())


if __name__ == "__main__":
    main()
