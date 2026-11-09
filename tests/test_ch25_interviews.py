"""Offline tests for Chapter 25 (no key, no network)."""
from pathlib import Path

import yaml

from chapters.ch25_interviews import inference, kit, pack, validity
from chapters.ch25_interviews.transcripts import (
    CANDIDATES, PLANTED, transcript)

DATA = Path(kit.__file__).resolve().parent / "data"


def load(name):
    return yaml.safe_load((DATA / name).read_text())


def test_kit_v1_passes_all_and_v0_none():
    v1 = kit.check(load("kit_ft_v1.yaml"))
    v0 = kit.check(load("kit_ft_v0.yaml"))
    assert not any(v1.values())
    assert all(v0.values())


def test_planted_fact_in_every_rendering():
    for cid, *_ in CANDIDATES:
        for r in ("fluent", "disfluent", "second"):
            t = transcript(cid, r).lower()
            assert all(p in t for p in PLANTED[cid])


def test_pack_allows_dropped_stammer_not_new_words():
    t = transcript("C25-01", "disfluent")
    ok = pack.check({"Q1": ["I stopped, locked out the "
                            "breaker at the panel"]}, t, [])
    assert ok[0]["Q1"]
    bad = pack.check({"Q1": ["I stopped and called my "
                             "supervisor"]}, t, [])
    assert not bad[0]["Q1"]
    assert ("EP-2" in [c for c, _ in bad[1]])


def test_pack_drops_extra_fields_and_personal():
    t = transcript("C25-01", "fluent")
    kept, f = pack.check(
        {"Q1": ["I dropped my twins at daycare first"],
         "impression": "confident"}, t, PLANTED["C25-01"])
    codes = [c for c, _ in f]
    assert "EP-1" in codes and not kept["Q1"]


def test_emotion_banned_in_eu_never_by_policy():
    f = {"id": "X", "inputs": ["video"], "infers": ["PI-01"],
         "decides": "ranks"}
    v, d = inference.verdict(f, ["NL", "US-CO"])
    assert v == "NEVER"
    assert ("BANNED", "AI Act Art 5(1)(f)") in d["NL"]
    assert not any(k == "BANNED" for k, _ in d["US-CO"])


def test_content_score_has_duties_not_ban():
    f = {"id": "Y", "inputs": ["video", "transcript"],
         "infers": [], "decides": "ranks"}
    v, d = inference.verdict(f, ["US-IL", "US-NYC", "DE"])
    assert v == "DUTIES"
    assert any(k == "CONSENT" for k, _ in d["US-IL"])
    assert any(k == "AUDIT" for k, _ in d["US-NYC"])


def test_validity_verdicts():
    inv = {m["id"]: validity.verdict(validity.checks(m))
           for m in load("inventory.yaml")["methods"]}
    assert inv == {"M1": "KEEP", "M2": "STOP", "M3": "KEEP",
                   "M4": "FIX", "M5": "STOP", "M6": "KEEP"}
