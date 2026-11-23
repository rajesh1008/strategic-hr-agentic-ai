# Strategic HR in the Age of Agentic AI, Chapter 4: Seats and People
# Listing: The Reason the CFO Cares About Goes to a Person (Under the Hood)

def route_reason(seat, predicted: str) -> str:
    # the model labelled half of the genuinely unfunded seats as something else
    if not seat.has_budget_line and predicted != "unfunded":
        return "person"
    return predicted
