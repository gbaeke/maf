import asyncio
import os
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

# Load environment variables from .env
load_dotenv()

async def main():
    # Create a client
    client = AzureOpenAIResponsesClient(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    )
    
    # Create an agent
    agent = client.create_agent(
        name="OutlineAgent",
        instructions="Based on the user's request, you create an outline for a presentation.",
    )
    
    # Run the agent
    result = await agent.run("Create an outline for a presentation about Python")
    print(result.text)

if __name__ == "__main__":
    asyncio.run(main())