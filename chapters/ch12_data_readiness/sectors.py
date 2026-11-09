"""Chapter 12: the same register checks on sector cases, and the
Hyderabad validation queue as a quality measure.

Hollis Precision and Calder Bank (synthetic) keep their rows in the
register's shape, so readiness.check_use() runs on them unchanged.
The validation queue at Hartwell's capability center gives a
first-pass return rate per entity. No model is involved.

Run: HRAI_MODEL=no-model python -m chapters.ch12_data_readiness.sectors
(writes runs/ch12/sectors/...)
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

from . import readiness

HERE = Path(__file__).resolve().parent


def main() -> None:
    data = yaml.safe_load((HERE / "sector_registers.yaml").read_text())
    rec = RunRecorder("ch12", "sectors")
    for org in ("hollis", "calder"):
        reg = data[org]
        rec.print(f"{org.title()} register v{reg['version']}, "
                  f"{reg['as_of']}")
        for u in reg["uses"]:
            f = list(dict.fromkeys(readiness.check_use(u, reg)))
            rec.print(f"{u['id']} {readiness.verdict(f)}: {u['name']}")
            for lvl, text in f:
                rec.print(f"   {'B' if lvl == readiness.BLOCK else 'F'}"
                          f"  {text}")
            rec.note(org=org, use=u["id"],
                     verdict=readiness.verdict(f),
                     findings=[t for _, t in f])
    q = data["validation_queue"]
    rec.print(f"Hyderabad validation queue, {q['month']}: "
              "returned for correction")
    tk = tr = 0
    for r in q["rows"]:
        tk, tr = tk + r["keyed"], tr + r["returned"]
        rec.print(f"  {r['entity']}  {r['returned']:>4} of "
                  f"{r['keyed']:>5}  {100 * r['returned'] / r['keyed']:4.1f}%"
                  f"  {r['top']}")
    rec.print(f"  all {tr} of {tk}  {100 * tr / tk:.1f}%")
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
