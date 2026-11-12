from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class SkyAgentState(TypedDict):
    """LangGraph state schema for Sky's dual-agent architecture."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_task: str
    missing_tool_request: Optional[Dict[str, Any]]
    tool_build_attempts: int
    built_tools: List[str]
    last_build_error: Optional[str]
