"""Chapter 25: Fieldnote and Thorne Kessler (synthetic).

Book sections "Fieldnote: take-home tasks when everyone has
an assistant" and "Thorne Kessler: the assessment center and
the wash-up". Deterministic: rates and an exact test from the
counts in data/sectors.yaml. No model.

Run:  python -m chapters.ch25_interviews.sectors
"""
from __future__ import annotations

from pathlib import Path

import yaml

from chapters.ch07_adverse_impact.impact import fisher_p
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent / "data"


def pct(x: int, n: int) -> str:
    return f"{x}/{n} ({100 * x / n:.0f}%)"


def main() -> None:
    rec = RunRecorder("ch25", "sectors")
    d = yaml.safe_load((HERE / "sectors.yaml").read_text())
    f, b, a = d["fieldnote"], d["fieldnote"]["before"], \
        d["fieldnote"]["after"]
    rec.print(f"== {f['org']}: {f['role']}")
    rec.print(f"completed take-home  2026 "
              f"{pct(b['completed'], b['invited'])}"
              f"  2027 {pct(a['completed'], a['invited'])}")
    rec.print(f"raters within 1 pt   2026 "
              f"{pct(b['pairs_within_one'], b['completed'])}"
              f"  2027 "
              f"{pct(a['pairs_within_one'], a['completed'])}")
    nd = a["completed"] - a["disclosed"]
    p = fisher_p(a["disclosed_passed"], a["disclosed"],
                 a["not_disclosed_passed"], nd)
    rec.print(f"walk-through passed  disclosed AI "
              f"{pct(a['disclosed_passed'], a['disclosed'])}"
              f"  did not {pct(a['not_disclosed_passed'], nd)}"
              f"  p {p:.2f}")
    t = d["thorne_kessler"]
    rec.print(f"== {t['org']}: {t['role']}")
    for y in ("y2026", "y2027"):
        r = t[y]
        rec.print(f"{y[1:]}: attended {r['attended']};"
                  f" adjustments asked"
                  f" {pct(r['adjustments_asked'], r['attended'])}")
        rec.print(f"      wash-up changed {r['washup_changed']}:"
                  f" toward presence {r['toward_presence']},"
                  f" with exercise evidence"
                  f" {r['changed_with_exercise_evidence']}")
    rec.note(fieldnote_p=p)
    rec.save()


if __name__ == "__main__":
    main()
