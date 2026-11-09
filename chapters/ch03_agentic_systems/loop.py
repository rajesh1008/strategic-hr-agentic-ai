"""A minimal agent loop: model, instructions, tools, memory,
loop and stop conditions, in one short file.

Book section: "The loop and its stop conditions". The model
only ever proposes a tool call. This code decides whether to
run it (each tool's handler), keeps the conversation (the
agent's short-term memory) and stops the loop on the first
stop condition that fires. Every call is recorded.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from hrai.llm import RunRecorder

# The box's Brotli build cannot decode streamed replies, so
# ask for gzip. Transport only; the request is unchanged.
GZIP = {"Accept-Encoding": "gzip, deflate"}


@dataclass
class Budget:
    max_turns: int = 6          # model calls per task
    max_tool_calls: int = 8     # tool calls per task
    max_output_tokens: int = 8000


@dataclass
class Tool:
    name: str
    kind: str                   # read | write | route
    description: str
    schema: dict
    handler: Callable[[dict], "Result"]

    def spec(self) -> dict:
        return {"name": self.name,
                "description": self.description,
                "input_schema": self.schema}


@dataclass
class Result:
    text: str                   # what the model is told
    error: bool = False
    stop: str | None = None     # set to end the loop


@dataclass
class Outcome:
    stop_reason: str
    turns: int
    calls: list[dict] = field(default_factory=list)
    final_text: str = ""


def args_of(raw) -> dict:
    """Tool input as sent. A JSON string is parsed; anything
    that is not an object becomes {} (handlers deny it)."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    return raw if isinstance(raw, dict) else {}


def run(rec: RunRecorder, system: str, tools: list[Tool],
        ask: str, budget: Budget = Budget()) -> Outcome:
    by_name = {t.name: t for t in tools}
    memory = [{"role": "user", "content": ask}]
    out, spent = Outcome("running", 0), 0
    while True:
        if out.turns >= budget.max_turns:
            out.stop_reason = "budget: turns"
            return out
        resp = rec.create(
            max_tokens=4000, system=system, messages=memory,
            tools=[t.spec() for t in tools],
            extra_headers=GZIP)
        out.turns += 1
        spent += resp.usage.output_tokens
        memory.append({"role": "assistant", "content": [
            b.model_dump(exclude_none=True)
            for b in resp.content]})
        asks = [b for b in resp.content
                if b.type == "tool_use"]
        out.final_text = " ".join(
            b.text for b in resp.content if b.type == "text")
        if not asks:
            out.stop_reason = "answered"
            return out
        results, stop = [], None
        for a in asks:
            if len(out.calls) >= budget.max_tool_calls:
                r = Result("Not run: tool budget used up.",
                           error=True, stop="budget: tools")
            elif a.name not in by_name:
                r = Result(f"Unknown tool {a.name}.", True)
            else:
                r = by_name[a.name].handler(args_of(a.input))
            out.calls.append({"tool": a.name,
                              "input": args_of(a.input),
                              "result": r.text,
                              "error": r.error})
            results.append({"type": "tool_result",
                            "tool_use_id": a.id,
                            "content": r.text,
                            "is_error": r.error})
            stop = stop or r.stop
        memory.append({"role": "user", "content": results})
        if stop:
            out.stop_reason = stop
            return out
        if spent >= budget.max_output_tokens:
            out.stop_reason = "budget: tokens"
            return out
