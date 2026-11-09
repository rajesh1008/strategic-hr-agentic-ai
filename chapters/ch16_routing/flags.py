"""Chapter 16: hard-case flags, computed by code.

Book section "Drawing the routing line". The reliability
table showed that the model's confidence hardly moves
between easy and hard applications. These checks do not
ask the model anything. They read the resume text and the
model's own month count, and flag the shapes of case that
the run got wrong most often. A flagged "meets" answer goes
to a recruiter's full review, whatever its score.
"""
from __future__ import annotations

import re

MON = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}
NOW = 2027 * 12 + 4                       # May 2027
DATES = re.compile(
    r"(\w{3}) (\d{4}) to (?:(\w{3}) (\d{4})|present)")
NONFIELD = re.compile(
    r"parts|dispatch|sales|warehouse associate|customer "
    r"service", re.I)
TRAINING = re.compile(
    r"apprentice|navy|army|military|in progress|booked|"
    r"not yet", re.I)


def spans(text: str) -> list[tuple[int, int]]:
    out = []
    for m in DATES.finditer(text):
        s = int(m.group(2)) * 12 + MON[m.group(1)]
        e = NOW if m.group(3) is None else \
            int(m.group(4)) * 12 + MON[m.group(3)]
        out.append((s, e))
    return out


def flags(resume: str, field_months) -> list[str]:
    """OVERLAP, NEAR, NONFIELD, TRAINING, NO_COUNT."""
    work = resume.split("Certifications")[0]
    sp = spans(work)
    out = set()
    if any(a[0] < b[1] and b[0] < a[1]
           for i, a in enumerate(sp) for b in sp[i + 1:]):
        out.add("OVERLAP")
    total = sum(e - s for s, e in sp)
    try:
        said = int(field_months)
    except (TypeError, ValueError):
        out.add("NO_COUNT")
        said = total
    if 18 <= total <= 30 or 18 <= said <= 30:
        out.add("NEAR")
    if NONFIELD.search(work):
        out.add("NONFIELD")
    if TRAINING.search(resume):
        out.add("TRAINING")
    return sorted(out)
