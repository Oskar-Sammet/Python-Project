import ollama

from src.graph.state import AgentState
from src.config import get_settings
from src.vector_database.qdrant import client

settings = get_settings()

def rewrite_query(state: AgentState) -> AgentState:
    """Node for refining the users query"""
    llm_response = ollama.chat(model=settings.OLLAMA_MODEL, messages=[
        {
            "role": "system",
            "content": (
                "You are an expert in refining user queries for RAG systems. "
                "Refine the query the user provides so it is optimized for semantic document retrieval. "
                "Answer only with the resulting refined query, nothing else."
            ),
        },
        { "role": "user", "content": state['query'] },
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
        score_threshold=0.5
    ).points

    return state

def grade_documents(state: AgentState) -> AgentState:
    """Grade each retrieved document for relevance to the query, filter out irrelevant ones."""
    relevant_docs = []

    for doc in state['retrieved_docs']:
        content = doc.payload.get('text', {}).get('content', '')

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


def has_relevant_docs(state: AgentState) -> str:
    """Conditional edge: route based on whether any relevant documents remain."""
    if state['retrieved_docs']:
        return "generate_answer"
    return "no_docs"


def handle_no_docs(state: AgentState) -> AgentState:
    """Fallback node when no relevant documents are found."""
    state['answer'] = "I don't know — no relevant documents were found for your question."
    return state

def generate_answer(state: AgentState) -> AgentState:
    system_prompt = f"""
        You are a helpful assistant. Answer the following question only based on the following sources below.
        If the answer is not in the sources, say "I don't know" do not provide an answer based on your trained knowledge.
        If the question has nothing to do with the provided sources, say: "I may need to refine the question."
        Do not use any external knowledge, assumptions, or general LLM knowledge, only the context provided should be used.
    """

    human_prompt = f"""
        Question: {state['query']}
        
        Context provided: {state['retrieved_docs']}
    """

    llm_response = ollama.chat(model=settings.OLLAMA_MODEL, messages=[
        { "role": "system", "content": system_prompt },
        { "role": "user", "content": human_prompt },
    ])

    state['answer'] = llm_response['message']['content']

    return state