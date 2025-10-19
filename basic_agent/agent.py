import asyncio
import os
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

# Load environment variables from .env file
load_dotenv()

async def main():
    """
    Create and run an AI agent using Microsoft Agent Framework with Azure OpenAI.
    
    This agent uses the Azure OpenAI configuration from your .env file:
    - AZURE_OPENAI_ENDPOINT
    - AZURE_OPENAI_API_KEY
    - AZURE_OPENAI_API_VERSION
    - AZURE_OPENAI_DEPLOYMENT
    """
    
    # Get Azure OpenAI configuration from environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    if not all([endpoint, api_key, deployment_name]):
        raise ValueError("Missing required Azure OpenAI configuration in .env file")
    
    print(f"🚀 Initializing Agent with Azure OpenAI...")
    print(f"   Endpoint: {endpoint}")
    print(f"   Deployment: {deployment_name}")
    print(f"   API Version: {api_version}")
    
    # Create agent with Azure OpenAI Responses Client
    # Using API key authentication from .env file
    agent = AzureOpenAIResponsesClient(
        endpoint=endpoint,
        api_key=api_key,
        # api_version=api_version,  --> left out to use default
        deployment_name=deployment_name
    ).create_agent(
        name="AssistantBot",
        instructions="""You are a helpful AI assistant created using the Microsoft Agent Framework. 
        You are knowledgeable, friendly, and always aim to provide accurate and helpful responses. 
        You can help with a wide variety of tasks including answering questions, providing explanations, 
        helping with code, and general assistance."""
    )
    
    print("\n✅ Agent initialized successfully!\n")
    
    # Example interactions
    test_prompts = [
        "Hello! Can you introduce yourself?",
        "What is the Microsoft Agent Framework?",
        "Write a short Python function to calculate the factorial of a number"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"🤔 Query {i}: {prompt}")
        print("🤖 Response:", end=" ")
        
        # Get response from the agent
        result = await agent.run(prompt)
        print(f"{result}\n")
        print("-" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with Azure OpenAI credentials")
        print("2. Installed the required packages: pip install -r requirements.txt")
        print("3. Authenticated with Azure CLI: az login (if using Azure CLI credentials)")