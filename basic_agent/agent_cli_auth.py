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
    
    This version uses Azure CLI credentials for authentication.
    Make sure to run 'az login' before running this script.
    
    Uses configuration from your .env file:
    - AZURE_OPENAI_ENDPOINT
    - AZURE_OPENAI_DEPLOYMENT (for deployment name)
    - AZURE_OPENAI_API_VERSION
    """
    
    # Get Azure OpenAI configuration from environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is required in .env file")
    
    # Use default deployment name if not specified
    if not deployment_name:
        deployment_name = "gpt-4o-mini"
        print(f"⚠️  No AZURE_OPENAI_DEPLOYMENT specified, using default: {deployment_name}")
    
    print(f"🚀 Initializing Agent with Azure OpenAI (Azure CLI auth)...")
    print(f"   Endpoint: {endpoint}")
    print(f"   Deployment: {deployment_name}")
    print(f"   API Version: {api_version or 'default'}")
    print(f"   Authentication: Azure CLI Credential")
    
    try:
        # Create agent with Azure OpenAI Responses Client using Azure CLI credentials
        agent = AzureOpenAIResponsesClient(
            endpoint=endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
            credential=AzureCliCredential()
        ).create_agent(
            name="AssistantBot",
            instructions="""You are a helpful AI assistant created using the Microsoft Agent Framework. 
            You are knowledgeable, friendly, and always aim to provide accurate and helpful responses. 
            You can help with a wide variety of tasks including answering questions, providing explanations, 
            helping with code, and general assistance."""
        )
        
        print("\n✅ Agent initialized successfully!\n")
        
        # Interactive chat loop
        print("💬 Interactive chat started. Type 'quit' or 'exit' to stop.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Agent: ", end="")
                
                # Get response from the agent
                result = await agent.run(user_input)
                print(f"{result}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error during chat: {e}\n")
                
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in to Azure CLI: az login")
        print("2. Verify your Azure OpenAI endpoint in .env file")
        print("3. Check that your Azure account has access to the OpenAI resource")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with Azure OpenAI credentials")
        print("2. Installed the required packages: pip install -r requirements.txt")
        print("3. Authenticated with Azure CLI: az login")