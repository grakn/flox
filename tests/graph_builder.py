from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    foo: str
    bar: list[str]

def node_a(state: State) -> State:
    return {"foo": "a", "bar": ["a"]}

def node_b(state: State) -> State:
    return {"foo": "b", "bar": ["b"]}

def build_graph(checkpointer: BaseCheckpointSaver):
    workflow = StateGraph(State)
    workflow.add_node("node_a", node_a)
    workflow.add_node("node_b", node_b)
    workflow.add_edge(START, "node_a")
    workflow.add_edge("node_a", "node_b")
    workflow.add_edge("node_b", END)
    return workflow.compile(checkpointer=checkpointer)
