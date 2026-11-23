# Strategic HR in the Age of Agentic AI, Chapter 13: Still Checking
# Listing: The Stop Rule as a Test

def test_override_is_never_alone(report):
    assert report.catch_rate is not None
    assert report.override_rate is not None

def test_catch_is_not_a_review_score(report):
    assert report.catch_goes_to_performance_file is False

def test_escalation_when_both_fall(month, previous):
    if month.override_rate < previous.override_rate:
        if month.catch_rate < previous.catch_rate:
            assert month.action == "escalate"
