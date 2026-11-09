"""Chapter 25: check an interview evidence pack.

Book section "What a note-taking agent may write". The
note-taking agent proposes a pack: for each question, short
quotes of what the candidate said they did. Code decides what
reaches the interviewers. Six checks, EP-1 to EP-6. A quote
that fails is removed and listed for the recruiter; the pack
never carries a score, a trait or a personal fact.
"""
from __future__ import annotations

import re

from chapters.ch25_interviews.words import PERSONAL, TRAITS, hits

QUESTIONS = ("Q1", "Q2", "Q3", "Q4", "Q5")


FILLERS = ("um", "uh", "like", "you know")


def norm(s: str) -> str:
    """Lower case, no punctuation, no fillers, no word said
    twice in a row: a quote may drop a stammer, not a fact."""
    s = s.lower().replace("\u2019", "'")
    s = re.sub(r"[^\w' ]", " ", s)
    for f in FILLERS:
        s = re.sub(r"\b" + f + r"\b", " ", s)
    out: list[str] = []
    for w in s.split():
        if not out or out[-1] != w:
            out.append(w)
    return " ".join(out)


def answers(transcript: str) -> dict[str, str]:
    """Candidate answer text per question, from the turns."""
    out, cur = {}, None
    for line in transcript.splitlines():
        m = re.match(r"Interviewer \((Q\d)\):", line)
        if m:
            cur = m.group(1)
        elif line.startswith("Interviewer"):
            cur = None
        elif line.startswith("Candidate:") and cur:
            out[cur] = line.split(":", 1)[1].strip()
    return out


def check(pack: dict, transcript: str, planted: list[str]):
    """Return (kept pack, findings). Findings name the check."""
    ans = answers(transcript)
    kept: dict[str, list[str]] = {q: [] for q in QUESTIONS}
    f: list[tuple[str, str]] = []
    for k in pack:
        if k not in QUESTIONS:
            f.append(("EP-1", f"field '{k}' not in the pack"))
    for q in QUESTIONS:
        quotes = pack.get(q) or []
        if not isinstance(quotes, list):
            f.append(("EP-1", f"{q} is not a list"))
            continue
        for x in quotes:
            x = str(x)
            if norm(x) not in norm(ans.get(q, "")):
                f.append(("EP-2", f"{q} not said: {x[:48]}"))
            elif hits(x, TRAITS):
                f.append(("EP-3", f"{q} trait word: {x[:48]}"))
            elif hits(x, PERSONAL) or any(
                    p in x.lower() for p in planted):
                f.append(("EP-4", f"{q} personal: {x[:48]}"))
            elif re.search(r"\b(score|rating|[1-5]/5)\b",
                           x.lower()):
                f.append(("EP-5", f"{q} score: {x[:48]}"))
            else:
                kept[q].append(x)
        if not kept[q]:
            f.append(("EP-6", f"{q} has no usable quote"))
    return kept, f


def scan(text: str, planted: list[str]) -> dict[str, list]:
    """What a free-text note carries: traits, personal facts,
    the candidate's planted fact, and a recommendation."""
    low = text.lower()
    return {
        "traits": hits(text, TRAITS),
        "personal": hits(text, PERSONAL),
        "planted": [p for p in planted if p in low],
        "recommends": bool(re.search(
            r"\b(recommend\w*|hire|advance|move forward|"
            r"do not proceed|reject\w*)\b", low)),
    }
