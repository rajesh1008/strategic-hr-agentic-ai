"""Write data/pilot_feb2027.json (seeded, synthetic).

The AskHartwell vendor pilot, January 11 to February 19, 2027:
the chatbot vendor's address-change skill wrote to HartwellOne
through the shared integration user that the nightly benefits
sync also uses. The vendor's log keeps conversation IDs and the
reply; HartwellOne keeps its audit log. Nothing joins them.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

OUT = Path(__file__).parent / "data" / "pilot_feb2027.json"


def build(seed: int = 13) -> dict:
    rnd = random.Random(seed)
    audit, trail = [], []
    n = 5001
    for i in range(41):                 # chatbot conversations
        corr = f"VND-{rnd.randint(100000, 999999)}"
        trail.append({"corr": corr, "step": "request",
                      "actor": "employee"})
        trail.append({"corr": corr, "step": "reply",
                      "actor": "vendor-bot", "said_done": True})
        if i == 17:                     # write failed silently
            continue
        audit.append({"change_id": f"CH-{n}",
                      "field": "home_address",
                      "actor": "svc_hw1_integration",
                      "action_id": None})
        n += 1
    for _ in range(6):                  # nightly benefits sync
        audit.append({"change_id": f"CH-{n}",
                      "field": "home_address",
                      "actor": "svc_hw1_integration",
                      "action_id": None})
        n += 1
    rnd.shuffle(audit)
    return {"_synthetic": "Invented for the book.",
            "agent_identities": ["svc_hw1_integration"],
            "audit": audit, "trail": trail}


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=1) + "\n")
    print(OUT)
