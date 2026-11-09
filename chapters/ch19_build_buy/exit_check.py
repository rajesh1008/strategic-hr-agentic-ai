"""Chapter 19: the exit test, run before the exit.

Book section "Leaving Takefen". Lists what Hartwell must
be able to keep after a vendor leaves, and checks what the
vendor's termination export actually delivered in a test
run (data/takefen_export.yaml). Run it during due diligence
on every vendor, not in the last month of the contract.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch19_build_buy.exit_check
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder

HERE = Path(__file__).resolve().parent


def main() -> None:
    cfg = yaml.safe_load((HERE / "data" / "takefen_export.yaml")
                         .read_text())
    rec = RunRecorder("ch19", "exit_check")
    tally: dict = {}
    for item, need in cfg["required"].items():
        got = cfg["delivered"].get(item, {"status": "none"})
        st = got["status"]
        tally[st] = tally.get(st, 0) + 1
        n = f" {got['records']:,}" if "records" in got else ""
        note = f" ({got['note']})" if "note" in got else ""
        rec.print(f"{item:<19}{st:<9}{n}{note}")
        if st != "complete":
            rec.print(f"{'':<19}needed for: {need['why']}")
    rec.print(f"required {len(cfg['required'])}: " + ", ".join(
        f"{k} {v}" for k, v in sorted(tally.items())))
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
