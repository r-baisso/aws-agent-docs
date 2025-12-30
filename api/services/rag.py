from google import genai
from api.core.config import settings

# Initialize client
google_client = None
if settings.GOOGLE_API_KEY:
    google_client = genai.Client(api_key=settings.GOOGLE_API_KEY)

from api.services.vector_db import search_service_index, list_service_headers
import logging

logger = logging.getLogger(__name__)

def retrieve_service_docs(service_name: str, query: str, path_filters: list[str] = None):
    """
    Retrieve relevant documents from the service's knowledge base.
    """
    logger.debug(f"Retrieving docs for {service_name} with query: '{query}'")
    docs = search_service_index(service_name, query, k=5, path_filters=path_filters)
    logger.debug(f"Retrieved {len(docs)} documents.")
    return docs

from langfuse import observe

# We might not need answer_question here anymore if the Agent handles it.
# But keeping a simple RAG function for the /ask endpoint is good.

def _construct_rag_prompt(service_name: str, docs: list[dict], question: str, history: list[dict] = None) -> str:
    """Helper to construct the RAG prompt."""
    context_str = ""
    for i, doc in enumerate(docs):
        context_str += f"Source {i+1} ({doc['url']} - {doc['context']}):\n{doc['content']}\n\n"
        
    history_str = ""
    if history:
        history_str = "Chat History:\n"
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n"
        history_str += "\n"

    prompt = f"""You are a helpful assistant for AWS {service_name} documentation. Use the following context to answer the user's question.
If the answer is not in the context, say you don't know.
Always cite the source URL when providing information.

Context:
{context_str}

{history_str}
Question: {question}

Answer:"""
    logger.debug(f"Constructed prompt with {len(prompt)} characters.")
    return prompt

@observe()
def answer_question(service_name: str, question: str, history: list[dict] = None):
    """
    Generates an answer using RAG for a specific service.
    """
    # 1. Retrieve relevant documents
    # Note: We use the raw question for search context. 
    # In a more advanced setup, we'd rewrite the query based on history.
    docs = retrieve_service_docs(service_name, question)
    
    if not docs:
        return f"I couldn't find any relevant information in the {service_name} knowledge base."
    
    # 2. Construct prompt
    prompt = _construct_rag_prompt(service_name, docs, question, history)

    # 3. Generate answer using Gemini
    try:
        if not google_client:
             return "Error: Google API Key not configured."
             
        response = google_client.models.generate_content(
            model=settings.GEMINI_RAG_MODEL_ID,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating answer: {e}"

async def generate_standalone_query(question: str, history: list[dict]) -> str:
    """
    Rewrites the question to be standalone based on history.
    """
    if not history:
        return question

    history_str = ""
    for msg in history[-3:]: # Only use recent history
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_str += f"{role}: {content}\n"

    prompt = f"""Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question.
Chat History:
{history_str}
Follow Up Input: {question}
Standalone Question:"""

    try:
        if not google_client:
            return question
            
        # Use async client if possible, or sync for simplicity since this is short
        response = await google_client.aio.models.generate_content(
            model=settings.GEMINI_RAG_MODEL_ID,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error rewriting query: {e}")
        return question

@observe()
async def answer_question_stream(service_name: str, question: str, history: list[dict] = None):
    """
    Generates a streaming answer using RAG.
    """
    # 0. Contextualize Query
    search_query = question
    if history:
         search_query = await generate_standalone_query(question, history)
         # Yielding a debug message or metadata could be useful, but let's keep it clean for now.
         # print(f"Rewritten Query: {search_query}")

    # 1. Retrieve relevant documents using the rewritten query
    docs = retrieve_service_docs(service_name, search_query)
    
    if not docs:
        yield f"I couldn't find any relevant information in the {service_name} knowledge base."
        return

    # 2. Construct prompt
    # We still use the original question and history for the generation prompt
    # so the model maintains the conversational tone, but the Context is now better.
    prompt = _construct_rag_prompt(service_name, docs, question, history)

    # 3. Generate stream
    try:
        if not google_client:
             yield "Error: Google API Key not configured."
             return

        # Use async client for streaming
        async_client = google_client.aio
        async for chunk in await async_client.models.generate_content_stream(
            model=settings.GEMINI_RAG_MODEL_ID,
            contents=prompt
        ):
             if chunk.text:
                 yield chunk.text

    except Exception as e:
        yield f"Error generating answer: {e}"
