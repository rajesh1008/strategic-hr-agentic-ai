# Strategic HR in the Age of Agentic AI, Chapter 12: Year Two
# Listing: The Exit Drill (Under the Hood)
# Questions 5 and 8, the cost of a rule change and how the price is set, are contract terms read by procurement rather than tested in code.

def exit_drill(vendor, held_out) -> dict[str, bool]:
    """Run before every renewal. Any False is a renewal condition."""
    rules = vendor.export_rules()                  # Q1: readable table, no charge
    logs = vendor.export_decision_logs()           # Q2: inputs and versions
    score = vendor.score(held_out)                 # Q4: our set, our labels
    return {
        "rules_readable": rules.is_tabular() and len(rules) > 0,
        "logs_complete": logs.has_fields("inputs", "versions", "reviewer"),
        "own_test_runs": score is not None,
        "test_set_ours": held_out.owner == "company",          # Q3
        "no_training_on_our_data": vendor.terms.no_training,   # Q6
        "deletion_certificate": vendor.terms.deletion_certified,  # Q7
        "notice_90_days_or_less": vendor.terms.notice_days <= 90,  # Q9
        "model_changes_notified": vendor.terms.notifies_model_change,  # Q10
    }
