
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from api.services.rag import answer_question
from api.services.agent import run_agent

async def main():
    print("--- Verifying Langfuse Observability Integration ---")
    print("Ensure LANGFUSE environment variables are set either in system or .env")
    
    # 1. Verify RAG trace
    print("\n[1] Testing RAG Trace (answer_question)...")
    try:
        # Assuming AmazonS3 exists from previous tests
        ans = answer_question("AmazonS3", "What is traceability?")
        print("RAG Answer received.")
    except Exception as e:
        print(f"RAG failed: {e}")

    # 2. Verify Agent trace
    print("\n[2] Testing Agent Trace (run_agent)...")
    try:
        res = run_agent("List available services")
        print(f"Agent Response: {res}")
    except Exception as e:
        print(f"Agent failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
