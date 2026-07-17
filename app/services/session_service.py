"""SQLite-backed conversation history that survives API restarts."""

import sqlite3
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.core.config import get_settings


class SQLiteSessionStore:
    def __init__(self, path: Path, history_limit: int) -> None:
        self._path = path
        self._history_limit = history_limit
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS session_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('human', 'ai')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_messages_session_id_id "
                "ON session_messages(session_id, id)"
            )

    def get_messages(self, session_id: str) -> list[BaseMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content FROM (
                    SELECT id, role, content FROM session_messages
                    WHERE session_id = ? ORDER BY id DESC LIMIT ?
                ) ORDER BY id ASC
                """,
                (session_id, self._history_limit),
            ).fetchall()
        return [HumanMessage(content=row["content"]) if row["role"] == "human" else AIMessage(content=row["content"]) for row in rows]

    def append_turn(self, session_id: str, user_message: str, answer: str) -> None:
        with self._connect() as connection:
            connection.executemany(
                "INSERT INTO session_messages(session_id, role, content) VALUES (?, ?, ?)",
                [(session_id, "human", user_message), (session_id, "ai", answer)],
            )


@lru_cache
def get_session_store() -> SQLiteSessionStore:
    settings = get_settings()
    return SQLiteSessionStore(settings.sessions_db_path, settings.session_history_limit)


def create_session_id() -> str:
    return str(uuid4())


def build_request_messages(session_id: str | None, user_message: str) -> tuple[str, list[BaseMessage]]:
    active_session_id = session_id or create_session_id()
    history = get_session_store().get_messages(active_session_id)
    return active_session_id, [*history, HumanMessage(content=user_message)]


def store_turn(session_id: str, user_message: str, answer: str) -> None:
    get_session_store().append_turn(session_id, user_message, answer)
