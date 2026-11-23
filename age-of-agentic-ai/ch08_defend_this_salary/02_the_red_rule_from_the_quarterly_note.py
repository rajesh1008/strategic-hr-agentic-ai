# Strategic HR in the Age of Agentic AI, Chapter 8: Defend This Salary
# Listing: The Red Rule From the Quarterly Note (Under the Hood)
# The 5% and two-quarter test is the one the note applies to the sales manager role. Amber and green thresholds are reward's to set; they are not in the source.

def skill_status(lag_by_quarter: list[float], pay_cited_share: float,
                 red_lag: float = 0.05) -> str:
    """Red when the range lags the market by more than red_lag for two
    quarters running and pay is a stated reason in declines."""
    last_two = lag_by_quarter[-2:]
    if (len(last_two) == 2 and all(l > red_lag for l in last_two)
            and pay_cited_share > 0):
        return "red"         # hiring-zone rule until the April build
    return "review"          # amber and green bands set by reward
