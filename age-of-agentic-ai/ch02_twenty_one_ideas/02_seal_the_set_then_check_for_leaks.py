# Strategic HR in the Age of Agentic AI, Chapter 2: Twenty-One Ideas
# Listing: Seal the Set, Then Check for Leaks (Under the Hood)
# Exact-match leakage is the floor, not the ceiling. Near-duplicates, paraphrases of tuning items, also disqualify an item; a reviewer reads the closest pairs.

import hashlib, json

def seal(items: list[dict]) -> str:
    """Freeze the hand-written set: any later edit changes the hash."""
    blob = json.dumps(sorted(items, key=lambda i: i["id"]), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()

def leakage(test: list[dict], tuning: list[dict], builders: set[str]) -> list[str]:
    seen = {i["text"].strip().lower() for i in tuning}
    problems = []
    for item in test:
        if item["author"] in builders:
            problems.append(f'{item["id"]}: written by a builder')
        if item["text"].strip().lower() in seen:
            problems.append(f'{item["id"]}: also in the tuning set')
    return problems             # must be empty before the run counts
