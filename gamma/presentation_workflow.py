import asyncio
import json
import time
import re
import logging
import requests
from dataclasses import dataclass
from typing import Never, Annotated, Awaitable
from pydantic import BaseModel, Field

from config.config import (
    API_KEY as GAMMA_API_KEY,
    API_BASE_URL as GAMMA_API_BASE_URL,
    TAVILY_API_KEY,
    AZURE_OPENAI_ENDPOINT as endpoint,
    AZURE_OPENAI_API_KEY as api_key,
    AZURE_OPENAI_DEPLOYMENT as deployment_name,
)

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    AgentRunEvent,
    ChatMessage,
    Executor,
    Role,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowOutputEvent,
    handler,
    ai_function,
)

from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework import FunctionInvocationContext
from azure.identity import AzureCliCredential
from typing import List
from collections.abc import Callable

from tools.search import search_web

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Custom formatter to show only filename, not full path
class ShortFileFormatter(logging.Formatter):
    def format(self, record):
        record.pathname = record.filename
        return super().format(record)

# Update root logger with custom formatter
root_logger = logging.getLogger()
for log_handler in root_logger.handlers:
    log_handler.setFormatter(ShortFileFormatter('[%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

# logging function middleware - no relation with otel but added for demo purposes
async def logging_function_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """Middleware that logs function calls."""
    logger.info(f'FUNCTION - "{context.function.name}" - Invoked')

    await next(context)

    result_preview = str(context.result)[:100].replace('\n', ' ')
    logger.info(f'FUNCTION - "{context.function.name}" - Result: {result_preview}')

# Pydantic classe for outline agent response

class SlideTitle(BaseModel):
    title: str
    reason: str

class OutlineResponse(BaseModel):
    title: str
    number_of_slides: Annotated[int, Field(default=5, description="Number of slides in the presentation")]
    slide_titles: List[SlideTitle]
    audience: Annotated[str, Field(default="general", description="Single word target audience for the presentation (technical, business, ...)")]

class SlideContent(BaseModel):
    title: str
    content: str

class ResearchResponse(BaseModel):
    title: str
    number_of_slides: int
    slides: List[SlideContent]
    audience: Annotated[str, Field(default="general", description="Single word target audience for the presentation (technical, business, ...)")]


# define outline agent
outline_agent = AzureOpenAIResponsesClient(
        endpoint=endpoint,
        api_key=api_key,
        # api_version=api_version,  --> left out to use default
        deployment_name=deployment_name
    ).create_agent(
        name="OutlineAgent",
        instructions="""
            Based on the user's request, you create an outline for a presentation.
            Generate a title for the presentation and a list of slide titles.
            If the user specified a number of slides, use that number.
            Before you generate the outline, use the 'search_web' tool to research the topic thoroughly with ONE query.
            Base the outline on the research findings.
        """,
        tools=[search_web],  # Register the search_web function as a tool
        response_format=OutlineResponse,
        middleware=[logging_function_middleware]
    )

research_agent = AzureOpenAIResponsesClient(
        endpoint=endpoint,
        api_key=api_key,
        # api_version=api_version,  --> left out to use default
        deployment_name=deployment_name
    ).create_agent(
        name="ResearchAgent",
        instructions="""
            You research and create content for slides. You will receive a presentation
            title and a list of slide titles with the reason the title was chosen.
            Generate one web search query to gather information for each slide title.
            Keep in mind the target audience when generating the queries.
            Next, use the 'search_web' tool ONCE passing in the queries all at once.

            Use the result from the queries to generate content for each slide. 
            Content for slides should be limited to 100 words max with three main bullet points.
            If you require an extra slide (max 3 extra), to explain a complex topic, feel free to add it.
            Ensure you update the number_of_slides field accordingly.
        """,
        tools=[search_web],  # Register the search_web function as a tool
        response_format=ResearchResponse,
        kwargs={"verbosity": "high"},
        middleware=[logging_function_middleware]
    )

#executor for gamma presentation creation
class GammaAPIExecutor(Executor):

    def __init__(self, id: str | None = None):
        super().__init__(id=id or "gamma_api")

    @handler
    async def call_gamma_api(
        self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]
    ) -> None:
        """Call Gamma API to generate presentation from agent response."""
        
        # Extract slide content from agent response
        slide_content = response.agent_run_response.text

        # Convert response to JSON and extract number of slides
        response_json = json.loads(slide_content)
        number_of_slides = response_json.get("number_of_slides", 5)
        audience = response_json.get("audience", "general")
        title = response_json.get("title", "Untitled Presentation")
        logger.info(f'GAMMA - "{title}" - Slides: {number_of_slides}, Audience: {audience}')

        # Save entire response to a file for debugging
        with open(f"{title.replace(' ', '_')}_response.json", "w") as f:
            json.dump(response_json, f, indent=2)
        
        if not GAMMA_API_KEY:
            error_msg = "Error: GAMMA_API_KEY not found in environment"
            await ctx.yield_output(error_msg)
            return
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": GAMMA_API_KEY,
        }

        payload = {
            "inputText": slide_content,
            "textMode": "condense", # Changed from "generate" to "condense"
            "format": "presentation",
            "themeName": "Gamma",
            "numCards": number_of_slides + 1,  # 1 title slide + content slides
            "cardSplit": "auto",
            "exportAs": "pdf",
            "textOptions": {
                "amount": "brief",  # Changed from "medium" to "detailed"
                "tone": "professional, engaging, informative",
                "language": "en",
                "audience": audience,
            },
            "imageOptions": {
                "source": "aiGenerated",
                "style": "photorealistic",
            },
            "cardOptions": {
                "dimensions": "16x9",
            },
        }

        try:
            api_response = requests.post(
                f"{GAMMA_API_BASE_URL}/generations",
                headers=headers,
                json=payload,
                timeout=30,
            )
            
            if api_response.status_code not in [200, 201]:
                error_msg = f"Gamma API Error: {api_response.status_code} - {api_response.text}"
                logger.error(f'GAMMA - "{title}" - POST /generations {api_response.status_code}')
                await ctx.yield_output(error_msg)
                return

            data = api_response.json()
            generation_id = data.get("id") or data.get("generationId")
            
            if not generation_id:
                error_msg = f"No generation ID in response: {json.dumps(data, indent=2)}"
                logger.error(f'GAMMA - "{title}" - No generation ID in response')
                await ctx.yield_output(error_msg)
                return

            logger.info(f'GAMMA - "{title}" - POST /generations {api_response.status_code} - Generation ID: {generation_id}')
            
            # Poll for completion
            completed_data = await self._poll_for_completion(generation_id)
            
            pdf_url = completed_data.get("exportUrl")
            if pdf_url:
                # Download the PDF
                pdf_path = self._download_pdf(pdf_url, output_path=f"{title.replace(' ', '_')}.pdf")
                
                result_msg = f"✓ Presentation created successfully!\nGeneration ID: {generation_id}\nPDF URL: {pdf_url}\nPDF saved to: {pdf_path}"
                logger.info(f'GAMMA - "{title}" - Presentation completed - PDF saved to: {pdf_path}')
                
                await ctx.yield_output(result_msg)
            else:
                error_msg = f"No PDF URL in response: {json.dumps(completed_data, indent=2)}"
                logger.error(f'GAMMA - "{title}" - No PDF URL in response')
                
                await ctx.yield_output(error_msg)
                
        except Exception as e:
            error_msg = f"Exception calling Gamma API: {str(e)}"
            logger.error(f'GAMMA - "{title}" - Exception: {str(e)}')
            
            await ctx.yield_output(error_msg)

    async def _poll_for_completion(self, generation_id: str, max_wait: int = 300) -> dict:
        """Poll the API to check if the presentation is ready."""
        headers = {
            "X-API-KEY": GAMMA_API_KEY,
            "accept": "application/json",
        }

        logger.info(f'GAMMA - GET /generations/{generation_id} - Polling started (max wait: {max_wait}s)')
        start_time = time.time()

        while time.time() - start_time < max_wait:
            response = requests.get(
                f"{GAMMA_API_BASE_URL}/generations/{generation_id}",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                if status == "completed":
                    logger.info(f'GAMMA - GET /generations/{generation_id} - Status: completed')
                    return data

                elapsed = int(time.time() - start_time)
                logger.info(f'GAMMA - GET /generations/{generation_id} - Status: {status} ({elapsed}s)')
                
            await asyncio.sleep(5)

        raise TimeoutError(f"Presentation generation timed out after {max_wait} seconds")

    def _download_pdf(self, pdf_url: str, output_path: str = "presentation.pdf") -> str:
        """
        Download the PDF from the provided URL.

        Args:
            pdf_url: URL of the PDF file
            output_path: Path where to save the PDF

        Returns:
            Path to the saved PDF file
        """
        logger.info(f'GAMMA - Downloading PDF to: {output_path}')

        response = requests.get(pdf_url, timeout=30)

        if response.status_code != 200:
            raise RuntimeError(f"Failed to download PDF (status {response.status_code})")

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f'GAMMA - PDF saved successfully to: {output_path}')
        return output_path





if __name__ == "__main__":
    workflow = (
        WorkflowBuilder()
        .set_start_executor(outline_agent)
        .add_edge(outline_agent, research_agent)
        .add_edge(research_agent, GammaAPIExecutor())
        .build()
    )

    from agent_framework.devui import serve
    serve(entities=[workflow], port=8093, auto_open=True)