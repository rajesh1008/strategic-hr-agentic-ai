# Strategic HR in the Age of Agentic AI, Chapter 9: The Pay Gap
# Listing: The Reason Gate (Under the Hood)

def gate_reason(note: str, model) -> str:
    label, confidence = model.classify(note)    # objective, non_objective, vague
    if label == "objective" and confidence >= model.pass_threshold:
        return "pass"                           # and joins the quarterly sample
    return "person"
