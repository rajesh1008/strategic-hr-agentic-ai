"""Offline tests for Chapter 12 (no model calls)."""
import csv

import pytest

from chapters.ch12_data_readiness import (access, lineage, paste_rule,
                                          quality, readiness)


@pytest.fixture(scope="module")
def reg():
    return readiness.load()


def test_register_quality_matches_scorecard(reg):
    d02 = next(s for s in reg["sources"] if s["id"] == "D02")
    card = quality.scorecard("UKB")
    for m, (ok, n) in card.items():
        assert d02["quality"][m] == round(100 * ok / n, 1)


def test_fixture_counts():
    cat = quality.rows("job_catalog.csv")
    ppl = quality.rows("local_codes.csv")
    assert len(cat) == 120 and len(ppl) == 5200
    assert sum(p["local_code"] in ("UK-R01", "UK-R02") for p in ppl) == 97
    assert sum(p["local_code"] == "" for p in ppl) == 41


def test_verdicts(reg):
    got = {u["id"]: readiness.verdict(readiness.check_use(u, reg))
           for u in reg["uses"]}
    assert got == {"U1": "FIX FIRST", "U2": "READY", "U3": "BLOCKED",
                   "U4": "FIX FIRST", "U5": "FIX FIRST",
                   "U6": "BLOCKED"}


def test_never_list_blocks(reg):
    u = {"id": "T", "name": "t", "purpose": "employee service",
         "reads": {"D01": ["bank_account"]}}
    assert readiness.verdict(readiness.check_use(u, reg)) == "BLOCKED"


def test_consent_flag_only_for_employees_in_europe():
    base = {"id": "X", "owner": "o", "category": "ordinary",
            "retention": "r", "deletion": "d", "lineage": []}
    emp = dict(base, subjects=["UK"], basis={"UK": "consent"})
    app = dict(emp, people="applicants")
    us = dict(base, subjects=["US"], basis={"US": "consent"})
    assert readiness.check_source(emp)[0][0] == readiness.FIX
    assert readiness.check_source(app) == []
    assert readiness.check_source(us) == []


def test_write_must_be_controlled_action(reg):
    u = {"id": "T", "name": "t", "purpose": "job architecture",
         "reads": {"D02": ["code"]},
         "writes": {"D02": {"fields": ["grade"], "via": "direct"}}}
    assert readiness.verdict(readiness.check_use(u, reg)) == "BLOCKED"


def test_manifest_and_reader(reg):
    with pytest.raises(PermissionError):
        access.manifest("U3", reg)
    r = access.Reader(access.manifest("U5", reg))
    rows = [{"code": "A", "title": "t", "desc": "d", "mapped_grade": "G4"}]
    assert r.read("D02", ["code", "title"], rows) == [
        {"code": "A", "title": "t"}]
    with pytest.raises(PermissionError):
        r.read("D02", ["code", "mapped_grade"], rows)
    assert [bool(x["refused"]) for x in r.log] == [False, True]
    with pytest.raises(PermissionError):
        r.propose("D02", "A", {"mapped_grade": "F2"}, "x")
    assert r.propose("D02", "A", {"proposed_grade": "F2"},
                     "x")["status"] == "proposed"


@pytest.mark.parametrize("text,cls", [
    ("Explain the leave policy for new starters.", "OPEN"),
    ("Feedback for HW-012771 on handovers.", "PERSONAL"),
    ("Summarize this fit note.", "NEVER"),
    ("Sort code 20-45-77, account 41234567.", "NEVER"),
    ("Compare the 3 women technicians' overtime.", "PERSONAL"),
])
def test_paste_rule(text, cls):
    assert paste_rule.classify(text)[0] == cls


def test_lineage_findings():
    import yaml
    lin = yaml.safe_load((lineage.HERE / "lineage.yaml").read_text())
    found = lineage.check(lin)
    assert [n for n, _ in found] == [3, 6, 7, 8]
    assert all("cross-border" in t for _, t in found)
