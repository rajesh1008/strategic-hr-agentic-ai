"""Append-only audit trail (JSON Lines). One line per proposal and gate decision."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def append(path: Path, event: dict) -> dict:
    event = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **event}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
    return event
