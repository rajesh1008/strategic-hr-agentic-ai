"""Six-view pack check (deterministic).

Book section: "Six views of one system". A view is complete
when the documentation shows every element listed for it.
A system goes to the Build gate (Chapter 22) only with all
six complete.

Run: HRAI_MODEL=no-model python -m \
     chapters.ch13_reference_arch.views
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

VIEWS = {
    "hld": ["users", "external_systems",
            "trust_boundaries", "contracts"],
    "infrastructure": ["identities", "secrets", "tenants",
                       "residency", "queues",
                       "observability", "backup"],
    "lld": ["schemas", "invariants", "versions",
            "error_codes", "timeouts", "idempotency",
            "retries", "approval_expiry"],
    "sequence": ["normal_path", "denied_path",
                 "partial_failure_path"],
    "lineage": ["fields_read", "system_of_record",
                "copies", "model_provider_hop"],
    "recovery": ["off_switch", "reversal", "restore",
                 "rto", "decider"],
}
DATA = Path(__file__).parent / "data" / "views.yaml"


def grade(system: dict) -> dict[str, tuple[str, list]]:
    out = {}
    for v, need in VIEWS.items():
        have = set(system.get(v, []))
        miss = [e for e in need if e not in have]
        mark = "C" if not miss else ("-" if not have else "P")
        out[v] = (mark, miss)
    return out


def main() -> None:
    rec = RunRecorder("ch13", "views")
    total = sum(len(v) for v in VIEWS.values())
    for rv in yaml.safe_load(DATA.read_text())["reviews"]:
        rec.print(f"Architecture review {rv['date']} "
                  f"(synthetic)")
        rec.print("sys  HLD INF LLD SEQ LIN REC  elements  gate")
        for s in rv["systems"]:
            g = grade(s)
            have = total - sum(len(m) for _, m in g.values())
            ready = all(m == "C" for m, _ in g.values())
            marks = "   ".join(m for m, _ in g.values())
            rec.print(f"{s['id']:4}  {marks}    {have:>2}/{total}"
                      f"   {'Build' if ready else 'hold'}")
            rec.note(**{f"{rv['date']} {s['id']}": g})
        rec.print("")
    print(rec.save())


if __name__ == "__main__":
    main()
