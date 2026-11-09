"""The provider desk's cluster rule (Quayfen, synthetic).

Book section: "Quayfen's tier 1: the first to hear". Advisers
answer one call at a time, so a pattern across calls is
nobody's job unless a rule makes it one. The rule: three calls
for one client in one category within 60 minutes pages the
team lead, who may request a stop under the contract. The
module replays the incident night and 60 ordinary nights
(seeded) to show when the rule would have fired and how often
it fires when nothing is wrong. No model is called.
"""
from __future__ import annotations

import random
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).resolve().parent / "data"
RULE_N, RULE_MIN = 3, 60


def minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def fires(times: list[int]) -> int | None:
    """Minute of the call that completes the first cluster."""
    t = sorted(times)
    for i in range(RULE_N - 1, len(t)):
        if t[i] - t[i - RULE_N + 1] <= RULE_MIN:
            return t[i]
    return None


def ordinary_nights(n: int = 60, seed: int = 23) -> list[list]:
    """BANK_QUERY calls 18:00 to 06:00 on ordinary nights."""
    rng = random.Random(seed)
    nights = []
    for _ in range(n):
        k = sum(rng.random() < 0.04 for _ in range(60))
        nights.append([18 * 60 + rng.randint(0, 719)
                       for _ in range(k)])
    return nights


def main() -> None:
    rec = RunRecorder("ch23", "quayfen")
    log = yaml.safe_load((DATA / "quayfen_calls.yaml").read_text())
    t = [minutes(x) for x in log["calls"]]
    hit = fires(t)
    rec.print(f"== {log['client']} {log['category']}, night of "
              f"{log['night']}: {len(t)} calls")
    rec.print(f"  rule: {RULE_N} calls in {RULE_MIN} min pages "
              "the team lead")
    rec.print(f"  rule fires at {hit // 60:02d}:{hit % 60:02d}"
              f" (call {sorted(t).index(hit) + 1})")
    rec.print("  readback detection at 05:42; rule would have "
              f"been {(24 * 60 + 5 * 60 + 42 - hit) // 60} h "
              f"{(24 * 60 + 5 * 60 + 42 - hit) % 60:02d} min "
              "earlier")
    nights = ordinary_nights()
    per = [len(n) for n in nights]
    false = sum(fires(n) is not None for n in nights)
    rec.print(f"== 60 ordinary nights (seeded): BANK_QUERY calls "
              f"per night mean {sum(per) / len(per):.1f}, "
              f"max {max(per)}")
    rec.print(f"  rule fires on {false} of 60 nights")
    print(rec.save())


if __name__ == "__main__":
    main()
