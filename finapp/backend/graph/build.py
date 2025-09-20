from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import AppState
from .nodes import node_parse, node_extract, node_validate, node_hitl_gate, node_apply_feedback, node_ratios
from ..settings import CHECKPOINT_DB

def build_graph():
    g = StateGraph(AppState)
    g.add_node("parse", node_parse)
    g.add_node("extract", node_extract)
    g.add_node("validate", node_validate)
    g.add_node("hitl", node_hitl_gate)
    g.add_node("apply_feedback", node_apply_feedback)
    g.add_node("ratios", node_ratios)

    g.set_entry_point("parse")
    g.add_edge("parse", "extract")
    g.add_edge("extract", "validate")
    g.add_edge("validate", "hitl")
    g.add_edge("hitl", "ratios")          # si no hay interrupt, sigue
    g.add_edge("apply_feedback", "validate")
    g.add_edge("ratios", END)

    checkpointer = SqliteSaver.from_conn_string(f"sqlite:///{CHECKPOINT_DB}")
    return g.compile(checkpointer=checkpointer)
