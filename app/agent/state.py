from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict


class ResearchAgentState(TypedDict):
    """Nodes share this state; messages are appended rather than overwritten."""

    messages: Annotated[list[AnyMessage], add_messages]
    plan: str
    selected_document_ids: NotRequired[list[str]]
