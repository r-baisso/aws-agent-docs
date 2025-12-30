
import sys
import os
sys.path.append(os.getcwd())
from api.core.config import settings
from google import genai
import asyncio

async def main():
    if not settings.GOOGLE_API_KEY:
        print("No API key")
        return

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    try:
        print("Streaming...")
        # Note: In google-genai, it is client.models.generate_content_stream
        response = client.models.generate_content_stream(
            model=settings.GEMINI_MODEL_ID,
            contents="Hello, say 'streaming works' in 3 words."
        )
        for chunk in response:
            print(f"Chunk: {chunk.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
