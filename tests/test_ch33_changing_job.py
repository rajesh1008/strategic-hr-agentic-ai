"""Offline tests for Chapter 33 (no model calls)."""
import random

import yaml

from chapters.ch33_changing_job import (approval_card, approvals,
                                        canvas, checks,
                                        exposure_map, reskill)


def test_role_shares_sum_to_one():
    for r in exposure_map.load()["roles"]:
        assert abs(sum(t["share"] for t in r["tasks"]) - 1) < 1e-9


def test_quayfen_freed_matches_80_of_450():
    d = exposure_map.load()
    qf = next(r for r in d["roles"] if r["id"] == "QF-T1")
    x = exposure_map.reading(qf, d["weights"], d["review_share"])
    assert round(x["freed"] * 450) == 80


def test_supervisor_changes_more_than_exposure_rank():
    d = exposure_map.load()
    xs = {r["id"]: exposure_map.reading(r, d["weights"],
                                        d["review_share"])
          for r in d["roles"]}
    by_exp = sorted(xs, key=lambda k: -xs[k]["exposed"])
    by_chg = sorted(xs, key=lambda k: -xs[k]["changed"])
    assert by_exp[-1] == "FS-US"
    assert by_chg.index("FS-US") < by_exp.index("FS-US")


def _canvases():
    p = canvas.Path(canvas.__file__).parent / "data/canvases.yaml"
    return yaml.safe_load(p.read_text())["canvases"]


def test_canvas_results():
    d = exposure_map.load()
    roles = {r["id"]: r for r in d["roles"]}
    got = {c["id"]: [k for k, v in canvas.check(
        c, roles[c["role"]], d).items() if v]
        for c in _canvases()}
    assert got["FS-US v0"] == ["JR-3", "JR-4", "JR-5", "JR-7",
                               "JR-8"]
    assert got["FS-US v1"] == []
    assert got["QF-T1 v1"] == []
    assert got["FN-EM v1"] == ["JR-3"]
    assert got["CB-BR v1"] == ["JR-5"]


def test_reskill_results():
    skills = reskill.canvas_skills(_canvases())
    ps = yaml.safe_load((reskill.DATA / "plans.yaml")
                        .read_text())["plans"]
    got = {p["id"]: [k for k, v in reskill.check(p, skills)
                     .items() if v] for p in ps}
    assert got["RS-ALL"] == ["RS-1", "RS-2", "RS-3", "RS-6"]
    assert got["RS-CB"] == ["RS-4"]
    assert got["RS-QF"] == [] and got["RS-FS"] == []


def test_five_proposals_flagged():
    d = checks.load()
    f = [p["id"] for p in d["proposals"]
         if checks.flagged(p, d["as_of"])]
    assert f == ["P02", "P04", "P05", "P07", "P10"]


def test_grade_card():
    g = approval_card.grade(
        "Ticket expired 2027-12-31.\nExtends shift.\n"
        "Recommendation: Approve", ["ticket"])
    assert g["named"] and g["first"] and g["rec_bad"]
    g = approval_card.grade("Extends shift to 12 h.", ["ticket"])
    assert not g["named"] and not g["rec"]


def test_v2_cuts_approved_despite_failed_check():
    sim = approvals.simulate(random.Random(33))
    s1 = approvals.summary(sim["rows"]["v1"])
    s2 = approvals.summary(sim["rows"]["v2"])
    assert s2["approved_failed"] < s1["approved_failed"] / 3
