"""Claim intake: the model drafts ledger entries from a vendor document; the ledger decides.

The model reads one vendor document and proposes one entry per claim through a tool call.
It may suggest a status. The code then applies the ledger's rules: the statement must be
a verbatim quote from the document, a claim with no number is sent back to be restated
as a metric, and every entry enters the ledger as Claimed, whatever the model suggested,
because a vendor document is not evidence for itself.

Run:  python -m chapters.ch04_claim_ledger.claim_intake      (needs ANTHROPIC_API_KEY)
"""
from __future__ import annotations

import re
from pathlib import Path

from hrai.ledger import Claim, Ledger, Status
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
DOCS = {"Takefen": "takefen-roi-slide.md", "RankRight": "crossfield-vendor-onepager.md"}

SYSTEM = (
    "You help an HR team log vendor claims before any of them enters a business case. "
    "Call propose_entry once for every distinct claim in the document. Quote the claim's "
    "words exactly as written. Name the metric it would be measured on, the population and "
    "comparison the document states (or 'not stated'), and up to three questions the buyer "
    "must ask before testing it on their own records."
)
TOOLS = [{
    "name": "propose_entry",
    "description": "Propose one Claim-Status Ledger entry for one claim in the document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "statement": {"type": "string", "description": "exact words from the document"},
            "metric_id": {"type": "string", "description": "snake_case metric name"},
            "value": {"type": ["number", "null"], "description": "the number claimed, or null"},
            "unit": {"type": "string"},
            "population_stated": {"type": "string"},
            "comparison_stated": {"type": "string"},
            "suggested_status": {"type": "string", "enum": [s.label for s in Status]},
            "questions": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        },
        "required": ["statement", "metric_id", "value", "unit", "population_stated",
                     "comparison_stated", "suggested_status", "questions"],
    },
}]


def norm(s: str) -> str:
    return re.sub(r"[\s*_]+", " ", s).strip().lower()


def admit(led: Ledger, vendor: str, doc: str, p: dict, k: int) -> str:
    """Apply the ledger's intake rules to one proposal; return the line to print."""
    quote = p.get("statement", "")
    if norm(quote) not in norm(doc):
        return f"REFUSED  not a verbatim quote: {quote[:50]}"
    if p.get("value") is None:
        return f"RESTATE  no number to test: \"{quote[:56]}\""
    cid = f"{vendor[:2].upper()}-{k:02d}"
    led.register(Claim(claim_id=cid, claimant=vendor, statement=quote,
                       metric_id=p["metric_id"], metric_definition=p["unit"],
                       value=float(p["value"]), unit=p["unit"], source=DOCS[vendor],
                       owner="unassigned"))
    note = ""
    if p.get("suggested_status") != Status.CLAIMED.label:
        note = f" (model suggested {p.get('suggested_status')})"
    return f"{cid}    {p['value']:g} {p['unit'][:24]}: Claimed{note}"


def main() -> None:
    rec = RunRecorder("ch04", "claim_intake")
    for vendor, fname in DOCS.items():
        doc = (HERE / "data/vendor" / fname).read_text()
        doc = re.sub(r"<!--.*?-->", "", doc, flags=re.S).strip()
        resp = rec.create(max_tokens=6000, system=SYSTEM, tools=TOOLS,
                          messages=[{"role": "user", "content": f"Vendor: {vendor}\n\n{doc}"}])
        led = Ledger(f"intake: {vendor}")
        rec.print(f"== {vendor} ({fname})")
        k = 0
        for b in resp.content:
            if b.type != "tool_use":
                continue
            k += 1
            line = admit(led, vendor, doc, b.input, k)
            rec.note(vendor=vendor, proposal=b.input, result=line)
            rec.print("  " + line)
            qs = b.input.get("questions") or []
            if qs and not line.startswith("REFUSED"):
                rec.print(f"           ask: {qs[0]}")
        u = resp.usage
        rec.print(f"  tokens: {u.input_tokens} in, {u.output_tokens} out, {k} proposals")
    print("run record:", rec.save().name)


if __name__ == "__main__":
    main()
