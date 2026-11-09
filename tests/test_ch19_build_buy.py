"""Offline tests for Chapter 19 (no model, no network)."""
import yaml

from chapters.ch19_build_buy import clauses, diligence, history
from chapters.ch19_build_buy import matrix

D = __import__("pathlib").Path(clauses.__file__).parent / "data"


def load(n):
    return yaml.safe_load((D / n).read_text())


def test_place_order():
    y = {f"Q{i}": "Y" for i in range(1, 7)}
    assert matrix.place(y)[0] == "CONFIGURE"
    n = {f"Q{i}": "N" for i in range(1, 7)}
    assert matrix.place(n)[0] == "REDESIGN"
    b = dict(n, Q1="Y", Q2="Y", Q5="Y")
    assert matrix.place(b)[0] == "BUILD"
    assert matrix.place(dict(n, Q4="Y"))[0] == "BUY"


def test_gate_fail_rejects():
    cfg = load("vendors.yaml")
    r = {k: diligence.assess(v, cfg["gates"])["verdict"]
         for k, v in cfg["vendors"].items()}
    assert r == {"takefen": "REJECT", "northgate": "PROCEED",
                 "fit_match": "REJECT", "vendor_c": "REJECT"}


def test_fix_items_are_the_v1_shortfalls():
    cfg = load("vendors.yaml")
    fix = diligence.assess(cfg["vendors"]["northgate"],
                           cfg["gates"])["fix"]
    v1 = clauses.check(load("terms.yaml")["documents"]
                       ["northgate_v1"])
    short = [c.replace("C", "DD") for c, s in v1.items()
             if s != "ok"]
    assert short == fix


def test_signed_contract_passes_all():
    doc = load("terms.yaml")["documents"]["northgate_v3"]
    assert set(clauses.check(doc).values()) == {"ok"}


def test_history_labels():
    a = {"certifications": "EPA 608 Type I",
         "years_field_service": "3", "longest_gap_months": "9"}
    assert history.posted(a) and not history.old_outcome(a)
    a["longest_gap_months"] = "4"
    assert history.old_outcome(a)
    a["certifications"] = "OSHA 10"
    assert not history.posted(a)


def test_small_model_is_deterministic():
    hist, _ = history.split()
    w1 = history.train(hist[:300], history.posted,
                       ["years", "epa608"])
    w2 = history.train(hist[:300], history.posted,
                       ["years", "epa608"])
    assert w1 == w2


def test_westbridge_price_benchmark_ignores_bids_out_at_gates():
    from chapters.ch19_build_buy import sectors

    class Rec:
        def __init__(self):
            self.lines = []

        def print(self, s):
            self.lines.append(s)

    c = {"weights": {"quality": 60, "price": 40},
         "bids": {"A": {"price_k": 200, "quality": 50, "fails": []},
                  "B": {"price_k": 100, "quality": 90, "fails": ["G1"]}}}
    r = Rec()
    sectors.westbridge(r, c)
    # A is the cheapest bid that passed, so it gets full price points
    assert "bid A GBP 200k: quality 50, score 70.0" in r.lines
