# Strategic HR in the Age of Agentic AI, Chapter 15: Month Six
# Listing: The Board Page Builder (Under the Hood)

LABELS = {"worked example", "company figures", "held-out", "observed"}

def board_page(case) -> list[str]:
    for n in case.numbers:
        if n.label not in LABELS:
            raise ValueError(f"{n.name}: a number with no label goes to a person")
        if n.kind == "cash" and n.basis == "annual run-rate" and n.booked:
            raise ValueError(f"{n.name}: an annual base is not booked cash")
    if case.stop_rule_fired and case.decision != "stopped":
        raise ValueError("stop rule fired; the pack cannot restart the case")
    return [case.decision_line, case.label_line, case.cash_line,
            case.capacity_line, case.risk_line, case.stop_line, case.signers_line]
