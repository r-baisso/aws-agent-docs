import os
import re
import uuid
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from api.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Configure Google GenAI Client
google_client = None
if settings.GOOGLE_API_KEY:
    google_client = genai.Client(api_key=settings.GOOGLE_API_KEY)

# Initialize Qdrant Client
# We assume the user has Qdrant running locally on Docker at the specified host/port
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

def get_embedding(text: str):
    # Using the new embedding model via google.genai SDK
    # ref: https://googleapis.github.io/python-genai/
    if not google_client:
        raise ValueError("Google API Key not configured")
        
    result = google_client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL_ID,
        contents=text,
        config=None # Task type is handled differently or defaults are fine
    )
    return result.embeddings[0].values

def split_markdown_by_headers(markdown_text):
    """
    Splits markdown text by headers (#, ##, ###) and returns chunks with hierarchy context.
    """
    lines = markdown_text.split('\n')
    chunks = []
    current_chunk_lines = []
    header_stack = [] # List of (level, text)
    
    for line in lines:
        header_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if header_match:
            # Save previous chunk if it has content
            if current_chunk_lines:
                text = '\n'.join(current_chunk_lines).strip()
                if text:
                    # Construct context from header stack
                    context = " > ".join([h[1] for h in header_stack])
                    chunks.append({"text": text, "context": context})
                current_chunk_lines = []
            
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            
            # Update header stack
            while header_stack and header_stack[-1][0] >= level:
                header_stack.pop()
            header_stack.append((level, title))
            
            # Add header to current chunk (optional, but good for context)
            current_chunk_lines.append(line)
        else:
            current_chunk_lines.append(line)
            
    # Add last chunk
    if current_chunk_lines:
        text = '\n'.join(current_chunk_lines).strip()
        if text:
            context = " > ".join([h[1] for h in header_stack])
            chunks.append({"text": text, "context": context})
            
    return chunks

def _sanitize_collection_name(name: str) -> str:
    # Qdrant collection names should be alphanumeric, underscores, or hyphens.
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def build_service_index(service_name: str):
    """
    Builds a Qdrant collection for a specific service.
    """
    raw_file = os.path.join(settings.RAW_DATA_DIR, f"{service_name}.md")
    if not os.path.exists(raw_file):
        return {"status": "error", "message": f"Raw data for {service_name} not found."}

    collection_name = _sanitize_collection_name(service_name)
    logger.info(f"Processing {service_name} into collection '{collection_name}'...")
    
    documents = []
    
    with open(raw_file, "r", encoding="utf-8") as f:
        content = f.read()
        
        # Split by pages first
        pages = content.split("--- START PAGE: ")
        for page in pages:
            if not page.strip(): continue
            
            # Extract URL
            try:
                url_end = page.find(" ---")
                if url_end == -1: continue
                url = page[:url_end].strip()
                page_content = page[url_end+4:].split("--- END PAGE:")[0]
                
                # Hierarchical chunking
                chunks = split_markdown_by_headers(page_content)
                
                for chunk in chunks:
                    # Combine context and text for embedding
                    full_text = f"Context: {chunk['context']}\nContent: {chunk['text']}"
                    # Limit chunk size (simple char limit for now)
                    if len(full_text) > 2000:
                        full_text = full_text[:2000]
                    
                    documents.append({
                        "source": f"{service_name}.md",
                        "service": service_name,
                        "url": url,
                        "context": chunk['context'],
                        "text": chunk['text'],
                        "embedding_text": full_text
                    })
            except Exception as e:
                print(f"Error processing page in {service_name}: {e}")

    if not documents:
        return {"status": "no documents found"}

    # Generate embeddings
    points = []
    
    print(f"Generating embeddings for {len(documents)} chunks...")
    logger.info(f"Generating embeddings for {len(documents)} chunks...")
    for i, doc in enumerate(documents):
        try:
            emb = get_embedding(doc["embedding_text"])
            
            # Create Qdrant Point
            point_id = str(uuid.uuid4())
            payload = {
                "source": doc["source"],
                "service": doc["service"],
                "url": doc["url"],
                "context": doc["context"],
                "text": doc["text"]
            }
            
            points.append(PointStruct(id=point_id, vector=emb, payload=payload))
            
            if i % 10 == 0:
                logger.debug(f"Embedded {i}/{len(documents)}")
        except Exception as e:
            logger.error(f"Error embedding chunk: {e}")

    if not points:
         return {"status": "failed to generate embeddings"}

    # Recreate collection
    dimension = len(points[0].vector)
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
        
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )

    # Upload points in batches to avoid payload size limits (e.g., 32MB limit)
    batch_size = 100
    total_points = len(points)
    
    for i in range(0, total_points, batch_size):
        batch = points[i : i + batch_size]
        logger.info(f"Upserting batch {i//batch_size + 1}/{(total_points + batch_size - 1)//batch_size} ({len(batch)} points)...")
        try:
            client.upsert(
                collection_name=collection_name,
                points=batch
            )
        except Exception as e:
            logger.error(f"Failed to upsert batch starting at {i}: {e}")
            # Optionally retry or re-raise? For now, we log and continue/raise
            raise e
    
    return {"status": "success", "documents_indexed": len(points)}

def list_service_headers(service_name: str) -> list[str]:
    """
    Returns a unique list of 'context' paths available for a service.
    """
    collection_name = _sanitize_collection_name(service_name)
    
    try:
        # Check if collection exists first
        client.get_collection(collection_name)
    except Exception:
        return []
        
    # Scroll through all points to collect contexts
    # Note: For very large collections, this might be slow. 
    # A better approach for production would be a separate payload index or dedicated structure.
    contexts = set()
    offset = None
    
    while True:
        points, next_offset = client.scroll(
            collection_name=collection_name,
            scroll_filter=None,
            limit=100,
            with_payload=True,
            with_vectors=False,
            offset=offset
        )
        
        for point in points:
            if point.payload and "context" in point.payload:
                contexts.add(point.payload["context"])
                
        offset = next_offset
        if offset is None:
            break
            
    return sorted(list(contexts))

def search_service_index(service_name: str, query: str, k: int = 5, path_filters: list[str] = None):
    """
    Searches the service index, optionally filtering by path contexts.
    """
    collection_name = _sanitize_collection_name(service_name)
    
    try:
        client.get_collection(collection_name)
    except Exception:
        return []
        
    query_emb = get_embedding(query)
    logger.debug(f"Generated embedding for query '{query}'")
    
    # Construct Filter
    query_filter = None
    if path_filters:
        # We want to match if ANY of the path_filters match the context.
        # Qdrant 'match' - 'text' check keywords. 'match' - 'value' checks exact match.
        # If we want "contains", we might need full text index on payload or use regex (slow).
        # For now, let's assume 'context' field in payload is not indexed for text search by default unless configured.
        # But we can assume exact match or simple match.
        # Let's try simple match for now. If path_filters are "S3 > Features", we check if context == "S3 > Features".
        # If we want substring, we'd need to iterate or use specific Qdrant features.
        
        should_conditions = []
        for pf in path_filters:
            # MatchValue checks for equality. 
            should_conditions.append(FieldCondition(key="context", match=MatchValue(value=pf)))
            
        query_filter = Filter(should=should_conditions)

    search_result = client.query_points(
        collection_name=collection_name,
        query=query_emb,
        query_filter=query_filter,
        limit=k,
        with_payload=True
    ).points
    
    results = []
    for scored_point in search_result:
        results.append({
            "content": scored_point.payload["text"],
            "context": scored_point.payload.get("context", ""),
            "source": scored_point.payload.get("source", ""),
            "url": scored_point.payload.get("url", ""),
            "score": scored_point.score
        })
                
    return results

def list_available_services() -> list[str]:
    """
    Lists all available services (collections) in Qdrant.
    """
    try:
        collections_response = client.get_collections()
        # Filter mostly to standard service names (optional)
        return [c.name for c in collections_response.collections]
    except Exception:
        return []

def delete_service_index(service_name: str) -> dict:
    """
    Deletes the Qdrant collection and raw data file for a service.
    """
    collection_name = _sanitize_collection_name(service_name)
    results = {"service": service_name, "actions": []}
    
    # 1. Delete Qdrant Collection
    try:
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            results["actions"].append("Deleted vector index")
        else:
            results["actions"].append("Vector index not found")
    except Exception as e:
        logger.error(f"Error deleting collection {collection_name}: {e}")
        results["errors"] = results.get("errors", []) + [f"Vector DB error: {str(e)}"]

    # 2. Delete Raw File
    try:
        raw_file = os.path.join(settings.RAW_DATA_DIR, f"{service_name}.md")
        if os.path.exists(raw_file):
            os.remove(raw_file)
            logger.info(f"Deleted file: {raw_file}")
            results["actions"].append("Deleted raw data file")
        else:
             # Try .txt just in case of legacy
            raw_file_txt = os.path.join(settings.RAW_DATA_DIR, f"{service_name}.txt")
            if os.path.exists(raw_file_txt):
                os.remove(raw_file_txt)
                results["actions"].append("Deleted raw data file (txt)")
            else:
                results["actions"].append("Raw file not found")
                
    except Exception as e:
        logger.error(f"Error deleting file for {service_name}: {e}")
        results["errors"] = results.get("errors", []) + [f"File error: {str(e)}"]

    return results
