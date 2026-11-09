"""Offline tests for Chapter 13 (no key, no network)."""
import json
from pathlib import Path

import yaml

from chapters.ch13_reference_arch import (integration, sor,
                                          trail_design, views)
from chapters.ch13_reference_arch import skeleton as sk
from chapters.ch13_reference_arch.controlled import (Actions,
                                                     idem_key)
from chapters.ch13_reference_arch.fakes import HartwellOne
from chapters.ch13_reference_arch.reconstruct import reconstruct
from chapters.ch13_reference_arch.trail import Trail

PKG = Path(sk.__file__).parent


def setup(lose=False):
    h = HartwellOne(lose_reply_once=lose)
    t = Trail("T")
    t.add("request", "employee")
    return h, t, Actions(h, t, sk.AGENT)


def test_normal_path_full_chain():
    h, t, a = setup()
    r = a.propose(sk.EMP, "home_address", sk.NEW, sk.EMP)
    assert r["status"] == "done"
    assert h.read(sk.EMP)["home_address"] == sk.NEW
    res = reconstruct(h.audit, t.entries, {sk.AGENT})
    assert [x["missing"] for x in res] == [[]]


def test_timeout_settled_by_readback_no_second_write():
    h, t, a = setup(lose=True)
    assert a.propose(sk.EMP, "home_address", sk.NEW,
                     sk.EMP)["status"] == "unknown"
    again = sk.NEW.replace("Apt 5", "Apt. 5")
    assert idem_key(sk.EMP, "home_address", again) == \
        idem_key(sk.EMP, "home_address", sk.NEW)
    a.propose(sk.EMP, "home_address", again, sk.EMP)
    assert [x["status"] for x in a.settle()] == ["done"]
    assert len(h.audit) == 1


def test_bank_change_waits_for_a_person():
    h, t, a = setup()
    r = a.propose(sk.EMP, "bank_account", "X ****7731", sk.EMP)
    assert r["status"] == "awaiting_approval"
    assert h.audit == []


def test_other_fields_and_other_people_denied():
    h, t, a = setup()
    assert a.propose(sk.EMP, "manager_id", "HW-1",
                     sk.EMP)["status"] == "denied"
    assert a.propose(sk.EMP, "home_address", sk.NEW,
                     "HW-000001")["status"] == "denied"
    assert h.audit == []


def test_trail_holds_no_values():
    h, t, a = setup()
    a.propose(sk.EMP, "home_address", sk.NEW, sk.EMP)
    assert sk.NEW not in json.dumps(t.entries)


def test_memory_refuses_record_fields():
    h, t, a = setup()
    mem = {}
    out = sk.tool("save_note", {"key": "home_address",
                                "value": sk.NEW},
                  h, a, t, mem)
    assert out.startswith("Not kept") and mem == {}


def test_pilot_reconstructs_nothing():
    p = json.loads((PKG / "data/pilot_feb2027.json")
                   .read_text())
    res = reconstruct(p["audit"], p["trail"],
                      set(p["agent_identities"]))
    assert len(res) == 46
    assert not [r for r in res if not r["missing"]]


def test_registers():
    regs = yaml.safe_load((PKG / "data/sor.yaml")
                          .read_text())["registers"]
    counts = [sum(map(len, sor.check(r).values()))
              for r in regs]
    assert counts == [10, 0, 2, 0]


def test_integrations():
    doc = yaml.safe_load((PKG / "data/integrations.yaml")
                         .read_text())
    passes = []
    for s in doc["sets"]:
        used = [i for i in s["interfaces"]
                if i["use"] != "none"]
        passes.append(sum(not integration.check(i, doc["needs"])
                          for i in used))
    assert passes == [3, 9, 0, 3]


def test_views_and_trails():
    rv = yaml.safe_load((PKG / "data/views.yaml")
                        .read_text())["reviews"]
    ready = [[all(m == "C" for m, _ in
                  views.grade(s).values())
              for s in r["systems"]] for r in rv]
    assert ready == [[False] * 5, [True, True, True, False]]
    ds = yaml.safe_load((PKG / "data/trail_designs.yaml")
                        .read_text())["designs"]
    assert [len(trail_design.check(d)) for d in ds] == \
        [0, 3, 2, 0, 4, 0]
