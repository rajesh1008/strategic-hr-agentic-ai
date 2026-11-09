"""INC-2027-031 replayed: the duplicate bank-detail change.

Book section: "The incident". HartwellOne sends the day's
approved changes to the US payroll provider in one evening
batch. The provider does not honor idempotency keys. A bank
change there *adds* a deposit instruction, and two changes to
one employee within 24 hours trip the provider's own fraud
rule: the new instruction is held and the next pay goes by
paper check until the client confirms.

On Tuesday, November 16, 2027 (synthetic) the provider took
the batch but its reply was lost; the feed job retried the
whole batch. The replay below runs that night twice, once
with the blind retry and once with look-before-retry, and
then runs PR-1, the morning readback that compares HartwellOne
with the provider. No model is called.
"""
from __future__ import annotations

import random
from collections import Counter

from hrai.llm import RunRecorder

SEED = 2023
BATCH = "B-1116-1800"


def changes() -> list[dict]:
    """The 52 approved changes in the evening batch."""
    rng = random.Random(SEED)
    out = []
    for i in range(52):
        emp = f"HW-04{1000 + i * 7}"
        bank = i < 37
        origin = "agent" if (i < 23 or 37 <= i < 46) \
            else "adviser"
        val = (f"Acct ****{rng.randint(1000, 9999)}" if bank
               else f"{rng.randint(10, 999)} Main St")
        out.append({"change_id": f"CH-{9100 + i}", "emp": emp,
                    "field": "bank_account" if bank
                    else "home_address",
                    "value": val, "origin": origin})
    return out


class Provider:
    """US payroll provider (fake): no keys, bank = add."""

    def __init__(self) -> None:
        self.deposit: dict[str, list[dict]] = {}
        self.address: dict[str, str] = {}
        self.records: Counter = Counter()
        self.batches: set[str] = set()
        self.notices = 0

    def apply(self, batch_id: str, batch: list[dict]) -> None:
        self.batches.add(batch_id)
        for c in batch:
            self.records[c["change_id"]] += 1
            if c["field"] == "home_address":
                self.address[c["emp"]] = c["value"]
                continue
            instr = self.deposit.setdefault(c["emp"], [])
            recent = [d for d in instr if d["status"] != "ended"
                      and d.get("new")]
            for d in instr:
                if d["status"] != "ended":
                    d["status"] = "ended"
            status = "held" if recent else "active"
            instr.append({"acct": c["value"], "status": status,
                          "change_id": c["change_id"],
                          "new": True})
            self.notices += 1

    def has_batch(self, batch_id: str) -> bool:
        return batch_id in self.batches


def send(prov: Provider, batch: list[dict], retry: str,
         rec: RunRecorder) -> None:
    """Attempt 1 lands but its reply is lost (the fault)."""
    prov.apply(BATCH, batch)
    rec.print("  attempt 1 18:00 sent; no reply after 120 s")
    if retry == "blind":
        prov.apply(BATCH, batch)
        rec.print("  attempt 2 18:10 sent the whole batch again")
        return
    if prov.has_batch(BATCH):
        rec.print(f"  18:10 lookup {BATCH}: found; not resent")
    else:
        prov.apply(BATCH, batch)
        rec.print("  18:10 lookup: not found; resent once")


def pr1(batch: list[dict], prov: Provider) -> dict:
    """PR-1: read the provider back against HartwellOne."""
    out: dict[str, list] = {"bank_ok": [], "bank_held": [],
                            "addr_ok": [], "addr_bad": [],
                            "addr_dup": []}
    for c in batch:
        if c["field"] == "home_address":
            ok = prov.address.get(c["emp"]) == c["value"]
            dup = prov.records[c["change_id"]] > 1
            out["addr_ok" if ok else "addr_bad"].append(c)
            if dup:
                out["addr_dup"].append(c)
            continue
        live = [d for d in prov.deposit[c["emp"]]
                if d["status"] != "ended"]
        good = (len(live) == 1 and live[0]["status"] == "active"
                and live[0]["acct"] == c["value"])
        out["bank_ok" if good else "bank_held"].append(c)
    return out


def night(retry: str, rec: RunRecorder) -> dict:
    batch = changes()
    prov = Provider()
    n_bank = sum(c["field"] == "bank_account" for c in batch)
    rec.print(f"batch {BATCH}: {len(batch)} changes "
              f"(bank {n_bank}, address {len(batch) - n_bank})")
    send(prov, batch, retry, rec)
    made = sum(len(v) for v in prov.deposit.values())
    held = sum(d["status"] == "held" for v in
               prov.deposit.values() for d in v)
    rec.print(f"  provider: instructions created {made} for "
              f"{n_bank} changes; held {held}; "
              f"change notices {prov.notices}")
    r = pr1(batch, prov)
    rec.print("  PR-1 payroll readback, Wednesday 05:30")
    rec.print(f"    bank     {len(r['bank_ok'])} match, "
              f"{len(r['bank_held'])} held with 2 instructions"
              " for 1 change")
    rec.print(f"    address  {len(r['addr_ok'])} match "
              f"({len(r['addr_dup'])} with 2 change records)")
    return r


def main() -> None:
    rec = RunRecorder("ch23", "feed")
    rec.print("== INC-2027-031 replay: HartwellOne to the US "
              "payroll provider (synthetic)")
    rec.print("-- blind retry (the feed job as built)")
    r = night("blind", rec)
    held = r["bank_held"]
    by = Counter(c["origin"] for c in held)
    rec.print("  held changes by origin of the original change:")
    rec.print(f"    AskHartwell controlled action  {by['agent']}")
    rec.print(f"    keyed by an adviser            "
              f"{by['adviser']}")
    rec.print("  HartwellOne ledger for the agent's 23: 23 done, "
              "1 write each, readback matched")
    rec.print("-- look before retry (the fix)")
    night("lookup", rec)
    rec.note(held=[c["emp"] for c in held])
    print(rec.save())


if __name__ == "__main__":
    main()
