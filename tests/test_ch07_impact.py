"""Offline tests for Chapter 7 (no key, no network)."""
import math

import yaml

from chapters.ch07_adverse_impact import adjustments, impact as ai
from chapters.ch07_adverse_impact import make_data, screen_agent


def recs(spec):
    out = []
    for g, n, s in spec:
        out += [{"g": g, "sel": i < s} for i in range(n)]
    return out


def test_fisher_matches_known_value():
    # 3/10 against 8/10: two-sided exact p = 0.0698
    assert math.isclose(ai.fisher_p(3, 10, 8, 10), 0.0698,
                        abs_tol=1e-4)


def test_sd_diff_sign_and_size():
    assert math.isclose(ai.sd_diff(30, 100, 50, 100), -2.887,
                        abs_tol=1e-3)


def test_table_reference_ratio_and_flags():
    rows, miss = ai.table(
        recs([("A", 1000, 600), ("B", 1000, 420),
              ("C", 1000, 540), ("declined", 50, 10)]),
        lambda r: r["g"], lambda r: r["sel"])
    by = {r.group: r for r in rows}
    assert miss == 50
    assert by["A"].flags == ["REF"] and by["A"].ratio == 1.0
    assert math.isclose(by["B"].ratio, 0.70)
    assert "AI" in by["B"].flags
    assert by["B"].shortfall == 60      # 0.8*0.6*1000 - 420
    assert "SIG" in by["C"].flags       # 0.90, p < 0.05


def test_small_group_below_line_is_not_significant():
    rows, _ = ai.table(recs([("A", 20, 11), ("B", 5, 1)]),
                       lambda r: r["g"], lambda r: r["sel"])
    b = next(r for r in rows if r.group == "B")
    assert "<.8" in b.flags and "SM" in b.flags
    assert "AI" not in b.flags


def test_one_person_flag():
    rows, _ = ai.table(recs([("A", 100, 50), ("B", 100, 39)]),
                       lambda r: r["g"], lambda r: r["sel"])
    b = next(r for r in rows if r.group == "B")
    assert "1P" in b.flags              # 40/100 / 0.5 = 0.80


def test_min_share_lists_but_does_not_compare():
    rows, _ = ai.table(
        recs([("A", 990, 500), ("tiny", 10, 1)]),
        lambda r: r["g"], lambda r: r["sel"], min_share=0.02)
    t = next(r for r in rows if r.group == "tiny")
    assert t.flags == ["XS"] and t.ratio is None


def test_intersection_unknown_if_any_part_missing():
    g = ai.intersect("sex", "age")
    assert g({"sex": "F", "age": "40+"}) == "F & 40+"
    assert g({"sex": "declined", "age": "40+"}) == "unknown"


def test_render_fits_64_columns():
    rows, miss = ai.table(
        recs([("Native Hawaiian or Pacific Islander", 40, 10),
              ("White", 900, 500)]),
        lambda r: r["g"], lambda r: r["sel"])
    assert all(len(x) <= 64 for x in ai.render(rows, "t", miss))


def test_data_is_reproducible():
    assert make_data.main(["--check"]) == 0


def test_adjustment_checks_before_and_after():
    cfg = yaml.safe_load(
        (adjustments.HERE / "lakemont_steps.yaml").read_text())
    before, after = cfg["versions"].values()
    assert sum(p for _, p, _ in adjustments.checks(before)) == 0
    assert sum(p for _, p, _ in adjustments.checks(after)) == 6


def test_agent_never_sees_self_id():
    banned = {"sex", "age_40_plus", "race_ethnicity",
              "disability", "veteran"}
    assert not banned & set(screen_agent.SHOWN)
