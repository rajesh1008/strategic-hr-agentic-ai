"""Offline tests for hrai.ledger (no model calls)."""
import pytest

from hrai.ledger import Claim, Ledger, LedgerError, Measurement, Status


def claim(**kw):
    base = dict(claim_id="C-01", claimant="Takefen", statement="cuts screening time by 70%",
                metric_id="screening_minutes", metric_definition="recruiter minutes per application",
                value=70.0, unit="percent reduction", source="contract schedule", owner="Daniel Brooks",
                version="4.2")
    base.update(kw)
    return Claim(**base)


def tested(value=24.0, **kw):
    base = dict(status="Tested on our records", metric_id="screening_minutes", value=value,
                version="4.2", measured_by="Hartwell people analytics", records="field reqs",
                n=120, period="Mar-May 2026", method="matched requisitions")
    base.update(kw)
    return Measurement(**base)


def test_new_claim_is_claimed_and_counts_zero():
    c = claim()
    assert c.effective_status() is Status.CLAIMED
    assert c.case_value("base") == 0.0 and c.case_value("planning") == 0.0
    assert c.board_number() is None


def test_tested_promotes_and_records_gap():
    c = claim()
    assert c.add(tested()) is Status.TESTED
    assert c.gap() == -46.0
    assert c.case_value("base") == 0.0
    assert c.case_value("planning") == 12.0
    assert c.board_number() is None


def test_metric_mismatch_refused():
    c = claim()
    with pytest.raises(LedgerError, match="metric mismatch"):
        c.add(tested(metric_id="time_to_shortlist_days"))


def test_missing_evidence_refused():
    with pytest.raises(LedgerError, match="needs n"):
        claim().add(tested(n=0))


def test_vendor_cannot_test_its_own_claim():
    with pytest.raises(LedgerError, match="measured by us"):
        claim().add(tested(measured_by="Takefen customer success"))


def test_vendor_may_demonstrate():
    m = Measurement(status="Demonstrated on vendor data", metric_id="screening_minutes", value=70,
                    version="4.2", measured_by="Takefen", records="benchmark set", n=5000, period="2025")
    assert claim().add(m) is Status.DEMONSTRATED


def test_only_production_supports_board_number():
    c = claim()
    c.add(tested())
    c.add(tested(status="Measured in shadow", value=22.0, baseline="same reqs, human only"))
    assert c.board_number() is None
    c.add(tested(status="Measured in production", value=21.0, baseline="Q1 2027 reqs",
                 owner="Daniel Brooks"))
    assert c.effective_status() is Status.PRODUCTION
    assert c.board_number() == 21.0 and c.case_value("base") == 21.0


def test_version_change_drops_status():
    c = claim()
    c.add(tested())
    c.version = "5.0"
    assert c.effective_status() is Status.CLAIMED
    assert c.effective_status("4.2") is Status.TESTED


def test_quarantined_cannot_be_promoted():
    c = claim(quarantined=True)
    with pytest.raises(LedgerError, match="quarantined"):
        c.add(tested())


def test_roundtrip_and_table(tmp_path):
    led = Ledger("Hartwell (synthetic)")
    c = led.register(claim())
    c.add(tested(), on="2026-06-01")
    c.contest("Hartwell people analytics")
    p = tmp_path / "ledger.json"
    led.save(p)
    back = Ledger.load(p)
    assert back["C-01"].effective_status() is Status.TESTED
    assert "contested" in back.table()
    assert Status.TESTED.tag == "[Tested]{.tag .tested}"
    with pytest.raises(LedgerError):
        led.register(claim())


def test_status_parse():
    assert Status.parse("measured in production") is Status.PRODUCTION
    assert Status.parse("shadow") is Status.SHADOW
    with pytest.raises(ValueError):
        Status.parse("independent")
