
import asyncio
import sys
import os
sys.path.append(os.getcwd())

from api.services.agent import create_agent

async def main():
    print("Initializing Agent...")
    try:
        agent = create_agent()
        query = "List available services"
        
        print(f"\nUser: {query}")
        print("Attempting agent.stream()...")
        
        async for chunk in agent.stream_async(query):
            print(f"Chunk: {chunk}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
