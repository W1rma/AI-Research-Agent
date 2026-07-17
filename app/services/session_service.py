"""In-memory session history for multi-turn chat."""

from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

_sessions: dict[str, list[BaseMessage]] = {}


def create_session_id() -> str:
    return str(uuid4())


def get_session_messages(session_id: str) -> list[BaseMessage]:
    return list(_sessions.get(session_id, []))


def append_session_messages(session_id: str, messages: list[BaseMessage]) -> None:
    history = _sessions.setdefault(session_id, [])
    history.extend(messages)


def build_request_messages(session_id: str | None, user_message: str) -> tuple[str, list[BaseMessage]]:
    active_session_id = session_id or create_session_id()
    history = get_session_messages(active_session_id)
    messages = [*history, HumanMessage(content=user_message)]
    return active_session_id, messages


def store_turn(session_id: str, user_message: str, answer: str) -> None:
    append_session_messages(
        session_id,
        [HumanMessage(content=user_message), AIMessage(content=answer)],
    )
