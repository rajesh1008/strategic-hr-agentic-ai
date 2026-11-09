"""Offline tests for Chapter 20: graders, unit checks, the
re-grade, the outcome scorer and the sector cases. No model."""
import yaml

from chapters.ch20_eval_pyramid import (outcome, regrade,
                                        sectors, unit)
from chapters.ch20_eval_pyramid.graders import grade

CASES = yaml.safe_load(open(
    "chapters/ch20_eval_pyramid/data/golden.yaml"))["cases"]


def seen(actions, writes=0, handoff=False, reply="",
         emp="HW-012771"):
    return {"actions": actions, "writes": writes,
            "handoff": handoff, "reply": reply, "emp": emp}


def test_golden_set_has_18_cases():
    assert sorted(CASES) == [f"G{i:02d}" for i in range(1, 19)]


def test_state_beats_words():
    s = seen([["address_change", "done", "HW-012771", 1]], 1,
             reply="Your address change is in progress.")
    assert grade(CASES["G18"], s)["fails"] == ["STATE",
                                               "WRITES"]


def test_claim_without_done_fails():
    s = seen([["bank_detail_change", "awaiting_approval",
               "HW-012771", 0]],
             reply="Done. Your bank account is updated.")
    assert "CLAIM" in grade(CASES["G03"], s)["fails"]


def test_other_persons_record_fails_own():
    s = seen([["bank_detail_change", "awaiting_approval",
               "HW-019044", 0]])
    assert "OWN" in grade(CASES["G04"], s)["fails"]


def test_unit_checks_all_pass():
    assert all(unit.run_checks().values())


def test_v11_makes_handoff_forbidden_on_bank_waits():
    g = regrade.golden(regrade.V11)
    assert g["G03"]["expect"]["handoff"] == "forbidden"
    assert g["G15"]["expect"]["handoff"] == "forbidden"


def test_outcome_definitions():
    r = {"end": "done", "repeat_7d": False,
         "reversed_30d": False, "human_min": None,
         "nothing": False}
    assert outcome.contained(r) and outcome.resolved(r)
    r["repeat_7d"] = True
    assert outcome.contained(r) and not outcome.resolved(r)


def test_outcome_log_is_reproducible():
    assert outcome.generate() == outcome.generate()


def test_lakemont_defect_is_time_only():
    busy = {"RN-01": 3 * 24 + 7}    # RN-01 not rested
    out = sectors.fill([(3, "ICU", 7)], 0, busy)
    assert out[0][2] == "RN-02" and out[0][3] <= 3
    assert sectors.fill([(0, "ICU", 7)], 0, {})[0][3] > 0
