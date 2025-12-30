
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def test_ask_stream():
    print("\n--- Testing /ask Stream ---")
    url = f"{BASE_URL}/ask"
    payload = {
        "question": "How do I configure bucket logging?",
        "service_name": "AmazonS3",
        "stream": True
    }
    
    try:
        with requests.post(url, json=payload, stream=True) as r:
            if r.status_code == 200:
                print("Stream started...")
                for chunk in r.iter_content(chunk_size=None):
                    if chunk:
                        print(chunk.decode("utf-8"), end="")
                print("\nStream finished.")
            else:
                print(f"Failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_agent_stream():
    print("\n--- Testing /agent Stream ---")
    url = f"{BASE_URL}/agent"
    payload = {
        "query": "List available services",
        "stream": True
    }
    
    try:
        with requests.post(url, json=payload, stream=True) as r:
            if r.status_code == 200:
                print("Stream started...")
                for chunk in r.iter_content(chunk_size=None):
                    if chunk:
                        print(chunk.decode("utf-8"), end="")
                print("\nStream finished.")
            else:
                print(f"Failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure uvicorn is running
    test_ask_stream()
    test_agent_stream()
