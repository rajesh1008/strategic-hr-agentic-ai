"""A canary set: fixed cases re-run when anything upstream moves.

Book section: "Drift you can test for". Twenty-four applications
from the Chapter 16 yardstick (their right answers were set by
two senior recruiters), screened with the A04 check in its
"work" configuration. The same cases are run as Takefen used to
present them and as the Northgate parser presents them after
the October 1, 2027 cutover (same facts, different layout:
"07/2022 - Current" for "Jul 2022 to present"). Running the
canary on a second model shows what a model change does.

Run: python -m chapters.ch23_monitoring.canary takefen
     python -m chapters.ch23_monitoring.canary northgate
(needs ANTHROPIC_API_KEY; writes runs/ch23/canary_<format>/)
"""
from __future__ import annotations

import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from hrai.llm import RunRecorder, model

from chapters.ch16_routing.make_data import load
from chapters.ch16_routing.screen import (GZIP, HERE as H16,
                                          JSON_ONLY, NO_THINK,
                                          SYSTEM, parse)

PICK = {"present_near": 4, "sum_near": 3, "overlap": 3,
        "clear_yes": 3, "clear_no": 2, "cert_wording": 2,
        "cert_not_epa": 2, "cert_pending": 2,
        "mixed_roles": 2, "apprentice_military": 1}
MON = {m: i + 1 for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}
ROLE = re.compile(r"^- (.+?), (\w{3}) (\d{4}) to "
                  r"(present|(\w{3}) (\d{4}))$")


def canary() -> list[dict]:
    rng = random.Random(2311)
    rows = load()
    out = []
    for kind, k in PICK.items():
        pool = [r for r in rows if r["kind"] == kind]
        out += rng.sample(pool, k)
    return sorted(out, key=lambda r: r["candidate_id"])


def northgate(resume: str) -> str:
    """Same facts in the Northgate parser's layout."""
    out, certs, sect = [], [], ""
    for line in resume.splitlines():
        m = ROLE.match(line)
        if line in ("Experience", "Certifications and licenses",
                    "Other"):
            sect = line
            if line == "Experience":
                out.append("WORK HISTORY")
            elif line == "Other":
                out.append("Licenses & certifications: "
                           + "; ".join(certs))
                out.append("")
                out.append("ADDITIONAL")
            continue
        if sect == "Certifications and licenses":
            if line.startswith("- "):
                certs.append(line[2:])
            continue
        if m:
            title, rest = m.group(1).split(", ", 1) \
                if ", " in m.group(1) else (m.group(1), "")
            start = f"{MON[m.group(2)]:02d}/{m.group(3)}"
            end = ("Current" if m.group(4) == "present" else
                   f"{MON[m.group(5)]:02d}/{m.group(6)}")
            out.append(f"{title} | {rest} | {start} - {end}")
            continue
        out.append(line)
    return "\n".join(out)


def screen(rec: RunRecorder, system: str, text: str
           ) -> dict | None:
    extra = {"thinking": NO_THINK[model()]} \
        if model() in NO_THINK else {}
    resp = rec.create(max_tokens=3000, system=system + JSON_ONLY,
                      messages=[{"role": "user",
                                 "content": text}],
                      extra_headers=GZIP, **extra)
    return parse("".join(b.text for b in resp.content
                         if b.type == "text"))


def main(fmt: str) -> None:
    system = SYSTEM.format(
        guidance=(H16 / "guidance.md").read_text().strip())
    cases = canary()
    rec = RunRecorder("ch23", f"canary_{fmt}")
    texts = [c["resume"] if fmt == "takefen"
             else northgate(c["resume"]) for c in cases]

    def safe(t: str) -> dict | None:
        try:
            return screen(rec, system, t)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=6) as pool:
        outs = list(pool.map(safe, texts))
    right = 0
    rec.print(f"canary {fmt} on {model()}: {len(cases)} cases")
    for c, o in zip(cases, outs):
        got = None if o is None else o["meets"]
        ok = got == c["meets"]
        right += ok
        months = "?" if o is None else o.get("field_months")
        rec.print(f"  {c['candidate_id']} {c['kind']:<19} "
                  f"truth {'meets' if c['meets'] else 'no':<5} "
                  f"got {str(got):<5} months {months} "
                  f"(truth {c['field_months']})"
                  + ("" if ok else "  WRONG"))
    rec.print(f"right {right} of {len(cases)}")
    rec.note(answers={c["candidate_id"]: o
                      for c, o in zip(cases, outs)})
    print(rec.save())


def compare() -> None:
    """Set the recorded canary runs side by side (no model)."""
    import json
    from hrai.llm import REPO
    truth = {c["candidate_id"]: c for c in canary()}
    rec = RunRecorder("ch23", "canary_compare")
    rec.print("run                          right  months off  "
              "mean conf  out tok")
    for f in sorted((REPO / "runs" / "ch23").glob(
            "canary_[nt]*/*.json")):
        d = json.loads(f.read_text())
        ans = d["events"][0]["answers"]
        right = sum(a is not None and a["meets"] ==
                    truth[k]["meets"] for k, a in ans.items())
        off = [k[4:] for k, a in sorted(ans.items())
               if a and a.get("field_months") !=
               truth[k]["field_months"]]
        conf = [a["confidence"] for a in ans.values() if a]
        out = [c["response"]["usage"]["output_tokens"]
               for c in d["calls"]]
        name = (f"{f.parent.name[7:]} {d['model'][7:-4]} "
                f"{d['run_id'][-7:-1]}")
        rec.print(f"{name:<29}{right:>2}/24  "
                  f"{','.join(off) or '-':<11} "
                  f"{sum(conf) / len(conf):9.3f} "
                  f"{sum(out) / len(out):8.0f}")
    print(rec.save())


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "takefen"
    compare() if arg == "compare" else main(arg)
