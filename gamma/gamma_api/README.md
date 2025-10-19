"""Gamma API Module

A configurable client for interacting with the Gamma API for presentation generation.

## Overview

The `gamma_api` module provides `GammaAPIClient` - a client for making requests to the Gamma API with full configuration options as constructor parameters.

## Usage

### Basic Usage

```python
from gamma_api import GammaAPIClient

# Create a client with minimal configuration
client = GammaAPIClient(
    api_key="your-api-key",
    api_base_url="https://api.gamma.app"
)

# Generate a presentation
result = await client.create_presentation(
    input_text="Your presentation content here",
    number_of_slides=10,
    audience="technical",
    title="My Presentation"
)

print(f"PDF URL: {result['pdf_url']}")
print(f"PDF saved to: {result['pdf_path']}")
```

### Fully Customized Configuration

```python
from gamma_api import GammaAPIClient

# Create a client with all parameters customized
client = GammaAPIClient(
    api_key="your-api-key",
    api_base_url="https://api.gamma.app",
    
    # Text generation settings
    text_mode="generate",
    text_amount="detailed",
    text_tone="academic, formal",
    text_language="en",
    text_audience="business",
    
    # Theme and format
    theme_name="Modern",
    format="presentation",
    
    # Image options
    image_source="aiGenerated",
    image_style="realistic",
    
    # Slide/card options
    card_dimensions="16x9",
    num_cards_offset=1,
    card_split="auto",
    
    # Export
    export_as="pdf",
    
    # Polling and timeout
    poll_interval=3,
    max_wait=600,
    request_timeout=60
)

result = await client.create_presentation(
    input_text="...",
    number_of_slides=10,
    title="My Presentation"
)
```

### Using with Executor

```python
from gamma_api import GammaAPIClient
from agent_framework import Executor, handler

class GammaAPIExecutor(Executor):
    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        text_mode: str = "condense",
        text_amount: str = "brief"
    ):
        super().__init__(id="gamma_api")
        
        self.client = GammaAPIClient(
            api_key=api_key,
            api_base_url=api_base_url,
            text_mode=text_mode,
            text_amount=text_amount
        )
    
    @handler
    async def call_gamma_api(self, response, ctx):
        result = await self.client.create_presentation(...)
        # Process result...
```

## Configuration Parameters

### API Configuration
- **api_key** (str): Your Gamma API key (required)
- **api_base_url** (str): Base URL for the Gamma API (required)

### Text Generation
- **text_mode** (str): "generate" or "condense" (default: "condense")
- **text_amount** (str): "brief", "medium", or "detailed" (default: "brief")
- **text_tone** (str): Tone for text generation (default: "professional, engaging, informative")
- **text_language** (str): Language code (default: "en")
- **text_audience** (str): Target audience (default: "general")

### Presentation Format
- **format** (str): Presentation format (default: "presentation")
- **theme_name** (str): Presentation theme (default: "Gamma")
- **export_as** (str): Export format (default: "pdf")

### Image Generation
- **image_source** (str): "aiGenerated", "stock", or "custom" (default: "aiGenerated")
- **image_style** (str): Image style (default: "photorealistic")

### Slide/Card Options
- **card_dimensions** (str): "16x9" or "4x3" (default: "16x9")
- **num_cards_offset** (int): Additional cards beyond number_of_slides (default: 1 for title slide)
- **card_split** (str): How to split content across cards (default: "auto")

### Request Configuration
- **poll_interval** (int): Seconds between status polls (default: 5)
- **max_wait** (int): Maximum seconds to wait for completion (default: 300)
- **request_timeout** (int): Request timeout in seconds (default: 30)
- **extra_params** (dict): Additional parameters to pass to API (default: {})

## Return Values

The `create_presentation()` method returns a dictionary with:

```python
{
    "generation_id": str,          # ID of the generation
    "pdf_url": str,                # URL to download the PDF
    "pdf_path": str,               # Local path where PDF was saved
    "completed_data": dict         # Full response data from API
}
```

## Error Handling

The client raises:
- **ValueError**: If API credentials are missing or API request fails
- **TimeoutError**: If presentation generation doesn't complete within max_wait
- **RuntimeError**: If PDF download fails

