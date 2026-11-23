# Strategic HR in the Age of Agentic AI, Chapter 14: The Audit
# Listing: Floors in Code, Duties to a Person (Under the Hood)
# Floors as at 23 November 2026. The $684 weekly figure is the 2019 floor, republished after the 2024 rule was vacated. The 1.5B model read every non-exempt job as exempt, which is why model size is a release condition.

from decimal import Decimal

FLOORS = {                                  # annual salary floors, 2026
    "federal": Decimal("35568"),            # $684 a week, 29 CFR 541.600
    "CA": Decimal("16.90") * 2 * 40 * 52,   # twice minimum wage: 70304
}
HCE_TOTAL = Decimal("107432")               # highly compensated, federal

def below_floor(annual_salary: Decimal, state: str) -> bool:
    floor = max(FLOORS["federal"], FLOORS.get(state, Decimal(0)))
    return annual_salary < floor              # NY, CO and others load each January

def route_duties(summary: str, reader) -> str:
    test, confidence = reader.classify(summary)    # executive, administrative, ...
    if test == "non_exempt":
        return "person: likely non-exempt"
    return "person: confirm the exemption"          # the reader never sets status
