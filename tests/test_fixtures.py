"""Offline tests: the fixture generator is seeded and consistent with
the book's continuity ledger (00-plan/continuity.md)."""
import csv
import gzip
import importlib.util
import json
from pathlib import Path

FIX = Path(__file__).resolve().parent.parent / "fixtures"
spec = importlib.util.spec_from_file_location(
    "generate", FIX / "generate.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _rows(name):
    raw = (FIX / name).read_bytes()
    if name.endswith(".gz"):
        raw = gzip.decompress(raw)
    lines = raw.decode().splitlines()
    assert lines[0].startswith("# _synthetic")
    return list(csv.DictReader(lines[1:]))


def test_generator_is_deterministic_and_matches_files():
    assert gen.main(["--check"]) == 0


def test_hartwell_headcount():
    rows = _rows("hartwell/employees.csv.gz")
    assert len(rows) == 38000
    hr = [r for r in rows if r["job_family"] == "HR"]
    assert len(hr) == 340


def test_412_batch_and_slice_agree():
    b = json.loads((FIX / "hartwell/smart-shortlist-412.json")
                   .read_text())
    cands = {c["id"]: c for c in b["candidates"]}
    assert len(cands) == 412 and "_synthetic" in b
    assert b["applicants_on_requisitions"] == 1031
    sl = json.loads((FIX / "hartwell/smart-shortlist-412-slice.json")
                    .read_text())
    for c in sl["candidates"]:
        assert all(cands[c["id"]][k] == v for k, v in c.items())
    assert sum(c["recruiter_invited_later"]
               for c in cands.values()) == 14


def test_applicants_and_invitations():
    rows = _rows("hartwell/field-tech-applicants.csv")
    assert len(rows) == 1031
    assert sum(r["recruiter_invited"] == "Y" for r in rows) == 61
    moved = [r for r in rows if r["status_fri"] == "not_progressed"]
    assert len(moved) == 412


def test_sector_sizes():
    want = {"brightwater": 21000, "cobbleford-bank": 16000,
            "hollis": 6400, "pennant": 48000, "restonmere": 11000,
            "westbridge": 7500, "thorne-kessler": 6800,
            "aurelia": 19000, "ashby-lowe": 410}
    for slug, n in want.items():
        org = json.loads((FIX / f"sectors/{slug}/org.json")
                         .read_text())
        assert org["employees"] == n and "_synthetic" in org
