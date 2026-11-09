"""Chapter 9: the transfer and residency checklist.

For each flow of employee data out of a comparison lane, it
compares what the lane's record needs with what the flow has.
Outcomes: OK, GAP (something needed is missing) and UNCLEAR
(the lane's rules are not complete, so counsel answers). It
never says a transfer is lawful; counsel does. No model.

Run: HRAI_MODEL=no-model python -m \
    chapters.ch09_gulf_asia.transfers
(writes runs/ch09/transfers/...)
"""
from __future__ import annotations

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


def load() -> dict:
    return yaml.safe_load((HERE / "transfers.yaml").read_text())


def assess(flow: dict, lanes: dict) -> tuple[str, list[str]]:
    lane = lanes.get(flow["from"])
    if lane is None:
        return "UNCLEAR", ["no lane record"]
    missing = [n for n in lane["needs"]
               if n not in flow["has"]]
    if missing:
        return "GAP", missing
    if not lane["regs_issued"]:
        return "UNCLEAR", ["regulations not issued"]
    return "OK", []


def main() -> None:
    from hrai.llm import RunRecorder
    d = load()
    rec = RunRecorder("ch09", "transfers")
    rec.print("Hartwell transfer and residency checklist")
    rec.print("(synthetic flows; every lane rule [VERIFY])")
    rec.print("")
    for f in d["flows"]:
        status, why = assess(f, d["lanes"])
        rec.print(f"{f['id']} {status:<7} {f['what']}")
        rec.print(f"   {f['from']} -> {f['to']}; owner "
                  f"{f['owner']}")
        if why:
            rec.print(f"   {', '.join(why)}")
        rec.note(flow=f["id"], status=status, why=why)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
