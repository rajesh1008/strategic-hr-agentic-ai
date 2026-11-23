# Strategic HR in the Age of Agentic AI, Chapter 12: Year Two
# Listing: Mask Personal Data Before Any Model Call

def mask_for_model(record, allowed_fields):
    # Minimisation: send only the fields this step needs.
    slim = {k: record[k] for k in allowed_fields if k in record}
    # Pseudonymise identifiers before the prompt is built.
    if "employee_id" in slim:
        slim["employee_id"] = hash_id(slim["employee_id"])
    for key in ("health", "ethnicity", "religion"):
        slim.pop(key, None)   # special-category data stays out of prompts
    return slim
