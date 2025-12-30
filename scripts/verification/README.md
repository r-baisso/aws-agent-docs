# Verification & Utility Scripts

This directory contains scripts used to verify the functionality of the AWS Doc Agent components and to inspect underlying libraries.

## Verification Scripts

Use these scripts to verify that specific components are working correctly.

| Script | Description |
|--------|-------------|
| `verify_scraper.py` | Verifies that the scraper can fetch pages and save them as Markdown. |
| `verify_qdrant.py` | Verifies the Qdrant vector store integration (Indexing, Search, Filtering). |
| `verify_rag_qdrant.py` | Verifies the full RAG pipeline (Retrieval + Generation) using Qdrant and Gemini. |
| `verify_agent.py` | Verifies the Strands Agent creation and tool execution. |
| `verify_gemini_import.py` | Simple check to ensure `strands-agents[gemini]` is installed correctly. |


## Usage

Run these scripts from the project root to ensure imports work correctly:

```bash
# Example: Verify Qdrant RAG
python scripts/verification/verify_rag_qdrant.py
```
