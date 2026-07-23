from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict

SpecialistName = Literal["knowledge", "literature", "web", "learning"]


class MultiAgentState(TypedDict):
    """Shared state for supervisor, specialist agents and final synthesis."""

    messages: Annotated[list[AnyMessage], add_messages]
    selected_document_ids: NotRequired[list[str]]
    routes: list[SpecialistName]
    route_index: int
    routing_reason: str
    plan: str


class SpecialistState(TypedDict):
    """Private state used inside one specialist's tool-calling loop."""

    messages: Annotated[list[AnyMessage], add_messages]
    selected_document_ids: NotRequired[list[str]]
