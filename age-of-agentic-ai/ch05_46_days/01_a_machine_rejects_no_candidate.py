# Strategic HR in the Age of Agentic AI, Chapter 5: 46 Days
# Listing: A Machine Rejects No Candidate

def review_identity(duplicate_flag, link_score_flag):
    # Detectors are recorded separately; they are not added together.
    if duplicate_flag or link_score_flag:
        return "queue_for_security"   # a person reviews every flag
    return "clear"

def may_go_live(ring_found, ring_total, auto_rejects):
    recall = ring_found / ring_total
    if auto_rejects:
        return "do_not_go_live"
    return "pass" if recall >= 0.75 else "hold"
