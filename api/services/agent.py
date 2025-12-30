from strands import Agent, tool
from strands.models.gemini import GeminiModel
from api.core.config import settings
from api.services.rag import retrieve_service_docs
from api.services.vector_db import list_service_headers
from langfuse import observe

import json
import os
import logging

logger = logging.getLogger(__name__)

# Initialize the model
gemini_model = None
if settings.GOOGLE_API_KEY:
    try:
        gemini_model = GeminiModel(
            client_args={
                "api_key": settings.GOOGLE_API_KEY,
            },
            model_id=settings.GEMINI_AGENT_MODEL_ID,
            params={
                "temperature": 0.0,
                "max_output_tokens": 8192,
            }
        )
    except Exception as e:
        print(f"Failed to initialize GeminiModel: {e}")

@tool
def list_available_services() -> list[str]:
    """
    Lists the AWS services available in the knowledge base documentation.
    
    Returns:
        List of service names to be used in `explore_service_topics` and `search_service_documentation`.
    """
    if not settings.QDRANT_HOST:
         return []
         
    from api.services.vector_db import list_available_services as db_list_services
    return db_list_services()

@tool
def explore_service_topics(service_name: str) -> list[str]:
    """
    Lists the topics available for a specific AWS service in the knowledge base documentation.
    Use this to understand what information is available for a service before searching.
    
    Args:
        service_name: The name of the AWS service (e.g., 'AmazonS3') from `list_available_services`.
        
    Returns:
        Unique list of topics from service documentation.
    """
    return list_service_headers(service_name)

@tool
def search_service_documentation(service_name: str, query: str, context_filters: list[str] = None) -> str:
    """
    Searches the documentation for a specific AWS service.
    
    Args:
        service_name: The name of the AWS service (e.g., 'AmazonS3') from `list_available_services`.
        query: The search query.
        context_filters: Optional list of context paths (from explore_service_topics) to filter the search.
        
    Returns:
        Relevant documentation snippets with sources.
    """
    docs = retrieve_service_docs(service_name, query, path_filters=context_filters)
    if not docs:
        return "No relevant documentation found."
        
    result = ""
    for i, doc in enumerate(docs):
        result += f"--- Result {i+1} ---\n"
        result += f"Source: {doc['url']}\n"
        result += f"Context: {doc['context']}\n"
        result += f"Content:\n{doc['content']}\n\n"
        
    return result

def create_agent():
    """Creates and returns the Strands Agent instance."""
    if not gemini_model:
        raise ValueError("Gemini Model not initialized. Check API Key.")
        
    agent = Agent(
        model=gemini_model,
        tools=[list_available_services, explore_service_topics, search_service_documentation],
        system_prompt="""You are an expert AWS Documentation Assistant.
Your goal is to help users find information about AWS services by querying the local knowledge base.

Follow this "work loop":
1. Identify the service the user is asking about. If not clear, ask the user and repeat this step.
2. Always explore available services and topics using `list_available_services` and `explore_service_topics` to understand the documentation structure and build a plan to answer the user's question.
3. Use `search_service_documentation` to find specific information about some service or topic from user question. 
   - Use `context_filters` if you have identified relevant topics from step 2 to make the search more precise.
4. Synthesize the information found to answer the user's question.
5. Always cite the sources (URLs) provided in the search results.

If you cannot find information on the knowledge base, suggest checking the official AWS website.
"""
    )
    return agent


@observe(as_type="agent")
def run_agent(query: str):
    """
    Runs the agent with Langfuse observability.
    """
    logger.debug(f"Starting agent with query: {query}")
    agent = create_agent()
    # Strands agent is callable
    return agent(query)

@observe(as_type="agent")
async def run_agent_stream(query: str):
    """
    Runs the agent in streaming mode.
    """
    logger.debug(f"Starting agent stream with query: {query}")
    agent = create_agent()
    # streams formatted chunks
    async for chunk in agent.stream_async(query):
        # Inspect chunk for tool calls (reasoning/actions)
        # Chunk structure:
        # Message with toolUse: {'message': {'role': 'assistant', 'content': [{'toolUse': {...}}]}}
        # Content Delta: {'event': {'contentBlockDelta': {'delta': {'text': '...'}}}}
        
        try:
             # Check for Tool Use (The "Reasoning" / Action)
             if "message" in chunk:
                 msg = chunk["message"]
                 if msg.get("role") == "assistant":
                     for content in msg.get("content", []):
                         if "toolUse" in content:
                             tool_use = content["toolUse"]
                             event = {
                                 "type": "thought",
                                 "content": f"🛠️ **Action**: Calling `{tool_use['name']}`\nInput: `{tool_use['input']}`"
                             }
                             yield json.dumps(event) + "\n"
            
             # Check for Tool Result (The Observation) - Optional, sometimes useful to show what it found
             if "message" in chunk:
                 msg = chunk["message"]
                 if msg.get("role") == "user":
                     for content in msg.get("content", []):
                         if "toolResult" in content:
                             # We can summarize or just note it returned
                             event = {
                                 "type": "thought", 
                                 "content": "✅ **Observation**: Received tool result."
                             }
                             yield json.dumps(event) + "\n"

             # Check for Content Delta (The Final Answer)
             if "event" in chunk:
                 event_data = chunk["event"]
                 if "contentBlockDelta" in event_data:
                     delta = event_data["contentBlockDelta"].get("delta", {})
                     if "text" in delta:
                         event = {
                             "type": "answer",
                             "content": delta["text"]
                         }
                         yield json.dumps(event) + "\n"
                         
        except Exception as e:
            logger.error(f"Error parsing chunk: {e}")
