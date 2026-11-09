"""Offline tests for Chapter 28 (no key, no network)."""
from pathlib import Path

import numpy as np
import yaml

from chapters.ch28_people_analytics import (analyst_agent, base_rates,
                                            causal, decision_brief)

BRIEFS = yaml.safe_load((Path(decision_brief.__file__).parent
                         / "data" / "briefs.yaml").read_text())


def _brief(i):
    return next(b for b in BRIEFS if b["id"] == i)


def test_dashboard_fails_the_brief():
    f = decision_brief.check(_brief("DB-26-00"))
    assert len(f) == 7 and not any(x.startswith("B5") for x in f)


def test_retention_test_brief_is_ready():
    assert decision_brief.check(_brief("DB-28-01")) == []


def test_tool_cannot_own_the_inference():
    b = dict(_brief("DB-28-01"), inference_owner="analytics agent")
    assert decision_brief.check(b) == [
        "B7 inference owned by a tool, not a person"]


def test_restricted_dimension_is_refused():
    t, why = analyst_agent.run_query({"group_by": ["age_band"]}, [])
    assert t is None and why.startswith("G-DIM")


def test_causal_check_skips_hedged_sentences():
    c = analyst_agent.causal_claims(
        "Pay drives exits. A test would show whether it causes"
        " them.")
    assert c == ["drives"]


def test_flag_nobody_beats_most_lists_on_accuracy():
    y = np.array([True] * 4 + [False] * 96)
    m = base_rates.metrics(np.zeros(100, bool), y)
    assert abs(m["acc"] - 0.96) < 1e-9 and m["lift"] is None


def test_auc_is_half_for_a_constant_score():
    y = np.array([True, False, True, False])
    assert abs(base_rates.auc(np.zeros(4), y) - 0.5) < 1e-9


def test_power_grows_as_the_effect_shrinks():
    assert causal.needed(0.09, 0.06) < causal.needed(0.09, 0.02)
