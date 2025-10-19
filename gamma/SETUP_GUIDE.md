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

## Step 5: Set Up Environment Variables

Create a `.env` file in the project root (or gamma folder) with your API keys and endpoints:

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
   - Ensure you have a deployment (e.g., `gpt-5-mini`)

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

1. **Enter a presentation topic** via the **Configure & Run** button
   - Example: "Create a presentation about Python async programming"
   - Example: "Machine Learning fundamentals for business leaders"

2. **Watch the workflow execute** in real-time:
   - ✓ Outline Agent researches and creates outline
   - ✓ Research Agent generates slide content
   - ✓ Gamma Executor creates presentation PDF

3. **Check the PDF** when complete or check the presentation in Gamma

## Step 9: Monitor Logs

Logs should appear in your terminal:

```
[2025-10-19 13:09:22 - search.py:45 - INFO] SEARCH - "Python async" - Searching
[2025-10-19 13:09:23 - presentation_workflow.py:150 - INFO] GAMMA - "Python Async Mastery" - POST /generations 201
```

