from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from src.graph.state import AgentState
from src.graph.tools import tools
from src.graph.nodes import (
    rewrite_query,
    retrieve_documents,
    grade_documents,
    enrich_documents,
    should_call_tools,
    merge_neighbors,
    generate_answer,
    handle_no_docs,
    has_relevant_docs,
)

workflow = StateGraph(AgentState)

workflow.add_node("rewrite_query", rewrite_query)
workflow.add_node("retrieve_documents", retrieve_documents)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("enrich_documents", enrich_documents)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("merge_neighbors", merge_neighbors)
workflow.add_node("generate_answer", generate_answer)
workflow.add_node("no_docs", handle_no_docs)

workflow.add_edge(START, "rewrite_query")
workflow.add_edge("rewrite_query", "retrieve_documents")
workflow.add_edge("retrieve_documents", "grade_documents")
workflow.add_conditional_edges("grade_documents", has_relevant_docs, ["enrich_documents", "no_docs"])
workflow.add_conditional_edges("enrich_documents", should_call_tools, ["tools", "merge_neighbors"])
workflow.add_edge("tools", "merge_neighbors")
workflow.add_edge("merge_neighbors", "generate_answer")
workflow.add_edge("generate_answer", END)
workflow.add_edge("no_docs", END)

graph = workflow.compile()