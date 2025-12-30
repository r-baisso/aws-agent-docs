
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from api.main import app
    print("Successfully imported FastAPI app from api.main")
except Exception as e:
    print(f"Failed to import api.main: {e}")
    import traceback
    traceback.print_exc()
