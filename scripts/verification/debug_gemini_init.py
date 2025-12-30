
import sys
import os
sys.path.append(os.getcwd())
from api.core.config import settings
from strands.models.gemini import GeminiModel

print("Initializing GeminiModel...")
try:
    gemini_model = GeminiModel(
        client_args={
            "api_key": settings.GOOGLE_API_KEY,
        },
        model_id="gemini-flash-latest",
        params={
            "temperature": 0.0,
            "max_output_tokens": 8192,
        }
    )
    print("GeminiModel initialized.")
except Exception as e:
    print(f"Failed: {e}")
