
import asyncio
import os
import sys
from api.services.vector_db import build_service_index, search_service_index, list_service_headers

def main():
    service_name = "AmazonS3"
    print(f"--- Verifying Qdrant Integration for {service_name} ---")

    # 1. Build Index
    print("\n[1] Building Index...")
    result = build_service_index(service_name)
    print(f"Build Result: {result}")
    
    if result.get("status") != "success":
        print("Stopping verification due to build failure.")
        return

    # 2. List Headers
    print("\n[2] Listing Headers...")
    headers = list_service_headers(service_name)
    print(f"Found {len(headers)} context headers.")
    for h in headers[:5]:
        print(f" - {h}")

    # 3. Search
    query = "What are S3 storage classes?"
    print(f"\n[3] Searching for: '{query}'")
    results = search_service_index(service_name, query, k=3)
    
    for i, res in enumerate(results):
        print(f"\nResult {i+1} (Score: {res['score']:.4f}):")
        print(f"Context: {res['context']}")
        print(f"Content: {res['content'][:150]}...")

    # 4. Filtered Search
    if headers:
        filter_path = headers[0]
        print(f"\n[4] Filtered Search (Context: '{filter_path}')")
        f_results = search_service_index(service_name, query, k=3, path_filters=[filter_path])
        for i, res in enumerate(f_results):
            print(f"\nResult {i+1}: {res['context']}")

if __name__ == "__main__":
    main()
