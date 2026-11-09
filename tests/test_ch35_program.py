"""Tests for Chapter 35 (program management)."""
from chapters.ch15_guardrails import entitle
from chapters.ch35_program import (band_sprint, handover,
                                   portfolio, rda, rollout)
import yaml


def test_band_pack_matches_matrix():
    cases = yaml.safe_load(
        (band_sprint.HERE / "data" / "band_pack.yaml")
        .read_text())["cases"]
    for c in cases:
        a = dict(band_sprint.DB[c["asker"]],
                 roles=["line_manager"])
        d = entitle.can_read(a, band_sprint.DB[c["target"]],
                             "band", band_sprint.M,
                             band_sprint.DB)
        assert d.allowed == (c["expect"] == "allowed"), c["id"]


def test_fixed_adapter_withholds():
    a = dict(band_sprint.DB["HW-030114"], roles=["line_manager"])
    out = band_sprint.get_pay_band(a, "HW-NL0412", "fixed")
    assert "band" not in out and "same_entity" in out["withheld"]
    out = band_sprint.get_pay_band(a, "HW-NL0412", "sprint")
    assert "band" in out


def test_ka12_ready_only_under_v0():
    d = rda.load("rda.yaml")
    sp = {s["id"]: s for s in rda.load("sprints.yaml")["items"]}
    v0 = rda.verdict(rda.check(sp["KA-12-04"], d["v0"]))
    v1 = rda.verdict(rda.check(sp["KA-12-04"], d["v1"]))
    assert v0 == "ACCEPTED" and v1 == "NOT READY"


def test_handover_counts():
    b = handover.load()
    jan = handover.grid(b, "2028-01-31")
    jun = handover.grid(b, "2028-06-30")
    assert sum(len(r["open"]) for r in jan) == 11
    assert sum(len(r["open"]) for r in jun) == 2
    assert len(handover.applies(b["services"][0], b)) == 5


def test_rollout_v1_and_waves():
    d = rollout.load()
    checks = list(d["checks"])
    ready = [p for p, pl in d["plants"].items()
             if not rollout.open_on(pl, checks, d["v1_date"])]
    assert ready == ["OH-2", "OH-1"]
    plan = rollout.waves(d)
    assert plan["not placed"] == []
    assert plan["2027-06-07"][0] == "OH-2"


def test_portfolio_loads():
    assert len(portfolio.load()["rows"]) == 16
