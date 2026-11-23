# Strategic HR in the Age of Agentic AI, Chapter 2: Twenty-One Ideas
# Listing: The Bound in Three Lines (Under the Hood)

def max_failure_rate(clean_runs: int, confidence: float = 0.95) -> float:
    """Largest failure rate still consistent with zero failures seen."""
    return 1 - (1 - confidence) ** (1 / clean_runs)

[round(max_failure_rate(n), 4) for n in (60, 100, 300, 1000)]
# [0.0487, 0.0295, 0.0099, 0.003]
