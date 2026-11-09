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


def test_line_v1_1_moves_f05_to_keep():
    d = line.load(line.HERE / "line_v1_1.yaml")
    f05 = next(s for s in d["steps"] if s["id"] == "F05")
    assert str(f05["placement"]) == "keep/recommend"
    assert sum(s["placement"].side == "keep" for s in d["steps"]) == 24


def test_register_v1_has_gaps_and_v1_1_is_clean():
    from chapters.ch11_automate_keep import register
    reg = register.load()
    gaps = register.check(line.load(), reg)
    assert {sid for sid, _ in gaps} == {
        "D03", "E04", "E06", "F03", "F07", "G04", "H05"}
    reg11 = register.load(register.HERE / "register_v1_1.yaml")
    assert register.check(line.load(register.LINES["1.1"]), reg11) == []


def test_register_flags_missing_entry_and_self_appeal():
    from chapters.ch11_automate_keep import register
    reg = register.load()
    reg = {**reg, "entries": [e for e in reg["entries"] if e["id"] != "H04"]}
    assert ("H04", "Keep step with no register entry") in register.check(
        line.load(), reg)


def test_sector_lines_place():
    import yaml
    data = yaml.safe_load((line.HERE / "sector_lines.yaml").read_text())
    got = {s["id"]: str(line.place(s["kind"], line.answers(s["answers"])))
           for steps in data["orgs"].values() for s in steps}
    assert got["HP3"] == "keep/retrieve"
    assert got["LK3"] == "keep/recommend"
    assert got["LK4"] == "automate/act_with_approval"
    assert got["AL08"] == "automate/act"


def test_placement_is_monotone_and_kind_capped():
    """A more cautious answer never raises the mode; a read never acts."""
    from itertools import product
    rank = {m: i for i, m in enumerate(line.MODES)}  # 0 = most autonomous
    cautious = {"consequence": True, "reversibility": False, "rule": False,
                "reservation": True, "sensitivity": True}
    for kind in line.KINDS:
        for bits in product([True, False], repeat=5):
            a = dict(zip(line.TESTS, bits))
            p = line.place(kind, a)
            if kind == "read":
                assert p.mode == "retrieve"
            if kind == "draft":
                assert p.mode in ("recommend", "retrieve")
            for t in line.TESTS:
                if a[t] != cautious[t]:
                    q = line.place(kind, {**a, t: cautious[t]})
                    assert rank[q.mode] >= rank[p.mode], (kind, a, t)
