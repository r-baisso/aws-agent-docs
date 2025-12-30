import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DATA_DIR = os.path.join(os.getcwd(), "data")
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    VECTOR_DB_DIR = os.path.join(DATA_DIR, "vectordb")
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    
    # Model Configuration
    GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash")
    GEMINI_RAG_MODEL_ID = os.getenv("GEMINI_RAG_MODEL_ID", "gemini-2.0-flash")
    GEMINI_AGENT_MODEL_ID = os.getenv("GEMINI_AGENT_MODEL_ID", "gemini-2.0-flash")
    GEMINI_EMBEDDING_MODEL_ID = os.getenv("GEMINI_EMBEDDING_MODEL_ID", "text-embedding-004")

    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    
    # OpenTelemetry Configuration
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("LANGFUSE_HOST", "http://localhost:3000") + "/api/public/otel"
    OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "aws-doc-agent")
    OTEL_TRACE_SAMPLING_RATIO = float(os.getenv("OTEL_TRACE_SAMPLING_RATIO", "1.0"))

    def __init__(self):
        os.makedirs(self.RAW_DATA_DIR, exist_ok=True)
        os.makedirs(self.VECTOR_DB_DIR, exist_ok=True)

settings = Settings()
