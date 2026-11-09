"""Chapter 30: the case file and the evidence chain.

Book section "The case file and the evidence chain". One
synthetic case, ER-2027-0907 (Hartwell UK, Leeds), loaded
from data/. Every item in a case file has an ID, a source,
the person who collected it, a date and a fingerprint. An
agent may cite only items in the chain, and every quote it
gives must appear word for word in the item it cites.

  chain_checks  CH-1 to CH-6 over a case folder
  manifest      fingerprints written when an item is added
  by_date       the evidence table for the 11 call-outs,
                built by code from the records (no model)
  quote_ok      is a quote verbatim in the item it cites?
                (an ellipsis may join verbatim parts, in order)

  CH-1  the item has an ID, a kind and a source
  CH-2  a named person collected it (not "automatic")
  CH-3  the date it was collected is recorded
  CH-4  statements and interview notes are signed
  CH-5  its fingerprint is in the manifest and matches
  CH-6  an HR-record item carries the reason a person
        added it to this case

Run:  HRAI_MODEL=no-model python -m \\
        chapters.ch30_relations.case
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).parent / "data"
SIGNED = {"statement", "interview_notes"}


def load(name: str = "er_2027_0907") -> dict:
    return yaml.safe_load((DATA / f"{name}.yaml").read_text())


def norm(s: str) -> str:
    s = s.replace("\u2019", "'").replace("\u201c", '"')
    s = s.replace("\u201d", '"')
    return " ".join(s.split()).lower()


def fingerprint(item: dict) -> str:
    raw = "|".join([item["id"], item["source"], item["text"]])
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def quote_ok(items: dict, item_id: str, quote: str) -> bool:
    it = items.get(item_id)
    if not it:
        return False
    src = norm(it["text"])
    parts = [norm(p).strip(" .\"'")
             for p in re.split(r"\.\.\.|\u2026", quote)]
    parts = [p for p in parts if p]
    pos = 0
    for p in parts:
        pos = src.find(p, pos)
        if pos < 0:
            return False
        pos += len(p)
    return bool(parts)


def chain_checks(folder: list[dict],
                 manifest: dict | None) -> dict:
    out = {}
    for it in folder:
        bad = []
        if not all(it.get(k) for k in ("id", "kind",
                                       "source")):
            bad.append("CH-1")
        who = str(it.get("collected_by", ""))
        if not who or "automatic" in who or "suite" in who:
            bad.append("CH-2")
        if not it.get("collected_on"):
            bad.append("CH-3")
        if it["kind"] in SIGNED and not it.get("signed"):
            bad.append("CH-4")
        fp = (manifest or {}).get(it["id"])
        if fp != fingerprint(it):
            bad.append("CH-5")
        if not it.get("reason") and it["kind"] == "hr_record":
            bad.append("CH-6")
        out[it["id"]] = bad
    return out


def write_manifest(folder: list[dict], path: Path) -> dict:
    man = {it["id"]: fingerprint(it) for it in folder}
    path.write_text(yaml.safe_dump(man, sort_keys=True))
    return man


def in_window(day: date, case: dict) -> bool:
    f = case["gate3_fault"]
    start = datetime.fromisoformat(str(f["opened"])).date()
    end = datetime.fromisoformat(str(f["closed"])).date()
    return start <= day <= end


def by_date(case: dict) -> list[dict]:
    book = {str(d) for d in case["signin_book"]}
    duty = {str(d) for d in case["duty_manager_nights"]}
    acct = {str(k): v for k, v in
            case["account_by_date"].items()}
    seen = {str(k): v for k, v in
            case["witness_by_date"].items()}
    rows = []
    for c in case["callouts"]:
        d = c["date"]
        key = str(d)
        fault = in_window(d, case)
        rows.append({
            "date": key, "ref": c["ref"],
            "reader": "offline" if fault else "online",
            "entry": "none",
            "book": "yes" if key in book else "no",
            "duty_mgr": "on" if key in duty else "off",
            "account": acct.get(key) or (
                acct["fault_window"] if fault else "?"),
            "witness": seen.get(key, "")})
    return rows


def folder_v1(case: dict) -> tuple[list[dict], list[str]]:
    """The chain after review: HR-record items leave the chain
    unless a person adds them with a reason."""
    keep = [it for it in case["items"]
            if it["kind"] != "hr_record" or it.get("reason")]
    out = [it["id"] for it in case["items"] if it not in keep]
    return keep, out


def main() -> None:
    rec = RunRecorder("ch30", "chain")
    case = load()
    items = case["items"]
    rec.print(f"== {case['case']}: folder as the HR suite held"
              f" it ({len(items)} items, no manifest)")
    v0 = chain_checks(items, None)
    for it in items:
        rec.print(f"  {it['id']}  {it['kind']:<15}"
                  f" {' '.join(v0[it['id']]) or 'ok'}")
    n0 = sum(len(v) for v in v0.values())
    rec.print(f"  problems: {n0}")
    keep, out = folder_v1(case)
    man_path = DATA / "er_2027_0907_manifest.yaml"
    man = yaml.safe_load(man_path.read_text())
    v1 = chain_checks(keep, man)
    n1 = sum(len(v) for v in v1.values())
    rec.print(f"== chain v1: {len(keep)} items, manifest"
              f" checked; outside the chain: {', '.join(out)}")
    rec.print(f"  problems: {n1}")
    edited = [dict(it) for it in keep]
    for it in edited:
        if it["id"] == "E05":
            it["text"] = it["text"].replace(
                "the 17th I think", "the 17th and the 19th")
    bad = {k: v for k, v in chain_checks(edited, man).items()
           if v}
    rec.print(f"== one word changed in E05 after collection:"
              f" {bad}")
    rec.print("== evidence by date (code: E02, E03, E06,"
              " E07, E08; account coded from E04)")
    rec.print("  date        reader   entry book duty  account")
    rows = by_date(case)
    for r in rows:
        rec.print(f"  {r['date']}  {r['reader']:<8} {r['entry']:<5}"
                  f" {r['book']:<4} {r['duty_mgr']:<4}"
                  f"  {r['account']}")
    off = sum(r["reader"] == "offline" for r in rows)
    bk = sum(r["book"] == "yes" for r in rows)
    rec.print(f"  reader offline on {off} of {len(rows)} dates;"
              f" sign-in book on {bk}; neither on"
              f" {len(rows) - off - bk}")
    rec.save()


if __name__ == "__main__":
    import sys
    if "--manifest" in sys.argv:
        c = load()
        write_manifest(folder_v1(c)[0],
                       DATA / "er_2027_0907_manifest.yaml")
    else:
        main()
