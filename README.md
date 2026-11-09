# The Strategic HR and Agentic AI Handbook: companion code

Runnable examples, fixtures and evaluation harnesses for the book by Rajesh Ranjan Mahapatra.
**All people data here is synthetic.** No real person, employer or applicant appears in any fixture.

Every code listing in the book comes from a file in this repository, and every model output the book quotes
comes from a captured run in `runs/`. If the book shows it, you can run it.

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
export ANTHROPIC_API_KEY=...        # or put it in .env (ignored by git); never commit it
pytest -q                           # offline tests: no key, no network
pytest -q -m live                   # live tests against the real API
python -m chapters.ch00_sample.shortlist_agent
```

## Layout

| Path | What it holds |
|---|---|
| `hrai/` | Shared library: `llm.py` (the only model client, with run capture), `gate.py` (policy gate), `trail.py` (audit log) |
| `hartwell_gate/policies/` | Hartwell Gate policies as YAML, versioned |
| `fixtures/` | Synthetic data: `hartwell/` and one folder per sector organization |
| `chapters/chNN_slug/` | The examples for one chapter; each module docstring names the book section |
| `runs/chNN/<example>/` | Captured real runs, one JSON per run: request, response, model, usage, git commit |
| `tests/` | Offline unit tests; `-m live` tests call the real API |

Models change. A run record names the exact model and SDK that produced it; re-running may give different
wording. The book quotes the recorded run, not a paraphrase.
