"""Gamma API configuration."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gamma API configuration
API_KEY = os.getenv("GAMMA_API_KEY")
API_BASE_URL = "https://public-api.gamma.app/v0.2"

if not API_KEY:
    print("Error: GAMMA_API_KEY not found in .env file")
    sys.exit(1)

# Tavily API configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_DEPLOYMENT:
    raise ValueError("Azure OpenAI configuration is missing in environment variables.")
