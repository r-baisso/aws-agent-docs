
import asyncio
import sys
# Make sure project root is in path
sys.path.append("c:/Users/renan.baisso/projetos/aws_doc_agents")

from api.services.rag import answer_question

async def main():
    service_name = "AmazonS3"
    question = "How do I configure a general purpose bucket?"
    print(f"--- Verifying RAG with Qdrant for {service_name} ---")
    print(f"Question: {question}")
    
    try:
        answer = answer_question(service_name, question)
        print("\nGenerated Answer:")
        print(answer)
    except Exception as e:
        print(f"\nError generating answer: {e}")

if __name__ == "__main__":
    asyncio.run(main())
