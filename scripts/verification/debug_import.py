
import sys
import os
sys.path.append(os.getcwd())

print("Importing api.services.agent...")
try:
    from api.services.agent import create_agent
    print("Import successful.")
except Exception as e:
    print(f"Import failed: {e}")
