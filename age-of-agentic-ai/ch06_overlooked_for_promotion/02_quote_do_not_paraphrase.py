# Strategic HR in the Age of Agentic AI, Chapter 6: Overlooked for Promotion
# Listing: Quote, Do Not Paraphrase (Under the Hood)
# Exact substring match is strict on purpose. Source ids map to goals, feedback and self-nomination records; the POSH prefix marks records that must never appear.

import re

def packet_problems(packet_sentences, sources: dict[str, str]) -> list[str]:
    """Every sentence in a packet must be a verbatim quote with a source id."""
    problems = []
    for s in packet_sentences:
        m = re.fullmatch(r'"(.+)" \[(\w+)\]', s.strip())
        if not m:
            problems.append(f"not a cited quote: {s[:40]}")
        elif m.group(2) not in sources:
            problems.append(f"unknown source {m.group(2)}")
        elif m.group(1) not in sources[m.group(2)]:
            problems.append(f"quote not found in {m.group(2)}")
        elif sources[m.group(2)].startswith("POSH:"):
            problems.append("Internal Committee record: barred from packets")
    return problems        # any problem blocks the packet from the panel
