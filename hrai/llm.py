"""The one model client every example uses.

- The API key comes from the environment (ANTHROPIC_API_KEY) and is never logged, printed or stored.
- The model is pinned here (override with HRAI_MODEL); every run record names the model that answered.
- RunRecorder writes runs/<chapter>/<example>/<UTC timestamp>-<model>.json: the request (system, messages,
  tools, parameters), the raw response content, usage, the git commit and a SHA-256 of the prompt, so a
  chapter can quote real output and a reader can find the exact run.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import anthropic

REPO = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "claude-haiku-5-5"


def model() -> str:
    return os.environ.get("HRAI_MODEL") or DEFAULT_MODEL


def client() -> anthropic.Anthropic:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. Export it or put it in .env (never commit it).")
    return anthropic.Anthropic()  # reads the key from the environment


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def _git_sha() -> str:
    return _git("rev-parse", "--short", "HEAD")


def _git_dirty() -> bool:
    """True if tracked code differs from the commit (runs/ is ignored). Book quotes need dirty == false."""
    out = _git("status", "--porcelain", "--", ".", ":(exclude)runs")
    return bool(out) and out != "unknown"


class RunRecorder:
    def __init__(self, chapter: str, example: str):
        self.chapter, self.example = chapter, example
        self.started = datetime.now(timezone.utc)
        self.calls: list[dict] = []
        self.events: list[dict] = []
        self.stdout: list[str] = []

    def create(self, **request) -> anthropic.types.Message:
        request.setdefault("model", model())
        resp = client().messages.create(**request)
        self.calls.append({
            "request": request,
            "prompt_sha256": hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
            "response": {"id": resp.id, "model": resp.model, "stop_reason": resp.stop_reason,
                         "content": [b.model_dump() for b in resp.content],
                         "usage": resp.usage.model_dump()},
        })
        return resp

    def print(self, line: str = "") -> None:
        """Print and keep the line: the book may quote only what a run actually printed or returned."""
        print(line)
        self.stdout.append(line)

    def note(self, **event) -> None:
        self.events.append(event)

    def save(self) -> Path:
        stamp = self.started.strftime("%Y%m%dT%H%M%SZ")
        used = self.calls[-1]["response"]["model"] if self.calls else model()
        out = REPO / "runs" / self.chapter / self.example / f"{stamp}-{used}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        record = {"run_id": f"{self.chapter}/{self.example}/{stamp}", "started_utc": self.started.isoformat(),
                  "git_commit": _git_sha(), "git_dirty": _git_dirty(), "model": used, "sdk": f"anthropic-python {anthropic.__version__}",
                  "calls": self.calls, "events": self.events, "stdout": self.stdout}
        out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        return out
