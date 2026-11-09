"""Chapter 25: the word lists the checks use.

TRAITS are words that describe a person's manner, feelings or
character rather than what they said they did. A kit anchor,
an interview note or an evidence pack that uses one is
describing the candidate, not the answer. PERSONAL topics are
ones a structured interview never asks about and a note never
records. Matching is on whole words, lower case.
"""
from __future__ import annotations

import re

TRAITS = (
    "confident", "confidence", "nervous", "nervousness",
    "anxious", "hesitant", "hesitation", "enthusiastic",
    "enthusiasm", "energetic", "energy", "passionate",
    "passion", "articulate", "fluent", "fluency",
    "personable", "warm", "likeable", "likable", "charisma",
    "charismatic", "presence", "polished", "engaged",
    "engagement", "calm", "composed", "composure",
    "assertive", "shy", "fit", "culture", "attitude",
    "demeanor", "mature", "maturity", "eager", "genuine",
    "sincere", "honest", "honesty", "authentic",
    "stammer", "stutter", "accent", "halting", "rambling",
    "unclear", "struggled", "impression", "gut",
)
PERSONAL = (
    "family", "families", "kids", "children", "child",
    "twins", "daughter", "son", "daycare", "married",
    "wife", "husband", "pregnant", "pregnancy", "expecting",
    "baby", "age", "old", "older", "younger", "born",
    "religion", "religious", "church", "mosque", "prayers",
    "prayer", "faith", "health", "surgery", "disability",
    "disabled", "hearing", "deaf", "aid", "medical",
    "nationality", "originally", "country", "immigrant",
    "outside work",
)


def hits(text: str, words) -> list[str]:
    """Whole-word matches, in list order, each once."""
    low = text.lower()
    found = []
    for w in words:
        if re.search(r"\b" + re.escape(w) + r"\b", low):
            found.append(w)
    return found
