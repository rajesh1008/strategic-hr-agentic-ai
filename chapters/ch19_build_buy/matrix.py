"""Chapter 19: the build, buy or configure matrix.

Book section "Configure, buy or build: the matrix". One row
per component, six yes/no questions answered from records
(data/options.yaml), and an ordered rule that places each
row. The order is the argument: use what you already own,
build only what is yours and differentiates, buy what is
common, and otherwise redesign before automating.

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch19_build_buy.matrix
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder

HERE = Path(__file__).resolve().parent


def place(a: dict) -> tuple[str, str]:
    y = {q: v == "Y" for q, v in a.items()}
    if y["Q3"]:
        return "CONFIGURE", "a system we own does it"
    if y["Q1"] and y["Q2"] and y["Q5"]:
        return "BUILD", "ours, differentiating, owned"
    if y["Q4"]:
        return "BUY", "common, and the market passes"
    if y["Q2"] and y["Q5"]:
        return "BUILD", "narrow: nobody sells it"
    return "REDESIGN", "back to the canvas first"


def tco(t: dict, years: int = 3) -> int:
    return t["one_off"] + years * sum(t["yearly"].values())


def main() -> None:
    cfg = yaml.safe_load((HERE / "data" / "options.yaml")
                         .read_text())
    rec = RunRecorder("ch19", "matrix")
    counts: dict = {}
    for cid, c in cfg["components"].items():
        verdict, why = place(c["answers"])
        extra = ""
        if verdict == "BUILD" and c["answers"]["Q6"] == "Y":
            extra = " + provider duties"
        counts[verdict] = counts.get(verdict, 0) + 1
        rec.print(f"{cid} {verdict:<9} {c['name']}")
        rec.print(f"    {why}{extra}; {c['owner']}")
    rec.print("placed: " + ", ".join(
        f"{k} {v}" for k, v in sorted(counts.items())))
    rec.print("three-year cost, US$ thousands (illustrative):")
    for k, t in cfg["tco"].items():
        rec.print(f"  {k:<15} {tco(t):>6}")
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
