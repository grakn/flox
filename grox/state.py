from typing import TypedDict, List, Tuple, Union, Annotated
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
import operator

class GroxState(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    agent_sctratchpad: Annotated[List[Tuple[AgentAction, str]], operator.add]
