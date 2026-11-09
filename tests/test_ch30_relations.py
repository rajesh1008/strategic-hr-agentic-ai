"""Offline tests for Chapter 30 (no API calls)."""
from chapters.ch30_relations import case as C
from chapters.ch30_relations import checks as K
from chapters.ch30_relations import letter as L
from chapters.ch30_relations import minutes as M
from chapters.ch30_relations import sectors as S
import random


def test_chain_v0_v1():
    case = C.load()
    v1, out = C.folder_v1(case)
    assert out == ["E09"]
    assert [i["id"] for i in v1] == [
        f"E{n:02d}" for n in range(1, 11) if n != 9]


def test_by_date_counts():
    rows = C.by_date(C.load())
    off = sum(r["reader"] == "offline" for r in rows)
    book = sum(r["book"] == "yes" for r in rows)
    assert (len(rows), off, book) == (11, 8, 1)


def test_conclusion_words_skip_quotes():
    assert K.conclusions('He said "we find it likely".') == []
    assert "substantiated" in K.conclusions(
        "The allegation is substantiated.")


def test_minutes_flags():
    c = M.check("He admitted moving the truck. He had "
                "never had a warning. The outcome was "
                "dismissal.")
    assert c["M1"] and c["M3"] and not c["M4"]


def test_letter_numbers():
    rec = {"put_on": "October 20, 2027",
           "appeal": {"name": "A", "window_days": 5}}
    c = L.check("Your appeal goes to A within 5 days of "
                "October 20, 2027, or 14 days.", rec)
    assert c["L1"] == ["14"] and c["L2"]


def test_sectors_seeded():
    rows = S.hollis(random.Random(S.SEED))
    assert rows[0]["rescinded"] == 29 and rows[1]["warnings"] == 141


def test_quote_ellipsis_and_multi_ids():
    items = {i["id"]: i for i in C.load()["items"]}
    assert C.quote_ok(items, "E05", "I was with Gary ... the 17th I think")
    assert not C.quote_ok(items, "E05", "the 17th and the 19th")
    out = {"chronology": [{"item": "E02, E05",
           "quote": "the 17th I think", "event": "x"}]}
    r = K.file_checks(out, items)
    assert r["multi_cites"] == 1 and not r["bad_quotes"]
