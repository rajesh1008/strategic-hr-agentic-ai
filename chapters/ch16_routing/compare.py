"""Chapter 16: one task, several configurations.

Book section "A better configuration is a new line". No
model is called. For each recorded screening run, the
script prints how often the answer was right, how far the
stated confidence sat from that (ECE), the mean confidence
on the answers that were wrong, and the tokens per screen.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch16_routing.compare <run id> [<run id> ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

from hrai import routing as rt
from hrai.llm import REPO, RunRecorder

from .calibrate import EDGES, joined, run_record


def main(run_ids: list[str]) -> None:
    p = RunRecorder("ch16", "compare")
    p.print("run                                model"
            "              right   ECE   wrong at  tokens out")
    for rid in run_ids:
        rec = run_record(rid)
        rows = [r for r in joined(rec)
                if r["said"] is not None and r["conf"] is not None]
        pairs = [(r["conf"], r["said"] == r["meets"])
                 for r in rows]
        wrong = [c for c, ok in pairs if not ok]
        mean_w = f"{sum(wrong) / len(wrong):.2f}" if wrong \
            else "none"
        out = sum(c["response"]["usage"]["output_tokens"]
                  for c in rec["calls"])
        right = sum(ok for _, ok in pairs)
        p.print(f"{rid:<35}{rec['model']:<19}"
                f"{right / len(pairs):.3f}  "
                f"{rt.ece(pairs, EDGES):.3f}  {mean_w:>6}"
                f"   {out / len(rec['calls']):6.0f}")
    path = p.save()
    print(f"saved {Path(path).relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1:])
