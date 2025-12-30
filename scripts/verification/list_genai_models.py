
import sys
import os
sys.path.append(os.getcwd())

from google import genai
from api.core.config import settings

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

print("Listing models...")
for m in client.models.list(config={"page_size": 100}):
    print(f"Model: {m.name}")
