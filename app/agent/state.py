from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ResearchAgentState(TypedDict):
    """Nodes share this state; messages are appended rather than overwritten."""

    messages: Annotated[list[AnyMessage], add_messages]
    plan: str
