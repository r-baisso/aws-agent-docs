# Changelog

## [0.4.0] - 2025-12-30

### Added
- **Dynamic Service Discovery**: Backend now fetches the full list of AWS services from the official `sitemap_index.xml` via `api.services.aws_metadata`.
- **Parallel Scraping**: `scraper.py` now supports concurrent page fetching using `ThreadPoolExecutor`.
- **Scraping Progress UI**: Frontend now displays a real-time progress bar and log stream during scraping.
- **Service Deletion**: Users can now delete indexed services (files and vector collections) from the Knowledge Base UI.
- **Concurrency Control**: Added a slider in the UI to control the number of scraping threads (1-20).

### Changed
- **Frontend UX**: "Knowledge Base" tab split into "Manage Knowledge Base" (Scrape) and "Indexed Services" (Delete/View).
- **RAG UX**: Chat history is automatically cleared when switching the selected service context.
- **Agent Logic**: Updated agent system prompt to enforce a "Loop" workflow (Explore -> Search -> Synthesize).
- **API Models**: Updated `ScrapeRequest` to include `max_jobs` parameter.
- **RAG Architecture**: Refactored `api/services/rag.py` to use `strands` Agent instead of raw Gemini client.
    - Enables consistent observability via `strands` and Langfuse.
    - Updated to inject context into User Prompt instead of System Prompt to support a wider range of models (e.g., Gemma).

## [0.3.0] - 2025-12-26

### Added
- **API Endpoints**: Implemented FastAPI endpoints for `/scrape`, `/ask` (RAG), and `/agent`.
- **Observability**: Integrated **Langfuse** for tracing RAG and Agent workflows.
- **OpenTelemetry Config**: Added configuration for sending traces via OTLP.
- **Environment Variables**: Externalized model configuration (`GEMINI_MODEL_ID`, `GEMINI_EMBEDDING_MODEL_ID`).
- **Verifications**: Added comprehensive verification scripts in `scripts/verification/`.

### Changed
- **SDK Migration**: Migrated from the deprecated `google.generativeai` to the new `google.genai` SDK.
- **Project Structure**: Organized verification scripts into a dedicated directory.

## [0.2.0] - 2025-12-23

### Added
- **Qdrant Vector Store**: Migrated from FAISS to Qdrant for more robust and scalable vector storage.
    - Requires a local Qdrant instance (Docker).
    - Implemented `api.services.vector_db` to interact with Qdrant.
- **Agent Integration**: Implemented a `Strands` agent with Google Gemini.
    - Added tools: `list_available_services`, `explore_service_topics`, `search_service_documentation`.
    - Integrated with `google.generativeai` (Gemini Flash).
- **RAG Service API**: Created `api.services.rag` to handle retrieval and question answering.
- **Documentation**: Added `doc/` folder with architecture and changelog.

### Changed
- **Scraper Output**: Updated scraper to output Markdown (`.md`) instead of plain text for better structure preservation.
- **Vector DB Logic**: Refactored `api/services/vector_db.py` to support hierarchical chunking and per-service Qdrant collections.
- **Configuration**: Added `QDRANT_HOST` and `QDRANT_PORT` to `api/core/config.py`.

### Removed
- **FAISS**: Removed FAISS dependency and implementation in favor of Qdrant.

## [0.1.0] - Initial Setup
- Basic project structure.
- Scraper for AWS documentation (Text output).
- Basic FastAPI setup.
