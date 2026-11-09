"""Chapter 12: what an agent may retrieve, what it may write, and the
record of both.

manifest() turns one planned use in the register into an access
manifest: the fields the agent may read, the fields it may propose
to change, and how. Reader serves only manifest fields and logs
every read, served or refused. Proposals go to a staging list for a
named approver; nothing here writes to the system of record.

Run: HRAI_MODEL=no-model python -m chapters.ch12_data_readiness.access
(writes runs/ch12/access/...)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import readiness


@dataclass
class Manifest:
    use: str
    reads: dict[str, set[str]]
    writes: dict[str, set[str]]
    approver: str


def manifest(use_id: str, reg: dict) -> Manifest:
    u = next(x for x in reg["uses"] if x["id"] == use_id)
    if readiness.verdict(readiness.check_use(u, reg)) == "BLOCKED":
        raise PermissionError(f"{use_id} is BLOCKED in the register")
    src = {s["id"]: s for s in reg["sources"]}
    w = {k: set(v["fields"]) for k, v in u.get("writes", {}).items()}
    return Manifest(use_id, {k: set(v) for k, v in u["reads"].items()},
                    w, src[next(iter(w))]["owner"] if w else "")


@dataclass
class Reader:
    m: Manifest
    log: list[dict] = field(default_factory=list)
    staged: list[dict] = field(default_factory=list)

    def read(self, source: str, fields: list[str],
             rows: list[dict]) -> list[dict]:
        allowed = self.m.reads.get(source, set())
        refused = [f for f in fields if f not in allowed]
        self.log.append({"use": self.m.use, "source": source,
                         "fields": fields, "refused": refused,
                         "rows": 0 if refused else len(rows),
                         "at": datetime.now(timezone.utc).isoformat()})
        if refused:
            raise PermissionError(f"{source}: {refused} not in "
                                  f"the manifest for {self.m.use}")
        return [{f: r.get(f, "") for f in fields} for r in rows]

    def propose(self, source: str, key: str, change: dict,
                why: str) -> dict:
        if not set(change) <= self.m.writes.get(source, set()):
            raise PermissionError(f"{source}: may not propose "
                                  f"{sorted(change)}")
        p = {"use": self.m.use, "source": source, "key": key,
             "change": change, "why": why, "status": "proposed",
             "approver": self.m.approver}
        self.staged.append(p)
        return p


def main() -> None:
    from hrai.llm import RunRecorder
    from . import quality
    reg = readiness.load()
    rec = RunRecorder("ch12", "access")
    m = manifest("U5", reg)
    rec.print(f"Manifest {m.use}: reads "
              + "; ".join(f"{k} {sorted(v)}" for k, v in m.reads.items()))
    rec.print(f"  may propose {sorted(m.writes['D02'])} for "
              f"approval by {m.approver}")
    r = Reader(m)
    cat = quality.rows("job_catalog.csv")
    got = r.read("D02", ["code", "title", "desc"], cat[:40])
    rec.print(f"read D02 code, title, desc: {len(got)} rows served")
    for ask in (["code", "title", "mapped_grade"],
                ["code", "base_pay"]):
        try:
            r.read("D02", ask, cat[:40])
        except PermissionError as e:
            rec.print(f"refused: {e}")
    try:
        manifest("U3", reg)
    except PermissionError as e:
        rec.print(f"refused: {e}")
    r.propose("D02", "UK-B01", {"proposed_grade": "F2"},
              "trade-qualified, works alone")
    applied = sum(p["status"] == "applied" for p in r.staged)
    rec.print(f"staged proposals: {len(r.staged)}, status "
              f"{r.staged[0]['status']}; applied: {applied}")
    rec.print(f"read log entries: {len(r.log)} "
              f"({sum(bool(x['refused']) for x in r.log)} refused)")
    rec.note(read_log=r.log, staged=r.staged)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()
