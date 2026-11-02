"""Offline tests for the Chapter 11 Line rule (no API calls)."""
from collections import Counter

import pytest

from chapters.ch11_automate_keep import line


def p(kind, letters):
    return str(line.place(kind, line.answers(letters)))


def test_reservation_always_keeps():
    assert p("write", "NYYYN") == "keep/recommend"


def test_consequence_cheap_and_ruled_is_automate_with_approval():
    assert p("write", "YYYNN") == "automate/act_with_approval"


def test_consequence_not_reversible_keeps():
    assert p("write", "YNYNN") == "keep/recommend"


def test_sensitive_keep_is_retrieve_only():
    assert p("write", "YNNNY") == "keep/retrieve"


def test_plain_steps_by_kind():
    assert p("write", "NYYNN") == "automate/act"
    assert p("write", "NNYNN") == "automate/act_with_approval"
    assert p("draft", "NYNNN") == "automate/recommend"
    assert p("read", "NYYNN") == "automate/retrieve"


def test_owner_may_lower_never_raise():
    assert line.allowed("recommend", "retrieve")
    assert not line.allowed("recommend", "act_with_approval")


def test_bad_answers_rejected():
    with pytest.raises(ValueError):
        line.answers("YNY")


def test_hartwell_line_counts():
    steps = line.load()["steps"]
    assert len(steps) == 64
    c = Counter(str(s["placement"]) for s in steps)
    assert c["keep/recommend"] + c["keep/retrieve"] == 23
    assert c["keep/retrieve"] == 12
    assert len({s["id"] for s in steps}) == 64
