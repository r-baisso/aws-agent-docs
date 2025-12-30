# AWS Doc Agents

A FastAPI-based agentic system that scrapes AWS documentation, indices it into a Qdrant vector database, and provides RAG capabilities using Google Gemini and the `strands` library.

## Documentation
- [Frontend Guide](doc/frontend.md)
- [Changelog](doc/changelog.md)
- [System Architecture](doc/architecture.md)
- [Agents Architecture](doc/agents_architecture.md)

## Features

- **Dynamic Service Discovery**: Automatically fetches the list of all available AWS services from the official sitemap.
- **Parallel Scraping**: High-performance scraping using concurrent threads (configurable via UI) to ingest documentation quickly.
- **Knowledge Base Management**:
    - **Scraping**: Ingests user guides and developer guides, converting them to structured Markdown.
    - **Indexing**: Uses **Qdrant** for efficient vector storage.
    - **Deletion**: Easily remove services from the index and file system via the UI.
- **Hierarchical Chunking**: Preserves document structure (Sections > Sub-sections) for better RAG context.
- **RAG & Agents**:
    - **Chat (RAG)**: Context-aware Q&A with streaming responses and automatic history clearing on context switch.
    - **Agent Search**: An autonomous agent that plans, explores, and synthesizes information across services.

## Setup

1.  **Clone the repository**.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Start Qdrant**:
    You need a local Qdrant instance running. Use Docker:
    ```bash
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
    ```
5.  **Environment Variables**:
    Create a `.env` file in the root directory:
    ```
    GOOGLE_API_KEY=your_gemini_api_key_here
    QDRANT_HOST=localhost
    QDRANT_PORT=6333
    ```

## Usage

### 1. Run the API
Start the FastAPI server:
```bash
uvicorn api.main:app --reload
```
The API will be available at `http://localhost:8000`. You can access the interactive documentation at `http://localhost:8000/docs`.

### 2. Verify Components

**Verify Qdrant Integration**:
```bash
python scripts/verification/verify_qdrant.py
```

**Verify RAG & Agent**:
```bash
python scripts/verification/verify_rag_qdrant.py
```

For a full list of verification scripts, see [scripts/verification/README.md](scripts/verification/README.md).
