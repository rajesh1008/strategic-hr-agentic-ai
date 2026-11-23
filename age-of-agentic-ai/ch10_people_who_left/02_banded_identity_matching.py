# Strategic HR in the Age of Agentic AI, Chapter 10: People Who Left
# Listing: Banded Identity Matching (Under the Hood)
# Exact name and date of birth recalled 0.13; normalised names 0.28; fuzzy with date of birth 0.82. Before go-live, the sampling rule for auto-matched credits and the accepted residual error are written and signed.

from difflib import SequenceMatcher
import unicodedata

def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return " ".join(sorted(s.lower().replace("-", " ").split()))

def band(carrier_name, carrier_dob, member, auto_at: float, review_at: float):
    """Three bands, never one threshold. Date of birth must agree to auto-match."""
    score = SequenceMatcher(None, norm(carrier_name), norm(member.name)).ratio()
    if score >= auto_at and carrier_dob == member.dob:
        return "auto_match"        # sampled; a false merge has a correction route
    if score >= review_at:
        return "person"
    return "unmatched"             # stays on the open list, never merged
