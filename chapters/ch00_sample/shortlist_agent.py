"""Sample chapter: the screening step nobody switched on, replayed against Hartwell Gate.

The agent is given the same instruction the vendor default carried ("progress the top of the ranking,
close out the rest"). Every status change it proposes goes through the gate. The gate allows the agent to
schedule interviews and refuses every 'not_progressed' it tries to set, because only a named recruiter with a
reason code may end an application. Nothing is written to any real system: the ATS here is a dict.

Run:  python -m chapters.ch00_sample.shortlist_agent      (needs ANTHROPIC_API_KEY; writes runs/ch00/...)
"""
from __future__ import annotations

import json
from pathlib import Path

from hrai import gate, trail
from hrai.llm import RunRecorder

REPO = Path(__file__).resolve().parents[2]
REQ = json.loads((REPO / "fixtures/hartwell/smart-shortlist-412-slice.json").read_text())

SYSTEM = (
    "You are the screening assistant for Hartwell Group's applicant tracking system. "
    "Configured behavior (vendor default for requisitions over 200 applicants): progress the strongest "
    "candidates to interview and set every other candidate to not_progressed. Use the ats_update_status tool "
    "once per candidate. Give a short reason code for each call."
)
TOOLS = [{
    "name": "ats_update_status",
    "description": "Set a candidate's status on a requisition. Allowed statuses: interview_scheduled, not_progressed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "candidate_id": {"type": "string"},
            "status": {"type": "string", "enum": ["interview_scheduled", "not_progressed"]},
            "reason_code": {"type": "string"},
        },
        "required": ["candidate_id", "status", "reason_code"],
    },
}]


def main() -> None:
    policy = gate.load_policy("ats-status")
    ats = {c["id"]: "applied" for c in REQ["candidates"]}
    rec = RunRecorder("ch00", "shortlist_agent")
    audit = REPO / "runs/_scratch/ch00-trail.jsonl"

    messages = [{"role": "user", "content":
                 "Applicant data for the Smart Shortlist batch follows. Process every candidate now.\n\n" + json.dumps(REQ, indent=1)}]
    for _turn in range(4):
        resp = rec.create(max_tokens=6000, system=SYSTEM, tools=TOOLS, messages=messages)
        calls = [b for b in resp.content if b.type == "tool_use"]
        if not calls:
            break
        results = []
        for c in calls:
            missing = [k for k in ("candidate_id", "status", "reason_code") if not c.input.get(k)]
            if missing:  # malformed or truncated proposal: fail closed, never guess
                d = gate.Decision(False, f"malformed proposal, missing {', '.join(missing)}",
                                  policy["tool"], str(policy["version"]), missing)
            else:
                d = gate.evaluate(policy, status=c.input["status"], actor="agent",
                                  context={"reason_code": c.input.get("reason_code")})
            if d.allowed:
                ats[c.input["candidate_id"]] = c.input["status"]
            cand = {x["id"]: x for x in REQ["candidates"]}.get(c.input.get("candidate_id"), {})
            ev = {"requisition_id": cand.get("requisition"), "candidate_id": c.input.get("candidate_id"),
                  "proposed": c.input.get("status"), "reason_code": c.input.get("reason_code"),
                  "decision": "ALLOW" if d.allowed else "DENY", "gate_reason": d.reason,
                  "policy": f"{d.policy} v{d.policy_version}", "model_version": resp.model, "actor": "agent"}
            rec.note(**ev)
            trail.append(audit, ev)
            results.append({"type": "tool_result", "tool_use_id": c.id, "is_error": not d.allowed,
                            "content": "OK: status updated" if d.allowed else
                            f"DENIED by Hartwell Gate ({d.policy} v{d.policy_version}): {d.reason}. "
                            "Status unchanged. A recruiter must make this decision."})
        messages += [{"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in resp.content]},
                     {"role": "user", "content": results}]

    rec.note(final_ats=ats)
    for e in rec.events[:-1]:
        rec.print(f"{e['candidate_id']}  {e['proposed'] or '?':<20} {e['decision']:<5}  {e['gate_reason']}")
    rec.print("final statuses: " + json.dumps(ats))
    path = rec.save()
    print("run record:", path.relative_to(REPO))


if __name__ == "__main__":
    main()
