# Strategic HR in the Age of Agentic AI, Chapter 11: Wrong Pay
# Listing: The Rule That Recomputes Every Line

def must_review(row, history):
    if row.bank_changed_within_days <= 5:
        return "mandatory"          # bank-detail change
    if row.is_leaver and row.still_on_the_run:
        return "mandatory"          # leaver still being paid
    if row.amount > 3 * history.twelve_month_average:
        return "mandatory"          # more than 3x the 12-month average
    return "ranked_by_gap"

def build_queue(rows, history, budget=40):
    mandatory = [r for r in rows if must_review(r, history) == "mandatory"]
    remaining = [r for r in rows if r not in mandatory]
    remaining.sort(key=lambda r: r.gap, reverse=True)
    return (mandatory + remaining)[:budget]   # 11 mandatory + 29 by gap, in the worked close
