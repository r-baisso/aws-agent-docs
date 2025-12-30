from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from api.models import ScrapeRequest, AskRequest, AgentRequest
from api.models import ScrapeRequest, AskRequest, AgentRequest
from api.services.scraper import scrape_aws_docs
from api.services.vector_db import build_service_index, list_available_services, delete_service_index
from api.services.aws_metadata import get_available_services
from api.services.rag import answer_question, answer_question_stream
from api.services.agent import run_agent, run_agent_stream

import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AWS Doc Agent", version="0.3.0")

@app.get("/services")
def get_services():
    logger.info("Request received: GET /services")
    return {"services": list_available_services()}

@app.get("/services/available")
def get_available_scrape_services():
    logger.info("Request received: GET /services/available")
    return {"services": get_available_services()}

@app.delete("/services/{service_name}")
def delete_service(service_name: str):
    logger.info(f"Request received: DELETE /services/{service_name}")
    return delete_service_index(service_name)

def scrape_and_index_pipeline(services, limit, max_jobs):
    # Iterate through scraper events
    for event_str in scrape_aws_docs(services, limit=limit, max_jobs=max_jobs):
        yield event_str + "\n"
        
        # Check if this event was a successful scrape result
        try:
            event = json.loads(event_str)
            if event.get("type") == "result" and event.get("status") == "success":
                service = event.get("service")
                yield json.dumps({"type": "log", "message": f"Indexing {service}..."}) + "\n"
                
                # Build Index
                try:
                    stats = build_service_index(service)
                    yield json.dumps({
                        "type": "index_result",
                        "service": service,
                        "stats": stats
                    }) + "\n"
                    yield json.dumps({"type": "log", "message": f"Indexing complete for {service}."}) + "\n"
                except Exception as e:
                    logger.error(f"Indexing failed for {service}: {e}")
                    yield json.dumps({"type": "error", "message": f"Indexing failed: {e}"}) + "\n"
                    
        except Exception:
            pass

@app.post("/scrape")
async def scrape_service(request: ScrapeRequest):
    logger.info(f"Request received: POST /scrape - Services: {request.services}")
    
    return StreamingResponse(
        scrape_and_index_pipeline(request.services, request.limit, request.max_jobs),
        media_type="text/event-stream"
    )

@app.post("/ask")
async def ask_question(request: AskRequest):
    logger.info(f"Request received: POST /ask - Service: {request.service_name}, Stream: {request.stream}")
    if request.stream:
        # answer_question_stream is an async generator, so we can pass it directly
        return StreamingResponse(
            answer_question_stream(request.service_name, request.question, request.history),
            media_type="text/event-stream"
        )
    return {"answer": answer_question(request.service_name, request.question, request.history)}

@app.post("/agent")
async def run_agent_endpoint(request: AgentRequest):
    logger.info(f"Request received: POST /agent - Stream: {request.stream}")
    if request.stream:
        return StreamingResponse(
            run_agent_stream(request.query),
            media_type="text/event-stream"
        )
    return {"response": run_agent(request.query)}
