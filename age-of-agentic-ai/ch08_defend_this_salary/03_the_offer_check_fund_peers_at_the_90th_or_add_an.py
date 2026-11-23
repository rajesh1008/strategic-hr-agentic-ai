# Strategic HR in the Age of Agentic AI, Chapter 8: Defend This Salary
# Listing: The Offer Check: Fund Peers at the 90th, or Add an Expiry (Under the Hood)

def offer_check(offer, peers, critical: bool) -> dict:
    p75, p90 = peers.percentile(75), peers.percentile(90)
    need_reason = offer.base > p75
    fund_peers = critical and offer.base >= p90
    return {
        "reason_required": need_reason,       # one line, on the offer
        "peer_adjustments": fund_peers,       # same cycle, or no 90th
        "expiry_required": offer.base >= p90 and not critical,
    }
