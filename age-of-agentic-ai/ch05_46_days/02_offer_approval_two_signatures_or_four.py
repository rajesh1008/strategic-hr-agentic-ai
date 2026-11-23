# Strategic HR in the Age of Agentic AI, Chapter 5: 46 Days
# Listing: Offer Approval: Two Signatures or Four (Under the Hood)
# Role names are illustrative. Offer approval fell from 5.3 to 3.2 days with no model involved.

def offer_signers(offer, band) -> list[str]:
    """The matrix existed; it was not applied."""
    signers = ["hiring_manager", "recruiting_lead"]
    if offer.base > band.midpoint:
        signers += ["finance_partner", "hr_director"]
    return signers
