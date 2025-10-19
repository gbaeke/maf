# Microsoft Agent Framework - Azure OpenAI Integration

This project demonstrates how to create an AI agent using the Microsoft Agent Framework with Azure OpenAI integration.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   ./setup.sh
   ```
   Or manually:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Azure OpenAI in `.env`:**
   Your `.env` file should contain (already configured):
   ```
   AZURE_OPENAI_ENDPOINT=https://oai-course.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key
   AZURE_OPENAI_API_VERSION=2024-12-01-preview
   AZURE_OPENAI_DEPLOYMENT=gpt-4.1
   ```

3. **Run the agent:**
   
   **Option A: API Key Authentication**
   ```bash
   python3 agent.py
   ```
   
   **Option B: Azure CLI Authentication**
   ```bash
   az login  # if not already logged in
   python3 agent_cli_auth.py
   ```

## 📁 Project Structure

```
├── .env                    # Azure OpenAI configuration
├── requirements.txt        # Python dependencies
├── setup.sh               # Setup script
├── agent.py               # Agent with API key authentication
├── agent_cli_auth.py      # Agent with Azure CLI authentication
└── README.md              # This file
```

## 🔧 Configuration

The project uses your existing `.env` configuration:

- **AZURE_OPENAI_ENDPOINT**: Your Azure OpenAI service endpoint
- **AZURE_OPENAI_API_KEY**: Your API key for authentication
- **AZURE_OPENAI_API_VERSION**: The API version to use
- **AZURE_OPENAI_DEPLOYMENT**: The model deployment name

## 🤖 Agent Features

The created agent:
- Uses Microsoft Agent Framework
- Integrates with Azure OpenAI
- Supports both API key and Azure CLI authentication
- Provides interactive chat functionality
- Has a helpful, knowledgeable personality

## 🔍 Code Examples

### Basic Agent Creation (API Key)
```python
from agent_framework.azure import AzureOpenAIResponsesClient

agent = AzureOpenAIResponsesClient(
    endpoint=endpoint,
    api_key=api_key,
    api_version=api_version,
    deployment_name=deployment_name
).create_agent(
    name="AssistantBot",
    instructions="You are a helpful AI assistant..."
)

result = await agent.run("Hello!")
```

### Basic Agent Creation (Azure CLI)
```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

agent = AzureOpenAIResponsesClient(
    endpoint=endpoint,
    deployment_name=deployment_name,
    credential=AzureCliCredential()
).create_agent(
    name="AssistantBot",
    instructions="You are a helpful AI assistant..."
)

result = await agent.run("Hello!")
```

## 🛠 Troubleshooting

### Import Errors
If you see import errors, make sure to install dependencies:
```bash
pip install -r requirements.txt
```

### Authentication Issues
- **API Key**: Verify your `AZURE_OPENAI_API_KEY` in `.env`
- **Azure CLI**: Run `az login` and ensure you have access to the OpenAI resource

### Endpoint Issues
- Verify your `AZURE_OPENAI_ENDPOINT` is correct
- Check that your deployment name matches your Azure OpenAI deployment

## 📚 Resources

- [Microsoft Agent Framework Documentation](https://github.com/microsoft/agent-framework)
- [Azure OpenAI Service Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/)

## 🎯 Next Steps

- Add custom tools and functions to your agent
- Implement streaming responses
- Add conversation memory
- Integrate with other Azure services
- Deploy to production environments

## 🔄 Agent Orchestration Patterns

The Microsoft Agent Framework supports different ways to orchestrate agents:

- Sequential Agent orchestration in scenarios where step-by-step workflows are needed.
- Concurrent orchestration in scenarios where agents need to complete tasks at the same time.
- Group chat orchestration in scenarios where agents can collaborate together on one task.
- Handoff Orchestration in scenarios where agents hand off the task to one another as the subtasks are completed.
- Magnetic Orchestration in scenarios where a manager agent creates and modifies a task list and handles the coordination of subagents to complete the task.





