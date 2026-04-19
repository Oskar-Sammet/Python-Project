from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from pydantic import BaseModel, Field
from src.config import get_settings

settings = get_settings()

class RelevanceAnswer(BaseModel):
    boolean: bool = Field(description="Ether Yes or No depending if the provided document is relevant for answering the users question.")
    reasoning: str = Field(..., description="Relevance Answer")

SYSTEM_PROMPT = """
    You are a relevance grader. Given a user question and a document you decided weather or not the provided document is relevant for 
    answering the users question. Do not use any external knowledge, assumptions, or general LLM knowledge—only the context provided should be used. 
    Even if the answer is not "yes" or a "no" (if that is the case), it still can be valid.
    
    Answers that correctly indicate lack of information in the context (e.g., "I don't know based on the provided documents") should be considered partially valid and receive a "yes"
    
    Reply only with a yes or no and provide a brief reasoning for why you 
"""

HUMAN_PROMPT = """
    User question: {question}
    
    Context Documents: {context}
    
    LLM generation: {generation}
    Provide the reasoning behind.
"""

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT),
])

def get_doc_relevance_chain(llm: BaseChatModel) -> RunnableSequence:
    structured_llm_relevance = llm.with_structured_output(RelevanceAnswer)
    return ANSWER_PROMPT | structured_llm_relevance