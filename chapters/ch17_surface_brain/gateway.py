"""Hartwell Gate as a model gateway (book section "Hartwell Gate:
one path to every model").

Every model call names a use from uses.yaml. The gateway checks
the caller, the use's status, the model and the budget; reads
the question with the Chapter 12 paste checker and refuses text
above the use's class; redacts identifiers; makes the call;
meters tokens and cost; and writes one log entry per call that
holds references and counts, never the text. Pausing a use is
the off switch: the next call is refused, whatever the agent's
loop is doing.
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from chapters.ch12_data_readiness import paste_rule

HERE = Path(__file__).resolve().parent
GZIP = {"Accept-Encoding": "gzip, deflate"}
REDACT = {
    "employee ID": (re.compile(r"\bHW-\d{6}\b"), "[EMPLOYEE-ID]"),
    "email": (re.compile(r"\b[\w.]+@[\w.]+\.\w+\b"), "[EMAIL]"),
    "phone": (re.compile(r"\+?\d[\d ]{9,}\d"), "[PHONE]"),
}


class Refused(Exception):
    def __init__(self, code: str, reason: str):
        super().__init__(f"{code}: {reason}")
        self.code, self.reason = code, reason


@dataclass
class Gateway:
    rec: object                      # hrai.llm.RunRecorder
    uses: dict = field(default_factory=dict)
    rates: dict = field(default_factory=dict)
    log: list = field(default_factory=list)

    @classmethod
    def load(cls, rec) -> "Gateway":
        u = yaml.safe_load((HERE / "uses.yaml").read_text())
        r = yaml.safe_load((HERE / "rates.yaml").read_text())
        return cls(rec, {x["id"]: x for x in u["uses"]},
                   r["per_mtok"])

    def pause(self, use: str, by: str) -> None:
        self.uses[use]["status"] = "paused"
        self.log.append({"event": "pause", "use": use, "by": by})

    def spent(self, use: str) -> float:
        return sum(e.get("cost_usd", 0) for e in self.log
                   if e.get("use") == use)

    def cost(self, model: str, tin: int, tout: int) -> float:
        r = self.rates[model]
        return (tin * r["input"] + tout * r["output"]) / 1e6

    def check(self, use: str, caller: str, model: str,
              question: str) -> tuple[dict, str]:
        u = self.uses.get(use)
        if not u:
            raise Refused("G-UNREG", f"no registered use {use}")
        if u["status"] == "paused":
            raise Refused("G-PAUSED", f"{use} is paused")
        if caller not in u["callers"]:
            raise Refused("G-IDENT",
                          f"{caller} may not call {use}")
        if model not in u["models"]:
            raise Refused("G-MODEL", f"{model} not allowed")
        if self.spent(use) >= u["monthly_budget_usd"]:
            raise Refused("G-BUDGET", f"{use} budget reached")
        cls, why = paste_rule.classify(question)
        top = paste_rule.CLASSES.index(u["max_question_class"])
        if paste_rule.CLASSES.index(cls) > top:
            raise Refused("G-CLASS", f"{cls}: {', '.join(why)}")
        return u, cls

    def call(self, *, use: str, caller: str, user_id: str,
             surface: str, question: str, system: str,
             prompt: str, model: str, docs: list[str]):
        entry = {"use": use, "caller": caller, "surface": surface,
                 "user": hashlib.sha256(user_id.encode())
                 .hexdigest()[:10], "model": model, "docs": docs}
        try:
            u, cls = self.check(use, caller, model, question)
        except Refused as r:
            entry.update(status=r.code, reason=r.reason)
            self.log.append(entry)
            raise
        n = 0
        if u["redact"]:
            for pat, tok in REDACT.values():
                prompt, k = pat.subn(tok, prompt)
                n += k
        t0 = time.time()
        resp = self.rec.create(
            model=model, max_tokens=u["max_tokens"], system=system,
            messages=[{"role": "user", "content": prompt}],
            extra_headers=GZIP)
        tin, tout = resp.usage.input_tokens, resp.usage.output_tokens
        entry.update(status="ok", question_class=cls, redactions=n,
                     tokens_in=tin, tokens_out=tout,
                     cost_usd=round(self.cost(model, tin, tout), 6),
                     latency_ms=int((time.time() - t0) * 1000),
                     prompt_sha=hashlib.sha256(prompt.encode())
                     .hexdigest()[:12])
        self.log.append(entry)
        return resp, entry
