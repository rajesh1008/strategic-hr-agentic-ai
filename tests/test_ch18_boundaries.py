"""Offline tests for Chapter 18 (no model calls)."""
from pathlib import Path

from chapters.ch18_boundaries import (cvscreen, monitoring,
                                      retention, steered,
                                      transfers)
from chapters.ch18_boundaries.tickets import TICKETS

import yaml

CVS = Path(cvscreen.__file__).parent / "data" / "cvs"


def attacks():
    return [t for t in TICKETS if t["kind"] == "attack"]


def test_steered_harm_by_build():
    for build, want in (("plain", 7), ("guarded", 7),
                        ("bounded", 0)):
        harm = sum(bool(g["leaked"] or g["dispatched"])
                   for g in (steered.play(build, t)
                             for t in attacks()))
        assert harm == want, build


def test_bounded_marks_blocked_link_as_steered():
    t8 = [t for t in attacks() if t["id"] == "T8"][0]
    g = steered.play("bounded", t8)
    assert g["steered"] and not g["leaked"]


def test_visible_extractor_drops_hidden_text():
    html = (CVS / "cv_b.html").read_text()
    raw, _ = cvscreen.extract(html, "raw")
    vis, flags = cvscreen.extract(html, "visible")
    assert "6 years" in raw and "6 years" not in vis
    assert flags == ["hidden text removed: 28 words"]


def test_visible_note_is_flagged_not_removed():
    html = (CVS / "cv_c.html").read_text()
    vis, flags = cvscreen.extract(html, "visible")
    assert "6 years" in vis and len(flags) == 1


def test_rule_needs_both_requirements():
    assert cvscreen.meets({"epa_608": "yes", "field_years": 2})
    assert not cvscreen.meets({"epa_608": "yes",
                               "field_years": 1})
    assert not cvscreen.meets({"epa_608": "unclear",
                               "field_years": 6})


def test_monitoring_verdicts():
    got = {(p["id"], p["version"]):
           monitoring.verdict(monitoring.check(p))
           for p in monitoring.load()}
    assert got[("NL-1", "v3")] == "PROCEED"
    assert got[("AT-1", "v1")] == "STOP"
    assert got[("LK-1", "v1")] == "STOP"
    assert got[("CB-1", "v1")] == "NOT YET"


def test_transfers_reconcile():
    d = transfers.DATA
    reg = yaml.safe_load((d / "register.yaml").read_text())
    log = yaml.safe_load((d / "access_log.yaml").read_text())
    missing = [a for a, hit in transfers.reconcile(reg, log)
               if not hit]
    assert len(missing) == 5


def test_retention_gaps():
    cfg = yaml.safe_load(
        (retention.DATA / "retention.yaml").read_text())
    n = sum(len(retention.check(c, set(cfg["never"])))
            for c in cfg["classes"])
    assert n == 8


def test_august_files_close_every_gap():
    d = transfers.DATA
    reg = yaml.safe_load((d / "register_aug.yaml").read_text())
    log = yaml.safe_load((d / "access_log_aug.yaml").read_text())
    assert all(hit for _, hit in transfers.reconcile(reg, log))
    assert not any(transfers.check_row(x) for x in reg)
    cfg = yaml.safe_load((d / "retention_aug.yaml").read_text())
    assert not any(retention.check(c, set(cfg["never"]))
                   for c in cfg["classes"])
