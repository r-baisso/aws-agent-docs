try:
    from strands.models.gemini import GeminiModel
    print("Successfully imported GeminiModel")
except ImportError as e:
    print(f"Failed to import GeminiModel: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
