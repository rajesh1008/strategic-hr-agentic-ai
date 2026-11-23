# Strategic HR in the Age of Agentic AI, Chapter 5: 46 Days
# Listing: The Only Shortlist Operation the Matcher Has (Under the Hood)
# Opt-in is checked before a name is proposed. Blocked moves are logged, not hidden. Keyword overlap scored 1.0 on templates and 0.41 on hand-written pairs; the small model reached 0.725.

def shortlist(recruiter_names: list[str], matcher_names: list[str],
              opted_in: set[str]) -> list[str]:
    """The matcher may add names. It may never remove one."""
    proposed = [n for n in matcher_names
                if n in opted_in and n not in recruiter_names]
    result = recruiter_names + proposed
    assert set(recruiter_names) <= set(result)     # nothing filtered out
    return result
