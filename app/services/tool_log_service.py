"""Append-only JSONL log for tool invocations."""

import json
from datetime import datetime, timezone
from threading import Lock

from app.core.config import get_settings

_lock = Lock()


def append_tool_log(session_id: str | None, name: str, args: dict, result: str) -> None:
    settings = get_settings()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "name": name,
        "args": args,
        "result": result[:2_000],
    }
    with _lock:
        with settings.tool_logs_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
