"""The controlled-action catalog and its eight checks.

Book section: "The controlled-action catalog". One row per
action the service agent may take, per group of
jurisdictions. Chapter 14's approval matrix says how one
action is approved; the catalog says which actions exist at
all, where, at which mode, and what proves and undoes them.
A row is live only when it passes all eight checks:

  CAT-1 Line    a Line row, and the mode is at or below its
                ceiling
  CAT-2 approver a rule or a named role, never the agent or
                the requester; pay rows use the payroll team
                that owns that country's payroll
  CAT-3 readback a readback for every write
  CAT-4 reversal a reversal route (a correction for a letter)
  CAT-5 validate a validator for every jurisdiction listed
  CAT-6 language a template in every language the
                jurisdiction requires
  CAT-7 owner   a named owner
  CAT-8 failure a failure queue that can read and fix the
                record (never tier 1 alone)

Run: HRAI_MODEL=no-model python -m chapters.ch26_service.catalog
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).parent / "data"
MODES = ["retrieve", "recommend", "act_with_approval", "act"]
VALID = {
    "us_zip": re.compile(r",\s*[A-Z]{2}\s+\d{5}(-\d{4})?$"),
    "ca_postal": re.compile(
        r",\s*(AB|BC|MB|NB|NL|NS|NT|NU|ON|PE|QC|SK|YT)\s+"
        r"[A-Z]\d[A-Z]\s?\d[A-Z]\d$"),
    "uk_postcode": re.compile(
        r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$"),
}
TIER1 = "Quayfen tier 1"
PAY = {"bank_detail_change"}
NEEDS_VALIDATOR = {"address_change"}


def check(row: dict, juris: dict) -> list[str]:
    bad = []
    line = row.get("line") or {}
    if not line.get("row") or MODES.index(row["mode"]) \
            > MODES.index(line.get("ceiling", "retrieve")):
        bad.append("CAT-1")
    appr = row.get("approver")
    pay_ok = all(juris[j]["payroll"] == appr
                 for j in row["where"]) \
        if row["action"] in PAY else True
    if appr in (None, "agent", "requester") or not pay_ok:
        bad.append("CAT-2")
    if row.get("readback") in (None, "none"):
        bad.append("CAT-3")
    if row.get("reversal") in (None, "none"):
        bad.append("CAT-4")
    if row["action"] in NEEDS_VALIDATOR and any(
            juris[j]["validator"] not in row.get("validators", [])
            for j in row["where"]):
        bad.append("CAT-5")
    if any(set(juris[j]["languages"]) - set(row["templates"])
           for j in row["where"]):
        bad.append("CAT-6")
    if not row.get("owner"):
        bad.append("CAT-7")
    if row.get("failure_queue") in (None, TIER1):
        bad.append("CAT-8")
    return bad


def show(rec, version: str) -> int:
    cat = yaml.safe_load(
        (DATA / f"catalog_v{version}.yaml").read_text())
    rec.print(f"== catalog v{cat['version']}:"
              f" {len(cat['actions'])} rows,"
              f" {len(cat['refused'])} refused actions")
    problems = 0
    for row in cat["actions"]:
        bad = check(row, cat["jurisdictions"])
        problems += len(bad)
        where = ",".join(row["where"])
        rec.print(f"  {row['id']:<14} {row['mode']:<18}"
                  f" {where:<16} "
                  + (" ".join(bad) if bad else "live"))
    rec.print(f"  problems: {problems}")
    return problems


ADDRESSES = {   # synthetic employees and addresses
    "HW-012771": "3315 Tejon Street, Denver, CO 80211",
    "HW-040217": "112 Signal Road, Fort McMurray, AB T9H 4N6",
    "HW-041388": "4521 rue Saint-Denis, Montréal, QC H2J 2L3",
    "HW-031244": "9 Canal Row, Manchester M4 6AB",
}


def addresses(rec) -> None:
    """The live US lifecycle on four countries' addresses."""
    from chapters.ch14_controlled_actions.actions import (
        Lifecycle)
    from chapters.ch14_controlled_actions.fakes import (
        Clock, HartwellOne)
    seed = {e: {"name": e, "home_address": "old",
                "bank_account": "-", "phone_on_file": "-"}
            for e in ADDRESSES}
    lc = Lifecycle(HartwellOne(seed=seed),
                   Clock("2027-12-06T09:00"))
    rec.print("== address change through the live US matrix v2")
    for emp, addr in ADDRESSES.items():
        a = lc.propose(emp, "home_address", addr, emp)
        rec.print(f"  {emp} {a.state:<7} {a.reason or ''}")
    rec.print("== the same addresses through catalog v1"
              " validators")
    for emp, addr in ADDRESSES.items():
        ok = [k for k, rx in VALID.items() if rx.search(addr)]
        rec.print(f"  {emp} " + (", ".join(ok) or "none"))


def main() -> None:
    rec = RunRecorder("ch26", "catalog")
    addresses(rec)
    for v in ("0", "1"):
        show(rec, v)
    print(rec.save())


if __name__ == "__main__":
    main()
