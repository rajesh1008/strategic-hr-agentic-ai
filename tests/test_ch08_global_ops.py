"""Offline tests for Chapter 8: hand-off checks, the operations
map and the tier-1 transition. No model, no network."""
import copy

from chapters.ch08_global_ops import (handoff, opsmap,
                                      sow_reader, transition)

D = handoff.load()
C = {c["id"]: c for c in D["contracts"]}


def fails(c):
    return {f.check for f in handoff.check(c, D["rules"])
            if f.ok is False}


def test_revised_meridian_passes_every_check():
    assert fails(C["MER-R"]) == set()


def test_vendor_draft_fails_ten_and_one_is_na():
    res = handoff.check(C["MER-D"], D["rules"])
    assert len(res) == len(handoff.CHECKS) == 12
    assert sum(f.ok is False for f in res) == 10
    assert [f.check for f in res if f.ok is None] == ["DATA-3"]


def test_vendor_cannot_be_answerable():
    c = copy.deepcopy(C["MER-R"])
    c["raci"][5]["A"] = "Meridian Outsourcing"
    assert "RACI-1" in fails(c)


def test_agent_never_on_a_keep_row():
    c = copy.deepcopy(C["MER-R"])
    keep = [r for r in c["raci"] if r["kind"] == "keep"][0]
    keep["R"] = ["agent"]
    assert "RACI-2" in fails(c)


def test_approver_apart_from_request_taker():
    assert "RACI-4" in fails(C["CAL"])
    c = copy.deepcopy(C["CAL"])
    c["raci"][2]["R"] = ["Calder Bank"]
    assert "RACI-4" not in fails(c)


def test_remote_view_needs_a_mechanism():
    c = copy.deepcopy(C["MER-R"])
    c["transfers"][1]["mechanism"] = None
    assert "DATA-1" in fails(c)


def test_provider_agent_needs_its_model_host():
    assert "DATA-2" in fails(C["AUR"])
    c = copy.deepcopy(C["AUR"])
    c["subprocessors"] = [{"name": "Host", "country": "US"}]
    c["transfers"].append({"data": "x", "from": ["CA"],
                           "to": "US", "recipient": "Host",
                           "mechanism": "terms"})
    assert "DATA-2" not in fails(c)


def test_claimed_rate_cannot_cut_seats():
    c = copy.deepcopy(C["MER-R"])
    c["seat_cuts"][0]["status"] = "Tested on our records"
    assert "SLA-3" in fails(c)


def test_map_flows_and_register_gap():
    m = opsmap.load()
    need = opsmap.flows(m)
    assert ("UK", "PH", "Meridian Outsourcing") in need
    gap = need - opsmap.covered(m, C["MER-D"])
    assert ("UK", "PH", "Meridian Outsourcing") in gap


def test_map_reads_modes_from_the_line():
    p = opsmap.placements()
    assert p["H01"] == "automate/act"
    assert p["H02"] == "automate/act_with_approval"
    assert p["D03"].startswith("keep/")


def test_glide_path_forces_no_exits():
    cfg = transition.load()
    plan = cfg["cases"][0]
    assert transition.target(cfg, plan)["target"] == 370
    rows = transition.schedule(cfg, plan)
    assert sum(r["forced"] for r in rows) == 0
    assert rows[-1]["end"] == 370


def test_one_quarter_cut_forces_exits():
    cfg = transition.load()
    vend = [c for c in cfg["cases"]
            if c["cut"] == "one quarter"][0]
    rows = transition.schedule(cfg, vend)
    assert rows[0]["forced"] == 146


def test_keyed_fields_and_overlay():
    k = sow_reader.keyed(C["MER-D"])
    assert k["seat_cut"] == 189 and not k["seat_cut_measured"]
    got = {f: {"value": v} for f, v in k.items()}
    m = sow_reader.overlay(C["MER-D"], got)
    base = handoff.sla(C["MER-D"], D["rules"])
    again = handoff.sla(m, D["rules"])
    assert [f.ok for f in base] == [f.ok for f in again]
