from strands import Agent
from strands.models.gemini import GeminiModel
from api.core.config import settings
from api.services.vector_db import search_service_index
import logging
import json

logger = logging.getLogger(__name__)

# Initialize RAG Model
gemini_rag_model = None
if settings.GOOGLE_API_KEY:
    try:
        gemini_rag_model = GeminiModel(
            client_args={
                "api_key": settings.GOOGLE_API_KEY,
            },
            model_id=settings.GEMINI_RAG_MODEL_ID,
            params={
                "temperature": 0.3, # Slightly creative but grounded
                "max_output_tokens": 8192,
            }
        )
    except Exception as e:
        logger.error(f"Failed to initialize GeminiModel for RAG: {e}")

def retrieve_service_docs(service_name: str, query: str, path_filters: list[str] = None):
    """
    Retrieve relevant documents from the service's knowledge base.
    """
    logger.debug(f"Retrieving docs for {service_name} with query: '{query}'")
    docs = search_service_index(service_name, query, k=5, path_filters=path_filters)
    # Deduplicate based on content to avoid repetitive context
    seen = set()
    unique_docs = []
    for doc in docs:
        if doc['content'] not in seen:
            unique_docs.append(doc)
            seen.add(doc['content'])
            
    logger.debug(f"Retrieved {len(unique_docs)} unique documents.")
    return unique_docs

from langfuse import observe

def _prepare_rag_context(service_name: str, docs: list[dict], history: list[dict] = None) -> str:
    """Helper to construct the RAG context string."""
    context_str = ""
    for i, doc in enumerate(docs):
        context_str += f"Source {i+1} ({doc['url']}):\n{doc['content']}\n\n"
        
    history_str = ""
    if history:
        history_str = "Chat History:\n"
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n"
        history_str += "\n"

    system_prompt = f"""You are a helpful assistant for AWS {service_name} documentation.
Your goal is to answer the user's question mostly based on the provided Context.

Instructions:
1. Use the Context below to answer the user's question.
2. If the answer is not in the Context, say "I couldn't find relevant information in the knowledge base." but you can try to answer from your general knowledge if clearly stated.
3. Always cite the Source URLs provided in the Context when using that information.
4. Be concise and professional.

Context:
{context_str}

{history_str}
"""
    return system_prompt

def _create_rag_agent() -> Agent:
    """Helper to create a configured Strands Agent for RAG (without system prompt)."""
    if not gemini_rag_model:
        raise ValueError("Gemini RAG Model not initialized.")
        
    # Initialize agent with NO tools and NO system prompt (to avoid model incompatibility)
    agent = Agent(
        model=gemini_rag_model,
        tools=[], 
        system_prompt=None
    )
    return agent

@observe(as_type="agent")
def answer_question(service_name: str, question: str, history: list[dict] = None):
    """
    Generates an answer using RAG via Strands Agent.
    """
    try:
        # 1. Retrieve
        docs = retrieve_service_docs(service_name, question)
        if not docs:
            return f"I couldn't find any relevant information in the {service_name} knowledge base."
            
        # 2. Create Agent and Context
        context_instruction = _prepare_rag_context(service_name, docs, history)
        agent = _create_rag_agent()
        
        # 3. Run Agent
        # Prepend context to the question since we can't use system_prompt with some models
        full_prompt = f"{context_instruction}\n\nUser Question: {question}"
        
        response = agent(full_prompt)
        return response.get("response", {}).get("text", "No response generated.")
        
    except Exception as e:
        logger.error(f"RAG Error: {e}")
        return f"Error generating answer: {e}"

# We skip standalone query rewrite for now to keep it simple with Strands,
# or we could reimplement it using a simple strands agent too if needed.
# For now, simplistic history injection is often sufficient.

@observe(as_type="agent")
async def answer_question_stream(service_name: str, question: str, history: list[dict] = None):
    """
    Generates a streaming answer using RAG via Strands Agent.
    """
    try:
        # 1. Retrieve
        docs = retrieve_service_docs(service_name, question)
        if not docs:
             yield f"I couldn't find any relevant information in the {service_name} knowledge base."
             return

        # 2. Create Agent and Context
        context_instruction = _prepare_rag_context(service_name, docs, history)
        agent = _create_rag_agent()
        
        # 3. Stream Agent
        full_prompt = f"{context_instruction}\n\nUser Question: {question}"
        
        async for chunk in agent.stream_async(full_prompt):
            # Parse Strands chunk for content
             if "event" in chunk:
                 event_data = chunk["event"]
                 if "contentBlockDelta" in event_data:
                     delta = event_data["contentBlockDelta"].get("delta", {})
                     if "text" in delta:
                         yield delta["text"]
                         
    except Exception as e:
        logger.error(f"RAG Stream Error: {e}")
        yield f"Error generating answer: {e}"
