# Running the Presentation Workflow

This guide walks you through setting up and running the AI-powered presentation generation workflow.

## Prerequisites

Before starting, ensure you have:
- Python 3.10 or later
- Azure subscription with OpenAI service deployed
- Tavily API key (for web search)
- GAMMA API key and endpoint (for presentation generation)
- Git (for cloning the repository, if needed)

## Step 1: Clone or Navigate to the Project

```bash
cd /path/to/maf
```

## Step 2: Create a Python Virtual Environment

Create an isolated Python environment to avoid conflicts with system packages:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt, indicating the environment is active.

## Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

## Step 4: Install Required Packages

```bash
pip install -r gamma/requirements.txt
```

This installs all dependencies including:
- Microsoft Agent Framework
- Azure SDKs
- FastAPI and Uvicorn
- Pydantic for data validation
- Tavily Python client
- And more...

**Installation time**: 3-5 minutes depending on your internet connection

## Step 5: Set Up Environment Variables

Create a `.env` file in the project root with your API keys and endpoints:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o  # or your deployment name

# Tavily Search API
TAVILY_API_KEY=<your-tavily-api-key>

# GAMMA API Configuration
GAMMA_API_KEY=<your-gamma-api-key>
GAMMA_API_BASE_URL=https://api.gamma.app  # or your GAMMA endpoint

# Optional: Logging level
LOG_LEVEL=INFO
```

**Where to get these keys:**

1. **Azure OpenAI**:
   - Go to Azure Portal → Your OpenAI Resource → Keys and Endpoint
   - Copy the endpoint URL and API key
   - Ensure you have a deployment (e.g., `gpt-4o-mini`)

2. **Tavily API**:
   - Visit [https://tavily.com](https://tavily.com)
   - Sign up and get your API key from the dashboard

3. **GAMMA API**:
   - Visit [https://gamma.app](https://gamma.app)
   - Get your API key from account settings
   - Your endpoint is typically `https://api.gamma.app`

## Step 6: Verify Installation

Test that everything is installed correctly:

```bash
# Activate the environment (if not already)
source .venv/bin/activate

# Test imports
python -c "import agent_framework; print('✓ Agent Framework installed')"
python -c "import azure.identity; print('✓ Azure SDK installed')"
python -c "import tavily; print('✓ Tavily installed')"
python -c "import pydantic; print('✓ Pydantic installed')"
```

## Step 7: Run the Workflow

Navigate to the gamma directory and start the workflow:

```bash
# Navigate to gamma directory
cd gamma

# Activate environment (if not already active)
source ../.venv/bin/activate

# Run the workflow with the development UI
python presentation_workflow.py
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8093 (Press CTRL+C to quit)
```

The workflow will:
1. Start a local server on `http://127.0.0.1:8093`
2. Automatically open the browser with the development UI
3. Be ready to accept requests

## Step 8: Use the Workflow

In the browser UI:

1. **Enter a presentation topic** in the input field
   - Example: "Create a presentation about Python async programming"
   - Example: "Machine Learning fundamentals for business leaders"

2. **Click "Submit"** to start the workflow

3. **Watch the workflow execute** in real-time:
   - ✓ Outline Agent researches and creates outline
   - ✓ Research Agent generates slide content
   - ✓ Gamma Executor creates presentation PDF

4. **Download the PDF** when complete

## Step 9: Monitor Logs

Open another terminal to monitor logs while the workflow runs:

```bash
# In a second terminal
source .venv/bin/activate
cd gamma
tail -f /path/to/logfile.log
```

Or check console output in the running terminal for structured logs like:
```
[2025-10-19 13:09:22 - search.py:45 - INFO] SEARCH - "Python async" - Searching
[2025-10-19 13:09:23 - presentation_workflow.py:150 - INFO] GAMMA - "Python Async Mastery" - POST /generations 201
```

## Step 10: Stop the Workflow

Press `CTRL+C` in the terminal running the workflow to stop it:

```
^C
INFO:     Shutdown complete.
```

## Troubleshooting

### Virtual Environment Issues

**Problem**: `python3: command not found` or `python` doesn't work
```bash
# Use python3 explicitly
python3 -m venv .venv
source .venv/bin/activate
```

**Problem**: Activation doesn't work
```bash
# Try with bash explicitly
bash .venv/bin/activate
```

### Installation Issues

**Problem**: `ModuleNotFoundError: No module named 'agent_framework'`
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall requirements
pip install --upgrade pip
pip install -r gamma/requirements.txt
```

**Problem**: `pip: command not found`
```bash
# Use python -m pip instead
python -m pip install -r gamma/requirements.txt
```

### Azure Authentication Issues

**Problem**: `AuthenticationError` or authentication fails
```bash
# Option 1: Use Azure CLI authentication (recommended)
az login

# Option 2: Provide API key in .env
AZURE_OPENAI_API_KEY=<your-key>
```

### API Key Issues

**Problem**: `ValueError: API key not found`
- Verify `.env` file exists in the project root
- Check that all keys are set correctly (no typos, extra spaces)
- Use `echo $AZURE_OPENAI_API_KEY` to verify environment variables are loaded
- Restart the terminal after updating `.env`

**Problem**: `401 Unauthorized` errors
- Verify API keys are correct
- Check that API keys haven't expired
- Ensure Tavily/GAMMA API keys are still valid

### Network Issues

**Problem**: Connection timeouts
- Check your internet connection
- Verify firewall allows outbound HTTPS connections
- Try with a VPN if behind corporate proxy

## Running Tests (Optional)

To test individual components:

```bash
# Test search functionality
python -c "
import asyncio
from tools.search import search_web

async def test():
    result = await search_web(['python async programming'])
    print(result)

asyncio.run(test())
"

# Test agent creation
python -c "
from presentation_workflow import outline_agent
print('✓ Outline agent created successfully')
"
```

## Advanced: Running Without Browser UI

If you prefer not to use the browser UI, you can run the workflow programmatically:

```python
import asyncio
from presentation_workflow import workflow

async def main():
    result = await workflow.run("Create a presentation about Python async")
    print(result)

asyncio.run(main())
```

## Advanced: Using Different Orchestration

To test different workflow orchestration modes, modify the `WorkflowBuilder`:

```python
# Sequential (default) - each step depends on previous
workflow = (
    WorkflowBuilder()
    .set_start_executor(outline_agent)
    .add_edge(outline_agent, research_agent)
    .add_edge(research_agent, GammaAPIExecutor())
    .build()
)

# For other patterns, see the blog post for concurrent/handoff examples
```

## Next Steps

1. **Customize agents**: Modify instructions in `presentation_workflow.py`
2. **Add more tools**: Create additional `@ai_function` decorated functions in `tools/search.py`
3. **Integrate with services**: Add custom executors for your APIs
4. **Deploy to production**: Use Docker and container orchestration

## Getting Help

- Check logs for detailed error messages
- Review the blog post for architecture explanations
- Consult [Microsoft Agent Framework docs](https://learn.microsoft.com/en-us/agent-framework/)
- Check [Azure OpenAI docs](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

## Summary

You should now have:
- ✓ Python virtual environment set up
- ✓ All dependencies installed
- ✓ Environment variables configured
- ✓ Workflow running and accessible at `http://127.0.0.1:8093`
- ✓ Ability to generate presentations with a single request

Happy presentation building! 🎉
