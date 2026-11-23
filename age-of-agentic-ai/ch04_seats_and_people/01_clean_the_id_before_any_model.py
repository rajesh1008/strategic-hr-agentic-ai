# Strategic HR in the Age of Agentic AI, Chapter 4: Seats and People
# Listing: Clean the ID Before Any Model (Under the Hood)
# Patterns are illustrative; formats in your feed will differ.

import re

def normalise_id(raw) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if s in {"", "NAN", "NONE", "NULL"}:
        return None
    if re.fullmatch(r"\d+\.0+", s):  # 104233.0
        s = s.split(".")[0]
    s = re.sub(r"[\s_\-/]", "", s)   # separators
    s = re.sub(r"^(POS|P)(?=\d)", "", s)
    return s.lstrip("0") or None
