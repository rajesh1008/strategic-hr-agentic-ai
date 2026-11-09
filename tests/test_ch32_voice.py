"""Offline tests for chapters/ch32_voice (no key, no network)."""
from collections import Counter

import yaml

from chapters.ch11_automate_keep import line, register
from chapters.ch32_voice import (agreement_final, intake, notice,
                                 pack, represent, voice)
from chapters.ch32_voice.line_change import HERE, V11, V12


def test_line_v12_counts():
    for path, a, k in ((V11, 40, 24), (V12, 37, 27)):
        c = Counter(s["placement"].side
                    for s in line.load(path)["steps"])
        assert (c["automate"], c["keep"]) == (a, k)


def test_register_v12_passes_both_check_sets():
    ld = line.load(V12)
    reg = yaml.safe_load(
        (HERE / "register_v1_2.yaml").read_text())
    assert register.check(ld, reg) == []
    assert represent.check(ld, reg) == []


def test_voice_map_gaps():
    first = voice.gaps(voice.load("2028-01"))
    assert ("VM-3", "skills.suggest HYD") in first
    assert sum(c == "VM-4" for c, _ in first) == 6
    assert voice.gaps(voice.load("2028-06")) == []


def test_only_v22_passes_signed_agreement():
    ds = agreement_final.designs()
    n = {k: sum(bool(ok(d)) for _, _, ok
                in agreement_final.SIGNED)
         for k, d in ds.items()}
    assert n == {"v2": 7, "v2.1": 6, "v2.2": 12}


def test_intake_verdicts():
    case = yaml.safe_load(
        (intake.HERE / "intake_case.yaml").read_text())
    got = [intake.verdict(i)[0] for i in case["items"]]
    assert got == ["REFUSE", "HOLD", "HOLD",
                   "ACCEPT", "ACCEPT"]


def test_pack_denies_by_default():
    packs = yaml.safe_load(
        (pack.HERE / "packs.yaml").read_text())
    assert pack.build(packs["skills.suggest"])[1] == []
    assert pack.build(packs["shift.offer"])[1] == [
        "PK-8", "PK-9"]


def test_notice_checks():
    p = notice.pack_text()
    c = notice.check("We guarantee talent search reads "
                     "your email for 12 weeks.", p)
    assert c["NC-1"] == ["12"]
    assert c["NC-2"] == ["mobility.match",
                         "learning.recommend"]
    assert c["NC-6"] == ["guarantee"]
    assert not c["NC-4"] and not c["NC-5"]


def test_second_reader_compare_reads_records():
    from chapters.ch32_voice import second_reader_compare as c
    old, new = c.routed_v10(), c.routed_v12()
    assert len(old) == 3 and len(new) == 3
    assert {"F08", "H08"} <= set.intersection(*old)
    assert {"F08", "H08"} <= set.intersection(*new)
