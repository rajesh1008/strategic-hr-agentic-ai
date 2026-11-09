"""Offline tests for Chapter 9: quota counts, WPS checks and
the transfer checklist. No model, no network."""
import copy

from chapters.ch09_gulf_asia import (model_count, quota,
                                     transfers, wps)

R = quota.load_rules()
HME = quota.load("hartwell_me.yaml")
AE, SA = HME["entities"]


def test_emiratisation_counts_only_registered_skilled():
    r = quota.emiratisation(AE, R["AE-EMIRATISATION"],
                            "2026-12-31")
    assert (r["base"], r["counted"]) == (293, 24)
    assert (r["required"], r["shortfall"]) == (29, 5)
    assert r["aed_year"] == 600_000


def test_rounding_is_a_rule_value_not_code():
    r = quota.emiratisation(AE, R["AE-EMIRATISATION"],
                            "2026-12-31", rounding="ceil")
    assert r["required"] == 30 and r["shortfall"] == 6


def test_nitaqat_weights_and_caps():
    r = quota.nitaqat(SA, R["SA-NITAQAT"])
    # 78 + 22*0.5 + 0 + 0 (undocumented) + 3*4 + 12*0.5
    assert r["weighted"] == 107.0
    assert r["band"] == "Low Green"
    assert quota.band_of(quota.hris_ratio(SA),
                         R["SA-NITAQAT"]) == "Medium Green"


def test_disability_cap_applies():
    ent = copy.deepcopy(SA)
    ent["cohorts"][4]["n"] = 20     # more than 10% of heads
    r = quota.nitaqat(ent, R["SA-NITAQAT"])
    heads = r["heads"]              # 145
    capped = int(0.10 * heads)      # 14 at weight 4
    assert r["weighted"] == 78 + 11 + capped * 4 + 6 + 6


def test_rules_are_not_mutated():
    before = copy.deepcopy(R["SA-NITAQAT"])
    quota.nitaqat(SA, R["SA-NITAQAT"])
    assert R["SA-NITAQAT"] == before


def test_documenting_contracts_moves_band():
    fixed = [dict(c, qiwa_documented=True)
             for c in SA["cohorts"]]
    r = quota.nitaqat(dict(SA, cohorts=fixed), R["SA-NITAQAT"])
    assert r["band"] == "Medium Green"


def test_ghafline_drift_found():
    rim = quota.load("ghafline_ae.yaml")["entities"]
    moves = quota.drift(*rim, [1, 2, 3])
    assert moves == [("site supervisor", 64)]
    a, b = (quota.emiratisation(e, R["AE-EMIRATISATION"],
                                "2026-12-31") for e in rim)
    assert (a["shortfall"], b["shortfall"]) == (9, 2)


def test_wps_finds_planted_problems():
    rule = wps.load_rules()
    roster = wps.read("ghafline_roster_2027-01.csv")
    lines = wps.read("ghafline_wps_2027-01.csv")
    ctl = dict(x.split("=") for x in (
        wps.DATA / "ghafline_wps_2027-01.control"
    ).read_text().split())
    from datetime import date
    found, tot = wps.check(roster, lines, ctl, rule,
                           date(2027, 1, 1))
    n = {k: sum(f[0] == k for f in found) for k in wps.OWNER}
    assert n == {"MISSING": 9, "NOT_ON_ROSTER": 1, "SHORT": 23,
                 "BANNED_DEDUCTION": 11, "NO_ACCOUNT": 1,
                 "CONTROL": 1, "LATE": 1}
    assert tot["days"] == 3


def test_transfers_never_ok_without_regulations():
    d = transfers.load()
    got = {f["id"]: transfers.assess(f, d["lanes"])[0]
           for f in d["flows"]}
    assert got == {"T1": "UNCLEAR", "T2": "GAP", "T3": "GAP",
                   "T4": "OK", "T5": "GAP"}


def test_model_prompt_has_rules_and_no_hris_view():
    p = model_count.prompt(SA, R)
    assert "ILLUSTRATIVE" in p and "hris_view" not in p
    assert model_count.truth(SA, R, "2026-12-31")[
        "weighted"] == 107.0


def test_parse_takes_first_json_object():
    assert model_count.parse('x {"a": 1} y') == {"a": 1}
