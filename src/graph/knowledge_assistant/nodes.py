import json
import logging
import ollama

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_ollama import ChatOllama
from qdrant_client.http.models import ScoredPoint

from state import AgentState
from tools import tools
from src.config import get_settings
from src.vector_database.qdrant import client

settings = get_settings()
logger = logging.getLogger(__name__)

def rewrite_query(state: AgentState) -> AgentState:
    """Node for refining the users query"""
    llm_response = ollama.chat(model=settings.OLLAMA_MODEL, messages=[
        {
            "role": "system",
            "content": (
                "You are an expert in refining user queries for RAG systems. "
                "Refine the query the user provides so it is optimized for semantic document retrieval. "
                "Do not change the meaning of the question or the core question itself. "
                "Answer only with the resulting refined query, nothing else."
            ),
        },
        {"role": "user", "content": state['query']},
    ])

    state['query'] = llm_response['message']['content']
    return state


def retrieve_documents(state: AgentState) -> AgentState:
    query_embedding = ollama.embed(model=settings.OLLAMA_EMBEDDING_MODEL, input=state['query'])['embeddings'][0]

    state['retrieved_docs'] = client.query_points(
        collection_name="files",
        query=query_embedding,
        with_payload=True,
        limit=5,
        score_threshold=0.5,
    ).points

    return state


def grade_documents(state: AgentState) -> AgentState:
    """Grade each retrieved document for relevance to the query, filter out irrelevant ones."""
    relevant_docs = []

    for doc in state['retrieved_docs']:
        content = doc.payload.get('content', '')

        response = ollama.chat(model=settings.OLLAMA_MODEL, messages=[
            {
                "role": "system",
                "content": (
                    "You are a relevance grader. Given a user question and a document excerpt, "
                    "decide if the document is relevant to answering the question. "
                    "Reply with only 'yes' or 'no'."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {state['query']}\n\nDocument: {content}",
            },
        ])

        verdict = response['message']['content'].strip().lower()
        if verdict.startswith('yes'):
            relevant_docs.append(doc)

    state['retrieved_docs'] = relevant_docs
    return state


def enrich_documents(state: AgentState) -> dict:
    """LLM reviews graded docs and calls get_document_neighbors for any that appear cut off."""
    llm = ChatOllama(model=settings.OLLAMA_MODEL).bind_tools(tools)

    docs_text = "\n\n".join(
        f"[ID: {doc.id}]\n{doc.payload.get('content', '')}"
        for doc in state['retrieved_docs']
    )

    response = llm.invoke([
        SystemMessage(content=(
            "You are a document completeness checker. "
            "Review the documents below for any that end mid-sentence or mid-thought "
            "— suggesting the answer may continue in a neighboring chunk if so "
            "call get_document_neighbors with that document's ID. If not do not call any tool."
            "If all documents are complete, do not call any tools."
        )),
        HumanMessage(content=docs_text),
    ])

    logger.info(f"enrich_documents: tool_calls={response.tool_calls}")
    return {"messages": [response]}


def should_call_tools(state: AgentState) -> str:
    """Conditional edge: route to ToolNode if the LLM made tool calls, else to merge_neighbors."""
    last = state['messages'][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "merge_neighbors"


def merge_neighbors(state: AgentState) -> AgentState:
    """Parse ToolMessage results and merge neighbor docs into retrieved_docs."""
    existing_ids = {str(doc.id) for doc in state['retrieved_docs']}

    for msg in state['messages']:
        if not isinstance(msg, ToolMessage):
            continue
        try:
            records = json.loads(msg.content)
            for r in records:
                if str(r['id']) not in existing_ids:
                    existing_ids.add(str(r['id']))
                    state['retrieved_docs'].append(
                        ScoredPoint(id=r['id'], payload=r['payload'], score=0.0, version=0)
                    )
        except (json.JSONDecodeError, KeyError):
            logger.warning(f"merge_neighbors: could not parse ToolMessage content: {msg.content}")

    logger.info(f"merge_neighbors: retrieved_docs count = {len(state['retrieved_docs'])}")
    return state


def has_relevant_docs(state: AgentState) -> str:
    """Conditional edge: route based on whether any relevant documents remain after grading."""
    if state['retrieved_docs']:
        return "enrich_documents"
    return "no_docs"


def handle_no_docs(state: AgentState) -> AgentState:
    """Fallback node when no relevant documents are found."""
    state['answer'] = "I don't know — no relevant documents were found for your question."
    return state


def generate_answer(state: AgentState) -> AgentState:
    system_prompt = (
        "You are a helpful assistant. Answer the following question only based on the sources provided. "
        "If the answer is not in the sources, say 'I don't know'. "
        "If the question has nothing to do with the provided sources, say 'I may need to refine the question.' "
        "Do not use any external knowledge, assumptions, or general LLM knowledge."
    )

    human_prompt = f"Question: {state['query']}\n\nContext provided:\n{state['retrieved_docs']}"

    llm_response = ollama.chat(model=settings.OLLAMA_MODEL, messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": human_prompt},
    ])

    state['answer'] = llm_response['message']['content']
    return state
