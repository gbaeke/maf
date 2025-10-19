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
    This version demonstrates streaming responses and conversation history for better user experience.
    
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
    
    print(f"🚀 Initializing Streaming Agent with Azure OpenAI...")
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
        name="StreamingAssistantBot",
        instructions="""You are a helpful AI assistant created using the Microsoft Agent Framework. 
        You are knowledgeable, friendly, and always aim to provide accurate and helpful responses. 
        You can help with a wide variety of tasks including answering questions, providing explanations, 
        helping with code, and general assistance. You respond in a conversational and engaging manner.
        You remember our conversation and can refer back to previous exchanges."""
    )
    
    print("\n✅ Streaming Agent with Conversation Memory initialized successfully!\n")
    
    # Create a conversation thread to maintain history
    # See https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/multi-turn-conversation?pivots=programming-language-python
    thread = agent.get_new_thread()
    
    # Example interactions with streaming responses and conversation memory
    test_prompts = [
        "Hello! Can you introduce yourself and tell me what makes you special?",
        "My name is Alice. Can you remember that for our conversation?",
        "What is the Microsoft Agent Framework and how does it work?",
        "What's my name again? And can you summarize what we've discussed so far?"
    ]
    
    try:
        for i, prompt in enumerate(test_prompts, 1):
            print(f"🤔 Query {i}: {prompt}")
            print("🤖 Response: ", end="", flush=True)
            
            # Stream response from the agent with conversation thread
            # The thread maintains conversation history automatically
            async for chunk in agent.run_stream(prompt, thread=thread):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            
            print("\n")  # New line after streaming is complete
            print("-" * 80)
            
            # Add a small delay between queries for better readability
            await asyncio.sleep(1)
            
    finally:
        # Clean up resources if needed
        print("🧹 Demo completed - conversation history maintained throughout!")
        print("💡 Try interactive mode to see the memory in action: python agent_streaming.py interactive")

async def interactive_mode():
    """
    Interactive mode where users can chat with the streaming agent.
    This version maintains conversation history using AgentThread.
    """
    # Get Azure OpenAI configuration from environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    if not all([endpoint, api_key, deployment_name]):
        raise ValueError("Missing required Azure OpenAI configuration in .env file")
    
    # Create agent
    agent = AzureOpenAIResponsesClient(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment_name
    ).create_agent(
        name="InteractiveStreamingBot",
        instructions="""You are a helpful AI assistant created using the Microsoft Agent Framework. 
        You are knowledgeable, friendly, and always aim to provide accurate and helpful responses. 
        Keep your responses conversational and engaging. You remember our entire conversation."""
    )
    
    # Create a conversation thread to maintain history
    # Azure OpenAI Responses service stores conversation history in the service
    thread = agent.get_new_thread()
    
    print("\n🎯 Interactive Streaming Mode with Conversation Memory")
    print("Type your questions and see responses stream in real-time!")
    print("The agent will remember our entire conversation!")
    print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Goodbye! Thanks for chatting!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Agent: ", end="", flush=True)
                
                # Stream the response with conversation thread
                # The thread maintains conversation history automatically
                async for chunk in agent.run_stream(user_input, thread=thread):
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                
                print("\n")  # New line after streaming
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for chatting!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
                
    finally:
        # Note: For Azure OpenAI Responses, threads may be persisted in the service
        # The framework handles cleanup automatically
        print("🧹 Cleaning up conversation thread...")
        print("✅ Session completed - conversation was managed by the service")

if __name__ == "__main__":
    import sys
    
    try:
        # Check if user wants interactive mode
        if len(sys.argv) > 1 and sys.argv[1].lower() in ['interactive', 'chat', '-i']:
            asyncio.run(interactive_mode())
        else:
            print("Running demo mode with predefined prompts...")
            print("For interactive mode, run: python agent_streaming.py interactive\n")
            asyncio.run(main())
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with Azure OpenAI credentials")
        print("2. Installed the required packages: pip install -r requirements.txt")
        print("3. Authenticated with Azure CLI: az login (if using Azure CLI credentials)")
        print("\nUsage:")
        print("  python agent_streaming.py          # Run demo mode")
        print("  python agent_streaming.py interactive # Run interactive chat mode")