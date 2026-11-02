"""The Claim-Status Ledger (Chapter 4), used book-wide.

Every number that could enter a business case, a board pack or a vendor decision gets one
entry. An entry keeps the claim exactly as it was made and, separately, every measurement
taken since. The ledger decides the status from the evidence; nobody types a status in.

Five statuses, in order (MASTER-PROMPT section 7):

    Claimed                     someone said it (vendor, consultancy, press release)
    Demonstrated on vendor data the vendor showed it working on its own or a demo data set
    Tested on our records       we re-ran it on our own records, offline, with a denominator
    Measured in shadow          it ran beside the live process; people still did the work
    Measured in production      it ran live, measured by us, over a stated period

Rules the code enforces:

  1. A measurement counts only if it measures the same metric as the claim (metric_id).
     A time-to-shortlist result cannot promote a screening-time claim.
  2. Each status needs its own evidence fields (who measured, which records, how many, when).
     A measurement missing any of them is refused with a reason, not silently accepted.
  3. Only "measured by" someone other than the claimant can lift a claim past
     Demonstrated on vendor data.
  4. A measurement belongs to one product or model version. When the version in use
     changes, measurements on older versions stop counting (effective_status falls back).
  5. Only Measured in production supports a board number (board_number() returns None
     otherwise). Claimed and Demonstrated values count for zero in the base case.
  6. An independent result that contradicts the claim marks the entry contested; a
     quarantined entry (unverified consultancy or press figure) cannot be promoted at all.

All people data in the book is synthetic. Nothing here calls a model.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Iterable


class Status(IntEnum):
    CLAIMED = 0
    DEMONSTRATED = 1
    TESTED = 2
    SHADOW = 3
    PRODUCTION = 4

    @property
    def label(self) -> str:
        return LABELS[self]

    @property
    def tag(self) -> str:
        """Manuscript tag span, as in 00-plan/design-system.md."""
        word, cls = TAGS[self]
        return f"[{word}]{{.tag .{cls}}}"

    @classmethod
    def parse(cls, text: str) -> "Status":
        t = text.strip().lower()
        for s, lab in LABELS.items():
            if t in (lab.lower(), s.name.lower()):
                return s
        raise ValueError(f"unknown status: {text!r}")


LABELS = {
    Status.CLAIMED: "Claimed",
    Status.DEMONSTRATED: "Demonstrated on vendor data",
    Status.TESTED: "Tested on our records",
    Status.SHADOW: "Measured in shadow",
    Status.PRODUCTION: "Measured in production",
}
TAGS = {
    Status.CLAIMED: ("Claimed", "claimed"),
    Status.DEMONSTRATED: ("Demonstrated", "claimed"),
    Status.TESTED: ("Tested", "tested"),
    Status.SHADOW: ("Shadow", "shadow"),
    Status.PRODUCTION: ("Measured", "measured"),
}

# Evidence each status needs, on top of metric_id, value and version.
REQUIRED = {
    Status.DEMONSTRATED: ("measured_by", "records", "n", "period"),
    Status.TESTED: ("measured_by", "records", "n", "period", "method"),
    Status.SHADOW: ("measured_by", "records", "n", "period", "method", "baseline"),
    Status.PRODUCTION: ("measured_by", "records", "n", "period", "method", "baseline", "owner"),
}

# Share of a measured value the base case may count, by status (rule 5).
BASE_CASE_WEIGHT = {Status.CLAIMED: 0.0, Status.DEMONSTRATED: 0.0, Status.TESTED: 0.0,
                    Status.SHADOW: 0.0, Status.PRODUCTION: 1.0}
# The planning case lets a pilot decision rest on tested or shadow evidence, discounted.
PLANNING_CASE_WEIGHT = {Status.CLAIMED: 0.0, Status.DEMONSTRATED: 0.0, Status.TESTED: 0.5,
                        Status.SHADOW: 0.8, Status.PRODUCTION: 1.0}


class LedgerError(ValueError):
    """A measurement or promotion the ledger refuses, with the reason."""


@dataclass
class Measurement:
    status: str                 # label of the status this measurement is evidence for
    metric_id: str
    value: float
    version: str                # product or model version measured
    measured_by: str = ""
    records: str = ""           # which records: "Hartwell field requisitions, Mar-May 2026"
    n: int = 0                  # denominator: requisitions, applications, tickets, stores
    period: str = ""
    method: str = ""
    baseline: str = ""
    owner: str = ""
    note: str = ""
    evidence_ids: list[str] = field(default_factory=list)   # R-IDs or run ids

    @property
    def level(self) -> Status:
        return Status.parse(self.status)


@dataclass
class Claim:
    claim_id: str
    claimant: str               # who made the claim
    statement: str              # the words as made, quoted
    metric_id: str              # what it measures, e.g. "screening_minutes_per_application"
    metric_definition: str
    value: float                # the claimed value
    unit: str                   # "percent reduction", "hours per month", "share of tickets"
    source: str                 # the document, page or slide; R-ID when public
    owner: str                  # who in our organization is accountable for testing it
    version: str = ""           # product version the claim refers to, when stated
    quarantined: bool = False
    contested: bool = False
    contested_by: str = ""
    measurements: list[Measurement] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)

    # -- evidence -----------------------------------------------------------------------
    def add(self, m: Measurement, on: str = "") -> Status:
        """Attach a measurement if it is admissible; return the new effective status."""
        level = m.level
        if self.quarantined and level > Status.CLAIMED:
            raise LedgerError(f"{self.claim_id} is quarantined: resolve the source before testing it")
        if m.metric_id != self.metric_id:
            raise LedgerError(f"metric mismatch: claim measures {self.metric_id!r}, "
                              f"evidence measures {m.metric_id!r}")
        if level == Status.CLAIMED:
            raise LedgerError("a claim is not evidence for itself")
        missing = [k for k in REQUIRED[level] if not getattr(m, k)]
        if missing:
            raise LedgerError(f"{level.label} needs {', '.join(missing)}")
        if level > Status.DEMONSTRATED and _same_party(m.measured_by, self.claimant):
            raise LedgerError(f"{level.label} must be measured by us, not by {self.claimant}")
        before = self.effective_status(m.version)
        self.measurements.append(m)
        after = self.effective_status(m.version)
        self.history.append({"on": on, "from": before.label, "to": after.label,
                             "value": m.value, "version": m.version, "n": m.n})
        return after

    def contest(self, by: str, on: str = "") -> None:
        self.contested, self.contested_by = True, by
        self.history.append({"on": on, "contested_by": by})

    # -- reading ------------------------------------------------------------------------
    def current(self, version: str | None = None) -> list[Measurement]:
        v = version or self.version
        return [m for m in self.measurements if not v or m.version == v]

    def effective_status(self, version: str | None = None) -> Status:
        ms = self.current(version)
        return max((m.level for m in ms), default=Status.CLAIMED)

    def best(self, version: str | None = None) -> Measurement | None:
        ms = self.current(version)
        if not ms:
            return None
        top = max(m.level for m in ms)
        return [m for m in ms if m.level == top][-1]

    def board_number(self, version: str | None = None) -> float | None:
        """Rule 5: only a production measurement may go in front of a board."""
        b = self.best(version)
        return b.value if b and b.level == Status.PRODUCTION else None

    def case_value(self, case: str = "base", version: str | None = None) -> float:
        weights = BASE_CASE_WEIGHT if case == "base" else PLANNING_CASE_WEIGHT
        b = self.best(version)
        return 0.0 if b is None else b.value * weights[b.level]

    def gap(self, version: str | None = None) -> float | None:
        """Best evidence minus the claim (negative: the claim overstated)."""
        b = self.best(version)
        return None if b is None else round(b.value - self.value, 4)


def _same_party(a: str, b: str) -> bool:
    a, b = a.strip().lower(), b.strip().lower()
    return bool(a) and (a == b or a.startswith(b) or b.startswith(a))


@dataclass
class Ledger:
    organization: str
    claims: dict[str, Claim] = field(default_factory=dict)

    def register(self, claim: Claim) -> Claim:
        if claim.claim_id in self.claims:
            raise LedgerError(f"duplicate claim id {claim.claim_id}")
        claim.history.append({"on": "", "to": Status.CLAIMED.label, "value": claim.value})
        self.claims[claim.claim_id] = claim
        return claim

    def __getitem__(self, cid: str) -> Claim:
        return self.claims[cid]

    def __iter__(self) -> Iterable[Claim]:
        return iter(self.claims.values())

    # -- persistence ----------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {"organization": self.organization, "claims": [asdict(c) for c in self]}

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n")

    @classmethod
    def from_dict(cls, d: dict) -> "Ledger":
        led = cls(d["organization"])
        for c in d["claims"]:
            ms = [Measurement(**m) for m in c.pop("measurements", [])]
            claim = Claim(**c)
            claim.measurements = ms
            led.claims[claim.claim_id] = claim
        return led

    @classmethod
    def load(cls, path: Path) -> "Ledger":
        return cls.from_dict(json.loads(Path(path).read_text()))

    # -- display --------------------------------------------------------------------------
    def rows(self) -> list[dict]:
        out = []
        for c in self:
            b = c.best()
            out.append({"id": c.claim_id, "claimant": c.claimant, "metric": c.metric_id,
                        "claimed": c.value, "best": None if b is None else b.value,
                        "status": c.effective_status().label, "n": 0 if b is None else b.n,
                        "board": c.board_number(),
                        "flags": ",".join(f for f, on in (("contested", c.contested),
                                                          ("quarantined", c.quarantined)) if on)})
        return out

    def table(self) -> str:
        head = f"{'id':<8}{'claimed':>8}{'best':>8}  {'status':<28}{'n':>6}  flags"
        lines = [head]
        for r in self.rows():
            best = "-" if r["best"] is None else f"{r['best']:g}"
            lines.append(f"{r['id']:<8}{r['claimed']:>8g}{best:>8}  {r['status']:<28}"
                         f"{r['n']:>6}  {r['flags']}")
        return "\n".join(lines)
