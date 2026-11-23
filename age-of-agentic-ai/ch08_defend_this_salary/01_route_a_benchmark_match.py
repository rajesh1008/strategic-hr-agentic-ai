# Strategic HR in the Age of Agentic AI, Chapter 8: Defend This Salary
# Listing: Route a Benchmark Match (Under the Hood)
# Set the threshold on held-out titles so auto-routed accuracy clears your bar; the company's analyst queue was 15 of 182 jobs.

def route_benchmark(job, rules, embed, threshold: float):
    """A title is never a match on its own; the description travels with it."""
    if not job.description:
        return ("analyst", None, "no description")
    code = rules.match(job.title)
    if code is not None:
        return ("auto", code, "rule")              # 94% right when it answers
    best, score = embed.top(job.title + "\n" + job.description)
    if score >= threshold:
        return ("auto", best, f"embedding {score:.2f}")
    return ("analyst", best, f"below threshold {score:.2f}")
