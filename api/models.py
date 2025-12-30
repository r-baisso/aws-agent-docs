from pydantic import BaseModel
from typing import List, Optional

class ScrapeRequest(BaseModel):
    services: List[str]
    limit: Optional[int] = None
    max_jobs: int = 4

class AskRequest(BaseModel):
    question: str
    service_name: str
    stream: bool = False
    history: Optional[List[dict]] = None

class AgentRequest(BaseModel):
    query: str
    stream: bool = False
