from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from pydantic import BaseModel, Field

class GradeAnswer(BaseModel):
    """Score and reasoning for answer quality"""
    score: float = Field(description="Answer addresses the question, a value between 0.0 and 1.0")
    reasoning: str = Field(..., description="Explanation for why the answer got the score.")


SYSTEM_PROMPT = """
You are a grader assessing whether an answer addresses / resolves a question based only on the provided context. 
Do not use any external knowledge, assumptions, or general LLM knowledge—only the context provided should be used. 
Even if the answer is not "yes" or a "no" (if the case), it still can be valid.

Answers that correctly indicate lack of information in the context (e.g., "I don't know based on the provided documents") should be considered partially valid and receive a score above 0.5.

Give a score between 0.0 and 1.0. 
- 1.0 means the answer fully resolves the question using the provided context.
- 0.5–0.9 means the answer partially addresses the question or correctly indicates that the context lacks sufficient information.
- Below 0.5 means the answer is mostly irrelevant or incorrect according to the context.
- 0.0 means the answer has nothing to do with the question according to the context.
"""

HUMAN_PROMPT = """
User question: 
{question}

Context Documents: {context}

LLM generation: {generation}. 
Provide the reasoning behind.",
"""

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT),
    ]
)


def get_answer_grader_chain(llm: BaseChatModel) -> RunnableSequence:
    """
    Create a LangChain grading chain for assessing answer quality.

    Builds a chain that uses structured output to determine whether an LLM-generated
    answer adequately addresses and resolves the user's question.

    :param llm: The language model to use for answer quality grading
    :return: A runnable chain (prompt | structured_llm) that outputs GradeAnswer
    """
    structured_llm_grader = llm.with_structured_output(GradeAnswer)

    return ANSWER_PROMPT | structured_llm_grader
