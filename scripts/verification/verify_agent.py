import asyncio
import sys
import os
sys.path.append(os.getcwd())

from api.services.agent import create_agent

import logging
import sys

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# Silence other noisy loggers
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

async def main():
    print("Initializing Agent...")
    try:
        agent = create_agent()
        
        queries = [
            "List available services",
            "What features does AmazonS3 offer?"
        ]
        
        for q in queries:
            print(f"\nUser: {q}")
            # Strands agent instance is callable. If it returns a coroutine, await it.
            # If it handles its own loop, just call it.
            # Given the previous stack trace, it seems to handle async internally or require it.
            # Let's try calling it in a way that is friendly to the loop.
            
            # Try awaiting
            if asyncio.iscoroutinefunction(agent) or asyncio.iscoroutine(agent):
                 response = await agent(q)
            else:
                 # Check if the result is awaitable
                 res = agent(q)
                 if asyncio.iscoroutine(res):
                     response = await res
                 else:
                     response = res
            print(f"Agent: {response}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting verification (Async mode)...")
    asyncio.run(main())
