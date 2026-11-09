"""Chapter 34 checks, offline (no model calls)."""
from collections import Counter

from chapters.ch34_operating_model import (ask, charter,
                                           owners, sizing)


def test_register_v1_passes_every_check():
    reg = owners.load()
    for r in owners.audit(reg, "v1"):
        assert all(v for k, v in r.items() if k != "id"), r


def test_register_v0_finds_megan_concentration():
    reg = owners.load()
    res = {r["id"]: r for r in owners.audit(reg, "v0")}
    assert not res["ka"]["OM-8"]
    assert not res["svc.sort"]["OM-1"]
    assert not res["line.reader"]["OM-2"]


def test_no_agent_runs_above_its_line_ceiling():
    reg = owners.load()
    for v in ("v0", "v1"):
        assert all(r["OM-3"] for r in owners.audit(reg, v))


def test_load_cap():
    agents = owners.load()["versions"]["v1"]
    n = Counter(a["product_owner"] for a in agents)
    assert max(n.values()) <= owners.MAX_LOAD


def test_charter_v1_clean_v0_not():
    c = charter.load()
    for r in c["versions"]["v1"]:
        assert all(charter.check(r, c["people"]).values())
    assert not all(all(charter.check(r, c["people"]).values())
                   for r in c["versions"]["v0"])


def test_every_question_has_an_answer_code():
    c = charter.load()
    rows = c["versions"]["v1"]
    for q in ask.questions():
        e = ask.expected(q, rows)
        assert e in c["roles"] + ["NOT_SET"], q


def test_grade_counts():
    c = charter.load()
    rows, qs = c["versions"]["v1"], ask.questions()
    perfect = {q["id"]: ask.expected(q, rows) for q in qs}
    assert ask.grade(perfect, qs, rows)["right"] == 12
    assert ask.grade({}, qs, rows)["not_set"] == 11


def test_sizing_scales_with_agents_not_staff():
    import yaml
    orgs = yaml.safe_load((sizing.HERE / "data" /
                           "orgs.yaml").read_text())["orgs"]
    tot = {o["name"]: sum(sizing.hours(o).values())
           for o in orgs}
    assert tot["Straits Ledger"] > tot["Lakemont"]
    assert tot["Hartwell"] < 38000 / 410 * tot["Ashby & Lowe"]
